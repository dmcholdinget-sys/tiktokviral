# Provider feasibility and limitations

## Current evidence

The selected GitHub repository was empty. Git read access worked, but the remote had no commits or branches. No licensed provider account, feed credentials, Telegram bot, or publisher chat bindings were supplied. The user requested Playwright public-page discovery; that provider is enabled and scheduled.

The Playwright adapter visits TikTok Creative Center and topic/language search pages without a creator whitelist. It expands queries from observed hashtags/topics, extracts publicly rendered hydration/DOM video metadata, and filters explicit Ethiopian signals. It does not log in, solve CAPTCHAs, spoof browser fingerprints, or evade access controls. Chromium launch and representative rendered-page extraction were tested. Actual TikTok access currently fails at the cloud egress proxy; no live candidate extraction has passed yet.

The fixture adapter is tested and clearly marked synthetic. Manual import and the HTTPS JSON feed adapter share validated ingestion and ranking. The feed connector can ingest repeated observations, hashtags, sounds, topics, local-language labels, and normalized source-derived signals. Scheduled runs refresh whatever the selected source supplies every 15 minutes.

## Operational prerequisite

For the enabled browser provider, apply the saved allowed-domain additions and rerun discovery. For an optional feed provider, select a licensed/authorized data source and demonstrate its permission for this use, Ethiopian coverage, query methods, supported languages, timestamp semantics, counter completeness, freshness, quotas, and actual end-to-end ingestion. Configure DISCOVERY_FEED_URL and, if required, DISCOVERY_API_TOKEN securely. Add the provider hostname to the cloud environment's allowed destinations; no domain is guessed in this configuration.

If the source API does not implement the documented feed contract, add a provider-specific adapter. This connector does not magically translate proprietary schemas. TikTok Research API access is neither guaranteed nor presumed suitable for live commercial discovery. No undocumented recommendation-feed access, scraping evasion, creator whitelist, or automated TikTok upload is implemented. Public browser extraction is best-effort and reports inaccessible or unusable pages as failed runs rather than fabricated results.

## Measurement plan

Record successful/failed runs, count new candidates by language and region, and compare source timestamps with collection times. Measure null-counter rates, publication age, repeat-observation frequency, and daily discovery volume over at least seven days. Agree acceptable provider-specific latency and coverage before claiming autonomous live readiness.

Propagation and novelty are supplied evidence, not invented platform estimates. Topic lifecycle currently uses observed cluster sizes as a transparent baseline heuristic. Prediction quality remains unvalidated until enough verified publishing outcomes and held-out evaluation exist.
