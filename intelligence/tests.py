from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from rest_framework.test import APIClient
from .models import *
from .providers import run_discovery, ingest, FixtureProvider, CandidateRecordSerializer
from .services import (
    review,
    assign,
    transition,
    publish,
    can_use_media,
    reconcile_delivery,
)
from .ranking import score_candidate
from .telegram import deliver


class WorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            "admin", password="test-long-passphrase", is_staff=True, is_superuser=True
        )
        self.u = User.objects.create_user("publisher", password="test-long-passphrase")
        self.other = User.objects.create_user("other", password="test-long-passphrase")
        self.p = PublisherProfile.objects.create(
            user=self.u, display_name="Publisher", telegram_chat_id="100"
        )
        self.p2 = PublisherProfile.objects.create(
            user=self.other, display_name="Other", telegram_chat_id="200"
        )
        self.provider = DiscoveryProvider.objects.create(name="Fixture", kind="fixture")
        run = run_discovery(self.provider)
        self.assertEqual(run.status, "success")
        self.c = VideoCandidate.objects.get()
        self.api = APIClient()

    def approved_assignment(self):
        review(self.c, self.admin, "approved")
        return assign(self.c, self.p, self.admin)[0]

    def test_end_to_end(self):
        self.assertIsNotNone(self.c.score)
        self.assertEqual(self.c.provenance.count(), 1)
        a = self.approved_assignment()
        transition(a, self.u, "accepted")
        p = publish(
            a, self.u, "https://www.tiktok.com/@publisher/video/123", timezone.now()
        )
        self.api.force_authenticate(self.u)
        r = self.api.post(
            "/api/metrics/",
            {
                "post": p.pk,
                "observed_at": timezone.now().isoformat(),
                "views": 12000,
                "verified": True,
            },
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertFalse(PerformanceSnapshot.objects.get().verified)
        self.api.force_authenticate(self.admin)
        self.assertEqual(
            self.api.post(f"/api/metrics/{r.data['id']}/verify/").status_code, 200
        )
        self.assertTrue(PerformanceSnapshot.objects.get().verified)
        self.assertGreaterEqual(AuditLog.objects.count(), 5)

    def test_canonical_deduplication_and_observation_idempotence(self):
        records = FixtureProvider().discover()
        run = DiscoveryRun.objects.create(provider=self.provider)
        ingest(self.provider, run, records)
        ingest(self.provider, run, records)
        self.assertEqual(VideoCandidate.objects.count(), 1)
        self.assertEqual(CandidateDiscovery.objects.filter(run=run).count(), 1)
        self.assertEqual(EngagementSnapshot.objects.count(), 6)

    def test_missing_metrics_are_not_zero(self):
        c = VideoCandidate.objects.create(
            canonical_id="missing",
            url="https://example.com/a",
            title="Missing",
            signals={"relevance": 1},
        )
        score_candidate(c)
        self.assertIsNone(c.score)
        self.assertNotIn("velocity", c.score_components)
        self.assertEqual(c.confidence, "Insufficient Data")

    def test_velocity_requires_two_observations(self):
        c = VideoCandidate.objects.create(
            canonical_id="single",
            url="https://example.com/b",
            title="Single",
            signals={"relevance": 1},
        )
        EngagementSnapshot.objects.create(
            candidate=c,
            provider=self.provider,
            observed_at=timezone.now(),
            views=100000,
        )
        score_candidate(c)
        self.assertNotIn("velocity", c.score_components)

    def test_declining_counters_not_negative_velocity(self):
        c = VideoCandidate.objects.create(
            canonical_id="decline", url="https://example.com/c", title="Decline"
        )
        for h, v in [(1, 100), (0, 50)]:
            EngagementSnapshot.objects.create(
                candidate=c,
                provider=self.provider,
                observed_at=timezone.now() - timedelta(hours=h),
                views=v,
            )
        score_candidate(c)
        self.assertNotIn("velocity", c.score_components)

    def test_stale_evidence_lowers_confidence(self):
        for s in self.c.snapshots.all():
            s.observed_at -= timedelta(days=3)
            s.save()
        score_candidate(self.c)
        self.assertEqual(self.c.confidence, "Low")

    def test_no_unapproved_assignment(self):
        with self.assertRaises(ValidationError):
            assign(self.c, self.p, self.admin)

    def test_assignment_duplicate_and_daily_limit(self):
        a = self.approved_assignment()
        self.assertEqual(assign(self.c, self.p, self.admin), (a, False))
        self.p.daily_limit = 1
        self.p.save()
        c = VideoCandidate.objects.create(
            canonical_id="another",
            title="Another",
            url="https://example.com/another",
            review_status="approved",
        )
        with self.assertRaises(ValidationError):
            assign(c, self.p, self.admin)

    def test_publish_requires_acceptance(self):
        a = self.approved_assignment()
        with self.assertRaises(ValidationError):
            publish(a, self.u, "https://example.com/post", timezone.now())

    def test_publisher_cannot_review_or_assign(self):
        self.api.force_authenticate(self.u)
        self.assertEqual(
            self.api.post(
                f"/api/candidates/{self.c.pk}/review/", {"decision": "approved"}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.api.post(
                f"/api/candidates/{self.c.pk}/assign/", {"publishers": [self.p.pk]}
            ).status_code,
            403,
        )

    def test_publisher_scope(self):
        a = self.approved_assignment()
        self.api.force_authenticate(self.other)
        self.assertEqual(self.api.get(f"/api/assignments/{a.pk}/").status_code, 404)
        self.assertEqual(self.api.get(f"/api/candidates/{self.c.pk}/").status_code, 404)
        with self.assertRaises(PermissionDenied):
            transition(a, self.other, "accepted")

    def test_revocation_of_other_publisher_does_not_hide_candidate(self):
        self.approved_assignment()
        a = assign(self.c, self.p2, self.admin)[0]
        transition(a, self.admin, "revoked")
        self.api.force_authenticate(self.u)
        self.assertEqual(self.api.get(f"/api/candidates/{self.c.pk}/").status_code, 200)
        self.api.force_authenticate(self.other)
        self.assertEqual(self.api.get(f"/api/candidates/{self.c.pk}/").status_code, 404)

    def test_rights_and_expiry(self):
        review(self.c, self.admin, "approved")
        self.c.refresh_from_db()
        self.assertFalse(can_use_media(self.c))
        self.c.rights = "permission"
        self.c.rights_evidence = "Written permission"
        self.c.save()
        self.assertTrue(can_use_media(self.c))
        self.c.rights_expires_at = timezone.now() - timedelta(seconds=1)
        self.assertFalse(can_use_media(self.c))

    def test_safety_flags_require_review_note(self):
        self.c.safety_flags = ["Sensitive topic"]
        self.c.save()
        with self.assertRaises(ValidationError):
            review(self.c, self.admin, "approved")
        self.assertEqual(
            review(
                self.c, self.admin, "approved", notes="Reviewed context."
            ).review_status,
            "approved",
        )

    def test_refresh_new_safety_flag_requires_review_again(self):
        self.approved_assignment()
        records = FixtureProvider().discover()
        records[0]["safety_flags"] = ["Sensitive"]
        run = DiscoveryRun.objects.create(provider=self.provider)
        ingest(self.provider, run, records)
        self.c.refresh_from_db()
        self.assertEqual(self.c.review_status, "pending")

    def test_invalid_import_is_atomic(self):
        run = DiscoveryRun.objects.create(provider=self.provider)
        records = FixtureProvider().discover()
        records.append({"canonical_id": "invalid"})
        from rest_framework.exceptions import ValidationError as DRFError

        with self.assertRaises(DRFError):
            ingest(self.provider, run, records)
        self.assertEqual(CandidateDiscovery.objects.filter(run=run).count(), 0)

    def test_feed_missing_configuration_reports_failure(self):
        p = DiscoveryProvider.objects.create(name="Unconfigured", kind="feed")
        with override_settings(DISCOVERY_FEED_URL=""):
            run = run_discovery(p)
        self.assertEqual(run.status, "failed")
        self.assertIn("ValueError", run.error)

    def test_urls_and_metrics_validate(self):
        data = FixtureProvider().discover()[0]
        data["url"] = "http://example.com"
        s = CandidateRecordSerializer(data=data)
        self.assertFalse(s.is_valid())
        data["url"] = "https://example.com"
        data["observations"][0]["views"] = -1
        self.assertFalse(CandidateRecordSerializer(data=data).is_valid())

    @override_settings(TELEGRAM_BOT_TOKEN="test-token")
    @patch("intelligence.telegram.bot_request")
    def test_telegram_success_is_not_resent(self, mock):
        a = self.approved_assignment()
        mock.return_value = {"ok": True, "result": {"message_id": 12}}
        self.assertEqual(deliver(a.delivery.pk), "sent")
        self.assertEqual(deliver(a.delivery.pk), "sent")
        mock.assert_called_once()
        a.refresh_from_db()
        self.assertEqual(a.status, "sent")

    @override_settings(TELEGRAM_BOT_TOKEN="test-token")
    @patch("intelligence.telegram.bot_request")
    def test_telegram_rate_limit_backoff(self, mock):
        a = self.approved_assignment()
        mock.return_value = {
            "ok": False,
            "error_code": 429,
            "parameters": {"retry_after": 90},
        }
        self.assertEqual(deliver(a.delivery.pk), "retry")
        self.assertEqual(deliver(a.delivery.pk), "retry")
        mock.assert_called_once()
        a.delivery.refresh_from_db()
        self.assertGreater(a.delivery.next_attempt_at, timezone.now())

    @override_settings(TELEGRAM_BOT_TOKEN="test-token")
    @patch("intelligence.telegram.bot_request", side_effect=TimeoutError)
    def test_ambiguous_delivery_requires_reconciliation(self, mock):
        a = self.approved_assignment()
        self.assertEqual(deliver(a.delivery.pk), "unknown")
        self.assertEqual(deliver(a.delivery.pk), "unknown")
        mock.assert_called_once()
        reconcile_delivery(
            a.delivery, self.admin, "retry", "Checked chat: no message present."
        )
        a.delivery.refresh_from_db()
        self.assertEqual(a.delivery.status, "pending")

    def test_revoked_assignment_not_sent(self):
        a = self.approved_assignment()
        transition(a, self.admin, "revoked")
        self.assertEqual(deliver(a.delivery.pk), "pending")

    @override_settings(TELEGRAM_WEBHOOK_SECRET="webhook-secret")
    def test_webhook_chat_binding_and_rotation(self):
        token = str(self.p2.link_token)
        payload = {
            "message": {
                "chat": {"id": 300, "type": "private"},
                "text": f"/start {token}",
            }
        }
        self.assertEqual(
            self.client.post(
                "/telegram/webhook/", data=payload, content_type="application/json"
            ).status_code,
            403,
        )
        r = self.client.post(
            "/telegram/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="webhook-secret",
        )
        self.assertEqual(r.status_code, 200)
        self.p2.refresh_from_db()
        self.assertEqual(self.p2.telegram_chat_id, "200")
        self.p2.telegram_chat_id = None
        self.p2.save()
        self.client.post(
            "/telegram/webhook/",
            data=payload,
            content_type="application/json",
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="webhook-secret",
        )
        self.p2.refresh_from_db()
        self.assertEqual(self.p2.telegram_chat_id, "300")
        self.assertNotEqual(str(self.p2.link_token), token)

    def test_views_render_and_login_is_required(self):
        self.assertEqual(self.client.get("/").status_code, 302)
        self.client.force_login(self.admin)
        a = self.approved_assignment()
        for url in [
            "/",
            "/candidates/",
            f"/candidates/{self.c.pk}/",
            "/trends/",
            "/assignments/",
            f"/assignments/{a.pk}/",
            "/reports/",
            "/integrations/",
        ]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_analyst_read_only(self):
        g = Group.objects.create(name="Analyst")
        self.other.groups.add(g)
        self.api.force_authenticate(self.other)
        self.assertEqual(self.api.get(f"/api/candidates/{self.c.pk}/").status_code, 200)
        self.assertEqual(
            self.api.post(
                f"/api/candidates/{self.c.pk}/review/", {"decision": "approved"}
            ).status_code,
            403,
        )

    def test_metric_for_other_publishers_post_forbidden(self):
        a = self.approved_assignment()
        transition(a, self.u, "accepted")
        p = publish(a, self.u, "https://example.com/mypost", timezone.now())
        self.api.force_authenticate(self.other)
        r = self.api.post(
            "/api/metrics/",
            {"post": p.pk, "observed_at": timezone.now().isoformat(), "views": 10},
        )
        self.assertEqual(r.status_code, 403)

    def test_notifications_and_reminders_are_idempotent(self):
        from .tasks import publisher_reminders

        a = self.approved_assignment()
        self.assertEqual(Notification.objects.filter(user=self.u).count(), 1)
        transition(a, self.u, "accepted")
        DistributionAssignment.objects.filter(pk=a.pk).update(
            updated_at=timezone.now() - timedelta(days=2)
        )
        self.assertEqual(publisher_reminders(), 1)
        self.assertEqual(publisher_reminders(), 0)
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.post(
                f"/notifications/{Notification.objects.first().pk}/read/"
            ).status_code,
            404,
        )

    def test_trend_signals_and_clusters_are_recorded(self):
        self.assertTrue(
            TrendSignal.objects.filter(kind="hashtag", value="ethiopia").exists()
        )
        self.assertEqual(TrendCluster.objects.get().lifecycle, "emerging")

    def test_learning_rejects_insufficient_outcomes(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            call_command("propose_model", model_version="not-enough")

    def test_model_validates_weights_and_benchmarks(self):
        from .ranking import DEFAULT_WEIGHTS

        model = RankingModelVersion(
            version="bad", weights=DEFAULT_WEIGHTS, benchmarks={"views_per_hour": 0}
        )
        with self.assertRaises(ValidationError):
            model.full_clean()

    def test_csv_export_is_staff_only(self):
        self.client.force_login(self.u)
        self.assertEqual(self.client.get("/reports/export/").status_code, 302)
        self.client.force_login(self.admin)
        r = self.client.get("/reports/export/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"assignment,publisher", r.content)

    def test_private_media_is_denied_without_rights(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        import tempfile

        with (
            tempfile.TemporaryDirectory() as directory,
            override_settings(MEDIA_ROOT=directory),
        ):
            a = self.approved_assignment()
            asset = MediaAsset.objects.create(
                candidate=self.c,
                file=SimpleUploadedFile("original.txt", b"owned test content"),
            )
            self.client.force_login(self.u)
            self.assertEqual(self.client.get(f"/media/{asset.pk}/").status_code, 403)
            self.c.refresh_from_db()
            self.c.rights = "owned"
            self.c.rights_evidence = "Original test file"
            self.c.save()
            response = self.client.get(f"/media/{asset.pk}/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                b"".join(response.streaming_content), b"owned test content"
            )
            transition(a, self.admin, "revoked")
            self.assertEqual(self.client.get(f"/media/{asset.pk}/").status_code, 403)

    def test_learning_saves_inactive_proposal_from_verified_evidence(self):
        from django.core.management import call_command
        from io import StringIO

        now = timezone.now()
        for index in range(30):
            candidate = VideoCandidate.objects.create(
                platform="fixture",
                canonical_id=f"learning-{index}",
                title="Learning fixture",
                url=f"https://example.com/learning/{index}",
            )
            ViralScore.objects.create(
                candidate=candidate,
                value=50,
                completeness=1,
                version="baseline-v1",
                components={"velocity": index / 29},
            )
            assignment = DistributionAssignment.objects.create(
                candidate=candidate,
                publisher=self.p,
                assigned_by=self.admin,
                status="published",
            )
            post = PublishedPost.objects.create(
                assignment=assignment,
                url=f"https://example.com/outcome/{index}",
                published_at=now - timedelta(hours=24),
            )
            PerformanceSnapshot.objects.create(
                post=post,
                observed_at=now,
                views=(index + 1) * 100,
                verified=True,
                entered_by=self.admin,
            )
        call_command(
            "propose_model", model_version="reviewed-fixture", stdout=StringIO()
        )
        model = RankingModelVersion.objects.get(version="reviewed-fixture")
        self.assertFalse(model.active)
        self.assertEqual(model.evidence["verified_posts"], 30)
        self.assertAlmostEqual(sum(model.weights.values()), 100, places=2)


from django.test import SimpleTestCase


class AnalystReportTests(TestCase):
    def test_analyst_can_read_reports_but_not_verify(self):
        user = User.objects.create_user("analyst")
        group = Group.objects.create(name="Analyst")
        user.groups.add(group)
        self.client.force_login(user)
        self.assertEqual(self.client.get("/reports/").status_code, 200)
        self.assertEqual(self.client.get("/reports/export/").status_code, 200)
        self.assertEqual(
            self.client.post("/reports/metrics/1/verify/").status_code, 302
        )


class BrowserDiscoveryTests(SimpleTestCase):
    def test_hydration_extracts_ethiopian_candidates_and_nullable_counters(self):
        from .browser_provider import parse_public_records

        now = timezone.now()
        blob = {
            "ItemModule": {
                "123": {
                    "id": "123",
                    "desc": "Ethiopian coffee #ethiopia",
                    "author": {"uniqueId": "newcreator"},
                    "createTime": int((now - timedelta(hours=1)).timestamp()),
                    "stats": {"playCount": 1200, "diggCount": 80},
                }
            }
        }
        records = parse_public_records([blob], [], now)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["canonical_id"], "123")
        self.assertIsNone(records[0]["observations"][0]["shares"])
        self.assertEqual(records[0]["observations"][0]["views"], 1200)
        self.assertNotIn("propagation", records[0]["signals"])

    def test_generic_unrelated_video_is_not_labeled_ethiopian(self):
        from .browser_provider import parse_public_records

        records = parse_public_records(
            [
                {
                    "id": "123",
                    "desc": "Generic unrelated trend",
                    "author": {"uniqueId": "creator"},
                }
            ],
            [],
            timezone.now(),
        )
        self.assertEqual(records, [])

    def test_public_dom_fallback_preserves_missing_metrics(self):
        from .browser_provider import parse_public_records

        records = parse_public_records(
            [],
            [
                {
                    "url": "https://www.tiktok.com/@creator/video/123",
                    "text": "ኢትዮጵያ cultural story",
                }
            ],
            timezone.now(),
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["observations"], [])

    def test_counter_normalization(self):
        from .browser_provider import counter

        self.assertEqual(counter("1.2K"), 1200)
        self.assertEqual(counter("1,200"), 1200)
        self.assertIsNone(counter("Unavailable"))

    def test_real_chromium_can_extract_rendered_public_page_structure(self):
        from playwright.sync_api import sync_playwright
        import shutil, json
        from .browser_provider import parse_public_records

        executable = shutil.which("chromium")
        with sync_playwright() as pw:
            options = {"headless": True}
            if executable:
                options["executable_path"] = executable
            browser = pw.chromium.launch(**options)
            page = browser.new_page()
            page.set_content(
                '<html><body><a href="https://www.tiktok.com/@creator/video/999">Ethiopian dance #ethiopia</a></body></html>'
            )
            links = page.locator('a[href*="/video/"]').evaluate_all(
                "(els)=>els.map(e=>({url:e.href,text:e.innerText}))"
            )
            records = parse_public_records([], links, timezone.now())
            self.assertEqual(records[0]["canonical_id"], "999")
            browser.close()


class TelegramConfigurationTests(SimpleTestCase):
    @override_settings(
        TELEGRAM_BOT_TOKEN="test-token", TELEGRAM_WEBHOOK_SECRET="test-webhook-secret"
    )
    @patch("intelligence.management.commands.configure_telegram.bot_request")
    def test_registers_webhook_using_environment_credentials(self, mock):
        from django.core.management import call_command
        from io import StringIO

        mock.return_value = {"ok": True}
        call_command(
            "configure_telegram",
            webhook_url="https://app.example.com/telegram/webhook/",
            stdout=StringIO(),
        )
        mock.assert_called_once_with(
            "setWebhook",
            {
                "url": "https://app.example.com/telegram/webhook/",
                "secret_token": "test-webhook-secret",
                "allowed_updates": ["message", "callback_query"],
            },
        )

    @override_settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_WEBHOOK_SECRET="")
    def test_missing_credentials_fail_without_network_request(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            call_command(
                "configure_telegram",
                webhook_url="https://app.example.com/telegram/webhook/",
            )
