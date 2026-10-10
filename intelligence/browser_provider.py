"""Public rendered-page discovery using normal Playwright browsing.

No account login, stealth, CAPTCHA solving, fingerprint spoofing, or proxy rotation.
Access failures remain failures. Missing metrics remain null.
"""

import json, os, re, shutil
from datetime import datetime, timezone as dt_timezone
from urllib.parse import urlsplit, quote, unquote
from django.conf import settings
from django.utils import timezone
from playwright.sync_api import sync_playwright


class DiscoveryAccessError(RuntimeError):
    pass


# Seed topic/language queries, rather than a manually maintained creator list.
DEFAULT_QUERIES = ["Ethiopia", "ኢትዮጵያ", "አማርኛ", "Afaan Oromo", "Tigrinya"]


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def relevance(text):
    lower = text.casefold()
    terms = (
        "ethiopia",
        "ethiopian",
        "addis ababa",
        "habesha",
        "amharic",
        "afaan oromo",
        "tigrinya",
        "ኢትዮጵያ",
        "አማርኛ",
        "ሀበሻ",
        "ቡና",
    )
    hits = sum(term in lower for term in terms)
    if hits:
        return min(1.0, 0.65 + 0.1 * hits)
    if re.search("[\u1200-\u137f]", text):
        return 0.6
    return None


