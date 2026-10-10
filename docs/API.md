# API and authorized feed contract

The browsable REST API lives under `/api/`. Login through Django's session flow. State-changing session requests must carry a CSRF token. Authentication is mandatory; list endpoints are paginated (30 records/page). Per-user throttle: 120 requests/minute.

| Method | Route | Permissions / payload |
|---|---|---|
| GET | `/api/candidates/` or `/{id}/` | Staff/analyst: all; publisher: assigned and not revoked. Filters: q, language, category, review_status |
| POST | `/api/candidates/import/` | Staff; JSON array of feed records, maximum 1000 |
| POST | `/api/candidates/{id}/review/` | Staff; decision approved/rejected, notes, optional rights and evidence |
| POST | `/api/candidates/{id}/assign/` | Staff; `{"publishers":[1,2]}`; approved candidates only |
| GET | `/api/assignments/` or `/{id}/` | Staff: all; publisher: own |
| POST | `/api/assignments/{id}/transition/` | Owner: status accepted/declined; staff: revoked |
| POST | `/api/assignments/{id}/publish/` | Owner, accepted assignment; url and published_at (ISO-8601) |
| GET | `/api/posts/` or `/{id}/` | Staff: all; publisher: own |
| GET, POST | `/api/metrics/` | Owner/staff; post ID, observed_at, optional counters and followers_gained |
| POST | `/api/metrics/{id}/verify/` | Staff; records verification and audit |
| POST | `/telegram/webhook/` | Telegram secret header, no session authentication |

Metric verification/source fields cannot be set by a publisher. Missing metrics are null; zero is an actual measured zero. Duplicate publication URLs and invalid transitions are rejected. Unauthorized object reads return 404, and forbidden actions return 403.

## Feed record format

An approved provider must return an HTTPS response with a JSON list. No redirects; maximum 5 MB and 1000 records per request. Optional bearer authentication uses DISCOVERY_API_TOKEN. TLS verification remains enabled. The endpoint is configured by the environment owner, not by publishers.

```json
[{
  "platform": "tiktok",
  "canonical_id": "source-stable-video-id",
  "url": "https://www.tiktok.com/@creator/video/123",
  "title": "Source caption",
  "creator": "creator",
  "language": "am",
  "category": "Culture",
  "published_at": "2026-10-09T07:00:00Z",
  "source_timestamp": "2026-10-09T08:00:00Z",
  "signals": {
    "relevance": 0.9,
    "propagation": null,
    "novelty": null,
    "topics": ["Coffee culture"],
    "hashtags": ["ethiopia"],
    "sounds": ["source-sound-id"]
  },
  "safety_flags": [],
  "observations": [{
    "observed_at": "2026-10-09T08:00:00Z",
    "views": 1200,
    "likes": 80,
    "comments": null,
    "shares": null
  }]
}]
```

Valid platforms: tiktok, youtube, instagram, fixture. Signals are 0–1 or null and must come from documented source evidence. Publication time may be null. Counters must be nonnegative and observation timestamps cannot be in the future. Velocity requires two observations with increasing time; counter corrections do not produce a negative growth rate. Engagement needs views, likes, comments, and shares. A single view count cannot imply velocity.

Identity is `(platform, canonical_id)`; providers must use the same platform's canonical identifier. Observations are immutable and unique by candidate/provider/time. Entire import batches validate before being committed. Every candidate ingestion is linked to its provider run; refreshing data preserves review/rights decisions, while new safety flags return approved candidates to pending review.
