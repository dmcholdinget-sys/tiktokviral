# Administrator and publisher guide

## Administrator

1. Run setup, create a superuser, and sign in. Optionally load labeled demo data with `manage.py seed_demo`.
2. Set passwords for the four publisher users. In administration, edit display names, daily limits, active state, and add publishers as needed. Additional users need a PublisherProfile. For an analyst, create a non-staff user in the Analyst group. Content administrators are active staff users; only superusers configure providers, models, and private media in Django administration.
3. Playwright public-page discovery is enabled and scheduled. Apply the TikTok network destinations in environment settings, then run it from System health. It searches Ethiopian topic/language signals and expands observed hashtags without a creator list. Inspect failures and source freshness. Optionally connect an authorized feed in environment settings and enable its DiscoveryProvider after validating access. System health shows run results and missing integration configuration.
4. Review ranked candidates. Inspect publication/observation times, confidence, missing metrics, provenance, source links, and score components. Open the source before approving. Document safety-flag review. Unknown rights allow link-only opportunities; uploading/downloading media requires current documented ownership, license, or permission.
5. Approve or reject. Select one, several, or all eligible publishers and queue assignments. Duplicate assignments and per-publisher daily limits are enforced. Family members can decide to create an original response to a trend rather than reuse a source video.
6. Review the distribution queue. Telegram sends require bot configuration and linked publisher chats. If a send is uncertain, inspect the chat and use the assignment's reconciliation form; record a note before retrying or confirming sent.
7. Review submitted publications and performance. Verify metrics only after checking evidence; CSV exports include source-linked assignment information. Self-reported follower gains are attributed by the publisher and are not proof of causation.
8. Generate an inactive learning proposal with `manage.py propose_model --model-version review-YYYYMMDD` once at least 30 distinct verified 12–36-hour outcomes with varied pre-assignment evidence exist. Evaluate held-out outcomes before switching models. Deactivate the old model before activating the reviewed proposal.

## Publisher

Sign in with the credentials provided by your administrator. You see only your own assignments and content. The administrator can privately send your one-time `/start TOKEN` command to link your private Telegram chat. Tokens rotate after successful binding; do not share them.

Accept or decline an opportunity on the site or through the Telegram buttons. Publish manually using original or authorized material, then report the HTTPS post URL and publication time on the assignment page, or use `/published ASSIGNMENT_ID HTTPS_URL` in the bot's private chat after accepting.

Record metrics on the assignment page. Leave unavailable counters blank. Submit observations around 2, 6, 24, 48, and 72 hours as practical. Reports remain labeled self-reported until administrator verification. The system never logs into your TikTok account or posts on your behalf.