def counter(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and value >= 0:
        return int(value)
    if isinstance(value, str):
        match = re.fullmatch(r"([\d,.]+)\s*([kKmMbB]?)", value.strip())
        if match:
            return int(
                float(match[1].replace(",", ""))
                * {"": 1, "k": 1000, "m": 1000000, "b": 1000000000}[match[2].lower()]
            )
    return None


def parse_public_records(blobs, links, observed_at):
    records = {}
    for blob in blobs:
        try:
            data = json.loads(blob) if isinstance(blob, str) else blob
        except (ValueError, TypeError):
            continue
        for item in walk(data):
            # TikTok hydration state contains source video IDs, captions, stats, and authors.
            video_id = str(
                item.get("id") or item.get("item_id") or item.get("aweme_id") or ""
            )
            if not video_id.isdigit() or not any(
                k in item for k in ("desc", "description", "title")
            ):
                continue
            title = str(
                item.get("desc") or item.get("description") or item.get("title") or ""
            )[:500]
            author = item.get("author") or item.get("authorInfo") or {}
            creator = (
                author.get("uniqueId")
                or author.get("unique_id")
                or author.get("nickname")
                or ""
                if isinstance(author, dict)
                else str(author)
            )
            creator = str(creator)[:120]
            url = (
                item.get("shareUrl")
                or item.get("share_url")
                or (
                    f"https://www.tiktok.com/@{quote(creator or 'unknown')}/video/{video_id}"
                )
            )
            parsed = urlsplit(url)
            if (
                parsed.hostname not in ("www.tiktok.com", "tiktok.com")
                or parsed.scheme != "https"
            ):
                continue
            rel = relevance(title + " " + creator)
            if rel is None:
                continue
            published = None
            try:
                stamp = int(item.get("createTime") or item.get("create_time") or 0)
                if stamp:
                    published = datetime.fromtimestamp(stamp, tz=dt_timezone.utc)
            except (ValueError, TypeError, OverflowError, OSError):
                pass
            if published and published > observed_at:
                published = None
            stats = item.get("stats") or item.get("statistics") or {}
            if not isinstance(stats, dict):
                stats = {}
            tags = re.findall(r"#([^\s#]+)", title)
            sounds = []
            music = item.get("music") or {}
            if isinstance(music, dict) and music.get("id"):
                sounds = [str(music["id"])]
            observations = [
                {
                    "observed_at": observed_at.isoformat(),
                    "views": counter(stats.get("playCount", stats.get("play_count"))),
                    "likes": counter(stats.get("diggCount", stats.get("digg_count"))),
                    "comments": counter(
                        stats.get("commentCount", stats.get("comment_count"))
                    ),
                    "shares": counter(
                        stats.get("shareCount", stats.get("share_count"))
                    ),
                }
            ]
            records[video_id] = {
                "platform": "tiktok",
                "canonical_id": video_id,
                "url": url,
                "title": title or "Public video opportunity",
                "creator": creator,
                "language": "ethiopic-script"
                if re.search("[\u1200-\u137f]", title)
                else "",
                "published_at": published.isoformat() if published else None,
                "source_timestamp": observed_at.isoformat(),
                "signals": {"relevance": rel, "hashtags": tags[:100], "sounds": sounds},
                "observations": observations,
            }
    for link in links:
        url = link.get("url", "")
        match = re.match(r"https://(?:www\.)?tiktok\.com/@([^/]+)/video/(\d+)", url)
        if not match or match[2] in records:
            continue
        title = link.get("text", "").strip()[:500]
        rel = relevance(title)
        if rel is None:
            continue
        records[match[2]] = {
            "platform": "tiktok",
            "canonical_id": match[2],
            "url": f"https://www.tiktok.com/@{match[1]}/video/{match[2]}",
            "title": title or "Public video opportunity",
            "creator": unquote(match[1])[:120],
            "source_timestamp": observed_at.isoformat(),
            "signals": {
                "relevance": rel,
                "hashtags": re.findall(r"#([^\s#]+)", title)[:100],
            },
            "observations": [],
        }
    return list(records.values())


class PlaywrightTrendProvider:
    def __init__(self, queries=None):
        self.queries = queries or DEFAULT_QUERIES

    def discover(self):
        queries = list(self.queries)
        # Expand topic queries from recent ingested source signals, with a bounded crawl budget.
        from .models import TrendSignal

        dynamic = list(
            TrendSignal.objects.filter(kind__in=["topic", "hashtag"])
            .order_by("-last_seen")
            .values_list("value", flat=True)[:3]
        )
        queries = list(dict.fromkeys(queries + dynamic))[:8]
        urls = [
            "https://ads.tiktok.com/business/creativecenter/inspiration/popular/pc/en"
        ] + [f"https://www.tiktok.com/search?q={quote(q)}" for q in queries]
        options = {"headless": True}
        executable = settings.PLAYWRIGHT_CHROMIUM_PATH or shutil.which("chromium")
        if executable:
            options["executable_path"] = executable
        proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        if proxy_url:
            parsed = urlsplit(proxy_url)
            if parsed.hostname:
                proxy = {
                    "server": f"{parsed.scheme}://{parsed.hostname}"
                    + (f":{parsed.port}" if parsed.port else "")
                }
                if parsed.username:
                    proxy["username"] = unquote(parsed.username)
                if parsed.password:
                    proxy["password"] = unquote(parsed.password)
                options["proxy"] = proxy
        records = {}
        errors = []
        readable = 0
        with sync_playwright() as pw:
            browser = pw.chromium.launch(**options)
            context = browser.new_context(locale="en-US")
            context.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ("image", "media", "font")
                    else route.continue_()
                ),
            )
            try:
                for url in urls:
                    page = context.new_page()
                    try:
                        response = page.goto(
                            url, wait_until="domcontentloaded", timeout=20000
                        )
                        if response is None or response.status >= 400:
                            errors.append(
                                f"HTTP {response.status if response else 'no response'}"
                            )
                            continue
                        try:
                            page.wait_for_load_state("networkidle", timeout=5000)
                        except Exception:
                            pass
                        text = page.locator("body").inner_text(timeout=5000)
                        if any(
                            marker in text.casefold()
                            for marker in (
                                "verify to continue",
                                "complete the captcha",
                                "access denied",
                                "unusual traffic",
                            )
                        ):
                            errors.append("Public access challenge")
                            continue
                        blobs = page.locator(
                            'script[type="application/json"],script#__NEXT_DATA__,script#SIGI_STATE,script#__UNIVERSAL_DATA_FOR_REHYDRATION__'
                        ).all_text_contents()
                        links = page.locator('a[href*="/video/"]').evaluate_all(
                            '(els)=>els.map(e=>({url:e.href,text:e.innerText || e.getAttribute("aria-label") || e.parentElement.innerText}))'
                        )
                        found = parse_public_records(blobs, links, timezone.now())
                        for record in found:
                            records[record["canonical_id"]] = record
                        # Public trending hashtags may expand subsequent runs without creator whitelists.
                        hashtags = re.findall(r"#([^\s#]{2,80})", text)[:30]
                        for tag in hashtags:
                            if relevance(tag):
                                TrendSignal.objects.get_or_create(
                                    kind="hashtag", value=tag.casefold()[:120]
                                )
                        if blobs or links:
                            readable += 1
                        else:
                            errors.append(
                                "Public page exposed no usable video metadata"
                            )
                    except Exception as exc:
                        codes = re.findall(r"net::[A-Z_]+", str(exc))
                        errors.append(codes[0] if codes else type(exc).__name__)
                    finally:
                        page.close()
                    if records and len(records) >= 50:
                        break
                    if len(errors) >= 2 and readable == 0:
                        break
            finally:
                browser.close()
        if not records:
            # Zero extracted candidates cannot be described as validated working discovery.
            raise DiscoveryAccessError(
                "No public Ethiopian-relevant candidates extracted. "
                + ", ".join(errors[:3])
            )
        return list(records.values())[:100]
