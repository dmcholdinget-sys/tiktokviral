# PRODUCT REQUIREMENTS DOCUMENT (PRD)

## Ethiopian Viral Trend Intelligence & Telegram Distribution System

**Version:** 1.0  
**Date:** October 9, 2026  
**Technology:** Django, PostgreSQL, Celery, Redis, Telegram Bot API  
**Primary Market:** Ethiopia and Ethiopian diaspora  
**Initial Team:** 1 Administrator + 4 Family Content Publishers  
**Product Type:** Automated Trend Intelligence, Content Review, and Distribution Platform

---

# 1. Executive Summary

## 1.1 Product Overview

The Ethiopian Viral Trend Intelligence System is a web-based platform designed to autonomously discover, analyze, rank, and distribute emerging viral content relevant to Ethiopian audiences.

The platform must identify potentially viral videos without relying on a manually maintained list of TikTok creators or channels.

Instead, the discovery engine shall identify emerging content through dynamically discovered topics, Amharic and other Ethiopian-language signals, hashtags, sounds, engagement patterns, and trend propagation.

The system shall continuously assess discovered videos and present them in a ranked dashboard.

The administrator will review candidates and approve suitable content for distribution to four family members through Telegram.

Family members will independently publish content manually on their respective social media accounts. The system will not publish directly to TikTok.

The platform will collect publishing outcomes and performance data, allowing the discovery engine to improve its recommendations over time.

## 1.2 Main Objective

**Identify potentially viral Ethiopian content as early as reliably possible, deliver the best opportunities to family members through Telegram, and learn which discovery strategies produce the strongest real-world performance.**

## 1.3 Business Goals

| Goal | Description |
|---|---|
| Early discovery | Discover emerging trends before widespread saturation |
| Autonomous operation | Eliminate manual creator/channel searching |
| Ethiopian relevance | Prioritize Ethiopian and diaspora audiences |
| Opportunity ranking | Identify promising content using measurable signals |
| Time efficiency | Reduce unnecessary manual video searching |
| Content distribution | Deliver approved opportunities through Telegram |
| Family coordination | Track which members receive and publish opportunities |
| Performance tracking | Measure views, engagement, and follower growth |
| Continuous learning | Improve recommendations based on actual outcomes |
| Expansion | Support additional members and platforms later |

## 1.4 Core Product Principle

The system shall recommend **individual viral opportunities, not predetermined creators**.

A new creator with 300 followers and a rapidly growing video must be eligible to outrank a popular creator with 500,000 followers whose video is growing slowly.

Creator popularity may be used for normalization but must not provide an automatic ranking advantage.

---

# 2. Scope of the System

## 2.1 Included

1. Autonomous trend discovery.
2. Ethiopian and diaspora relevance detection.
3. Dynamic keyword, sound, and hashtag discovery.
4. Video metadata collection.
5. Repeated engagement metric observation.
6. Viral potential scoring.
7. Emerging trend detection.
8. Duplicate and saturation detection.
9. Video categorization.
10. AI-assisted content classification.
11. Video review and approval workflow.
12. Permission-aware media library.
13. Telegram Bot integration.
14. Family member management.
15. Video opportunity assignment.
16. Publishing status tracking.
17. Manual publishing-link submissions.
18. Performance data entry and optional authorized imports.
19. Analytics dashboard.
20. Feedback-driven ranking optimization.
21. Background processing.
22. Notifications and system administration.
23. Audit logging and reports.

## 2.2 Excluded

The initial product shall not include:

- Automatic uploading to TikTok.
- TikTok account login automation.
- Browser fingerprint spoofing.
- Residential proxy rotation for account evasion.
- Artificial engagement generation.
- Automated liking, commenting, or following.
- Circumvention of platform anti-bot systems.
- Unauthorized downloading and redistribution of copyrighted third-party media.
- Guaranteed access to a complete, live TikTok recommendation feed.

## 2.3 Important Discovery Dependency

Real-time discovery depends on the quality and freshness of authorized source data.

The architecture must support multiple interchangeable discovery providers.

No provider shall be assumed to expose all public TikTok videos, all Ethiopian audience recommendations, or continuously updated engagement counters.

If a source cannot supply a metric, the system must mark that metric as unavailable rather than inventing a value.

---

# 3. User Roles and Permissions

## 3.1 User Roles

| Role | Access |
|---|---|
| Super Administrator | Full system configuration, users, integrations, algorithms |
| Content Administrator | Review candidates, approve, reject, distribute, monitor |
| Family Publisher | Receive assigned videos, report publishing, submit metrics |
| Analyst (optional) | Read-only access to trends, performance, reports |

The initial installation shall support one administrator and four registered family publishers.

The system must permit the administrator to add additional publishers without changing application code.

## 3.2 Permission Requirements

- Family publishers may only see their assigned content.
- Family publishers cannot modify global viral scores.
- Family publishers cannot approve or reject global discovery candidates.
- Administrators may send content to one, multiple, or all eligible family publishers.
- Administrators may revoke assignments.
- Super Administrators control integrations and application-wide settings.
- All critical actions must be logged.

---

# 4. Module 1 — Autonomous Trend Discovery Engine

**Priority: P0 — Critical**

## 4.1 Objective

Automatically identify new and emerging viral videos relevant to Ethiopian viewers without a fixed channel list.

## 4.2 Discovery Methods

The engine must support multiple discovery strategies.

### A. Language-Based Discovery

Detect content signals associated with:

- Amharic.
- Afaan Oromo.
- Tigrinya.
- Ethiopian English.
- Common Ethiopian slang.
- Ethiopian-language transliterations.
- Mixed-script captions.

Signals may come from available captions, subtitles, text metadata, speech transcripts, or source-provided language indicators.

Language alone must not be interpreted as proof of creator location or audience geography.

### B. Geographic Relevance

The application must support:

- Ethiopia-focused candidates.
- Ethiopian diaspora candidates.
- Globally published videos with Ethiopian cultural relevance.

Possible signals include source-provided regional metadata, culturally relevant topics, Ethiopian-language captions, and known Ethiopian locations.

Every geographic inference must include a confidence value and evidence source.

### C. Hashtag Discovery

The system shall dynamically identify relevant hashtags and related tags.

Example search concepts include Ethiopian comedy, relationships, daily life, family content, food, entertainment, and cultural trends.

Hashtags are discovery hints rather than a permanent channel or content whitelist.

The system should expand its search vocabulary when new useful terms emerge.

### D. Sound-Based Discovery

When sound or music identifiers are available, the system shall:

- Identify recurring sounds.
- Count newly discovered uses.
- Observe changes in sound usage.
- Associate sounds with topics and candidate videos.
- Rank emerging sounds.
- Link related candidate videos.

### E. Engagement-Based Discovery

The engine shall identify videos showing unusual growth relative to their age and available audience-size context.

Potential signals:

- View growth.
- Comment growth.
- Share growth.
- Engagement rates.
- Engagement acceleration.
- Video freshness.
- Number of independent accounts participating in the same trend.

### F. Dynamic Topic Discovery

The discovery engine must identify new topics automatically instead of restricting searches to predefined categories.

For example, an emerging Ethiopian comedy phrase or local challenge should become a temporary search signal after sufficient supporting evidence is detected.

Newly discovered signals shall have an expiration or decay mechanism so obsolete trends do not dominate the search indefinitely.

## 4.3 Discovery Data Providers

Implement a modular provider architecture.

Each provider must expose a consistent internal interface for:

- Finding candidates.
- Retrieving available metadata.
- Retrieving available engagement counters.
- Providing source timestamps.
- Declaring supported regions and query methods.
- Reporting rate limits and provider errors.

Supported provider types:

| Provider Type | Intended Function |
|---|---|
| Licensed data provider | Automated discovery and engagement snapshots |
| Authorized public trend source | Sound, hashtag, and trend discovery where permitted |
| Manual URL import | Add opportunities discovered outside the system |
| Authorized external dataset | Batch import of video and engagement records |
| Future provider connector | Add new data sources without changing scoring logic |

**Mandatory prerequisite:** Before promising fully autonomous discovery, developers must demonstrate an authorized provider with measurable coverage, acceptable latency, and reliable metadata.

TikTok's Research API may serve approved analytical research purposes where eligible, but shall not be treated as a guaranteed real-time trending source.

## 4.4 Discovery Frequency

Configurable defaults:

| Task | Target Frequency |
|---|---|
| Discover emerging candidates | Every 15 minutes |
| Refresh priority-candidate metrics | Every 30 minutes |
| Refresh normal-candidate metrics | Every 60 minutes |
| Discover related topics and sounds | Every 60 minutes |
| Recalculate viral scores | After every meaningful metric update |
| Deduplicate candidates | At ingestion |
| Expire outdated opportunities | Continuous scheduled job |
| Generate daily discovery summary | Daily |

These intervals represent desired application scheduling. Actual data freshness must remain dependent on provider capabilities and rate limits.

## 4.5 Freshness Rules

Default candidate age bands:

| Age Since Publication | Priority |
|---|---|
| 0–2 hours | Highest discovery priority |
| 2–6 hours | Very high |
| 6–12 hours | High |
| 12–24 hours | Normal |
| Older than 24 hours | Historical or exceptional candidates |

The engine must calculate freshness from the source video's publication timestamp, not simply the time it entered the database.

Where publication time is unknown, the video shall be marked **Publication Time Unverified**.

## 4.6 Discovery Output

Every candidate record must contain, where available:

- Internal video ID.
- Source platform.
- Source URL.
- Source video ID.
- Creator identifier.
- Video description.
- Publication time.
- Discovery time.
- Latest observation time.
- Thumbnail URL.
- Available preview.
- Duration.
- Detected language.
- Geographic relevance indicators.
- Hashtags.
- Sound identifier.
- Category.
- Latest known views, likes, comments, shares.
- Engagement history.
- Viral score.
- Confidence level.
- Trend stage.
- Rights and content-review status.
- Discovery provider.
- Data freshness indicator.

Unknown fields must remain null or explicitly unavailable.

## 4.7 Acceptance Criteria

- A new candidate can enter the system without its creator being on a predefined account list.
- Duplicate imports of the same source video do not create multiple canonical records.
- Every candidate has source provenance.
- Provider failures do not stop other providers from functioning.
- Missing engagement metrics do not cause the system to generate fictional scores.
- The dashboard clearly identifies stale data and unavailable metrics.
- Discovery queries can evolve from observed topics and sounds.
- Authorized data-source integration is demonstrated using real sample records before the phase is considered complete.

---

# 5. Module 2 — Viral Intelligence and Ranking Engine

**Priority: P0 — Critical**

## 5.1 Objective

Identify which discovered videos have the strongest evidence of future growth.

The engine must focus on growth behavior rather than total popularity.

## 5.2 Core Measurements

### A. View Velocity

Views gained per hour between two valid observations.

**Formula:**

View Velocity = (Current Views − Previous Views) / Hours Between Observations

Example:

- First observation: 2,000 views.
- Second observation, one hour later: 8,000 views.
- Calculated view velocity: 6,000 views/hour.

If only one observation is available, the system may display average lifetime views/hour separately, but must not label that figure as observed recent velocity.

### B. Comment Velocity

Comment Velocity = (Current Comments − Previous Comments) / Hours Between Observations

### C. Share Velocity

Share Velocity = (Current Shares − Previous Shares) / Hours Between Observations

### D. Engagement Rate

Default available-engagement rate:

Engagement Rate = (Likes + Comments + Shares) / Views × 100

The interface must identify which engagement components were actually available.

If a component is unavailable, the metric must be marked as partial or use a separately defined rate.

### E. Growth Acceleration

Growth Acceleration = (Current Velocity − Previous Velocity) / Previous Velocity

A minimum of three properly spaced counter observations is required to estimate successive interval velocities and acceleration.

If previous velocity is zero, acceleration must be marked undefined and handled using an explicitly defined fallback rule.

### F. Relative Creator Performance

Compare a video's performance with available historical observations of the creator.

A new creator must not be penalized simply because reliable follower or historical statistics are absent.

### G. Local Relevance

Estimate how closely content relates to Ethiopian viewers using available evidence.

### H. Trend Propagation

Detect whether a hashtag, sound, challenge, phrase, or content pattern is spreading across multiple unrelated accounts.

Do not treat identical reposts by one account as independent trend participation.

### I. Saturation

Estimate whether an opportunity is already widespread or declining.

Possible evidence:

- Many repeated examples.
- Declining growth velocity.
- Trend age.
- High adoption without further acceleration.

## 5.3 Initial Viral Potential Algorithm

Use an explainable weighted scoring model with a 0–100 scale.

| Component | Proposed Weight |
|---|---:|
| View velocity | 25% |
| Growth acceleration | 20% |
| Engagement quality | 15% |
| Ethiopian relevance | 15% |
| Freshness | 10% |
| Trend propagation | 10% |
| Novelty / low saturation | 5% |
| **Total** | **100%** |

This is the initial product hypothesis, not a scientifically validated forecasting model.

Each component must be normalized using configurable benchmarks, preferably segmented by content age and relevant content class.

The score must not be calculated by blindly treating unavailable metrics as zero.

Instead:

1. Calculate a provisional score from available signals.
2. Record which signals contributed.
3. Calculate a separate data-completeness value.
4. Display lower confidence when critical evidence is missing.
5. Permit administrator configuration of minimum eligible evidence.

All rankings must retain an algorithm-version identifier.

## 5.4 Ranking Labels

| Score | Display Label |
|---|---|
| 85–100 | Breakout Candidate |
| 70–84 | Rising Fast |
| 55–69 | Worth Watching |
| 40–54 | Early / Uncertain |
| 0–39 | Low Priority |

Labels must not promise virality. A high score indicates stronger evidence under the current model, not a guaranteed outcome.

## 5.5 Confidence Classification

Confidence is separate from viral score.

Example:

- **High Confidence:** Fresh observations, reliable provider, multiple usable metrics.
- **Medium Confidence:** Some supporting observations, partial metric coverage.
- **Low Confidence:** Limited evidence or uncertain source freshness.
- **Insufficient Data:** Scoring requirements not satisfied.

## 5.6 Trend Lifecycle

Each candidate shall have a trend stage:

- New.
- Emerging.
- Accelerating.
- Sustained.
- Peak Suspected.
- Declining.
- Expired.

Stage transitions must use configurable rules based on available observations.

## 5.7 Duplicate Detection

Implement multiple layers:

1. Exact source-video ID.
2. Canonical source URL.
3. Exact media checksum when authorized media exists.
4. Perceptual video hashing where source material is lawfully available.
5. Similar captions, audio, or sound identifiers for candidate clustering.

The application must distinguish between:

- Exact duplicate.
- Near-duplicate.
- Related trend.
- Independent original content.

Related trends should be grouped rather than automatically deleted.

## 5.8 Saturation Detection

The engine shall identify candidates that may have passed their strongest opportunity window.

The saturation assessment must be displayed alongside the viral score.

Candidates with high historical popularity but slowing current growth should be deprioritized for immediate distribution.

## 5.9 Feedback-Based Ranking

Initially use deterministic scoring.

Once sufficient verified performance history exists, introduce:

- Outcome-based weight tuning.
- Category-specific recommendations.
- Member-specific content affinity.
- Ranking model comparison.
- Historical forecasting evaluation.

Performance feedback must be based on actual reported results rather than only administrator approval choices.

The system shall retain the original score and model version for every recommendation.

---

# 6. Module 3 — Content Review and Media Library

**Priority: P0 — Critical**

## 6.1 Objective

Provide administrators with a centralized location to inspect, approve, reject, categorize, and prepare video opportunities for family members.

## 6.2 Candidate Review Page

Each discovered video must have a detail page showing:

- Thumbnail or supported preview.
- Source link.
- Creator information when available.
- Description.
- Publication date and time.
- Latest engagement metrics.
- Trend history.
- Viral potential score.
- Confidence and explanation.
- Content category.
- Hashtags and sound metadata.
- Ethiopian relevance evidence.
- Duplicate status.
- Content safety flags.
- Copyright or reuse authorization status.
- Distribution history.

## 6.3 Administrator Actions

- Approve.
- Reject.
- Save for later.
- Watch.
- Recheck metrics.
- Change category.
- Add notes.
- Mark unsuitable.
- Assign to family member.
- Assign to multiple members.
- Request or attach reusable media with appropriate permission.

## 6.4 Review Statuses

- Discovered.
- Pending Review.
- Watching.
- Approved.
- Rejected.
- Distribution Ready.
- Distributed.
- Archived.

## 6.5 Rights-Aware Media Handling

The system must differentiate between discovering content and having permission to redistribute the actual file.

**Media statuses:**

| Status | Meaning |
|---|---|
| Link Only | Source link available; no media reuse permission documented |
| Permission Requested | Rights confirmation pending |
| Authorized | Required media and audio permissions documented |
| Owner Supplied | Content supplied by its rights holder |
| Restricted | Downloading or redistribution not permitted |
| Revoked | Previously granted permission withdrawn |

Only eligible media records may enter the automated file-delivery workflow.

For link-only candidates, Telegram shall distribute the original source URL, a trend summary, and suggestions for making independently created content based on the trend.

The system must not treat a platform's download button, publicly accessible URL, or watermark removal as evidence of legal reuse permission.

## 6.6 Media Storage Requirements

For authorized media:

- Store the original file.
- Store file checksum.
- Preserve metadata.
- Generate a preview image.
- Record duration and dimensions.
- Record media ownership or permission evidence.
- Support optional review-approved derivative files.
- Generate expiring download links.
- Allow administrators to remove or revoke media.

## 6.7 Quality Requirements

For media accepted into the library:

- Confirm the file can be decoded.
- Record media type.
- Detect corruption.
- Identify duplicate files.
- Record file size.
- Validate the permitted delivery format.
- Flag potentially unsuitable audio and video.
- Preserve original source attribution.

## 6.8 Content Categories

Initial categories:

- Comedy.
- Family.
- Relationships.
- Entertainment.
- Lifestyle.
- Food.
- Ethiopian Culture.
- Sports.
- Educational.
- Motivational.
- Challenges.
- Trending Sound.
- Other.

Administrators may add, merge, rename, disable, or reorder categories.

## 6.9 Content Safety

Automatically flag potentially sensitive content for administrator review, including:

- Graphic violence.
- Harassment.
- Hate speech.
- Sexual content.
- Dangerous acts.
- Privacy violations.
- Potential misinformation.
- Political controversy.
- Religious controversy.
- Potential copyright restrictions.

A flag is a review signal, not proof of wrongdoing.

---

# 7. Module 4 — Telegram Family Distribution

**Priority: P0 — Critical**

## 7.1 Objective

Automatically deliver administrator-approved opportunities to selected family members through Telegram.

Family members will manually publish suitable content on their own accounts.

## 7.2 Telegram Bot Setup

The system must support one centrally managed Telegram bot.

Each family member shall:

1. Receive a secure bot invitation.
2. Start the bot.
3. Complete account linking.
4. Become eligible for assignments.
5. Receive approved content packages.

The application shall maintain the member's Telegram chat identifier and connection state.

## 7.3 Content Delivery Package

Every Telegram opportunity should include:

**VIRAL CONTENT OPPORTUNITY**

- Candidate title or topic.
- Viral score and confidence.
- Category.
- Trend age.
- Original source link.
- Video preview or authorized file.
- Relevant sound and hashtags.
- Suggested content angle.
- Suggested caption, where appropriate.
- Recommended action.
- Priority.
- Assignment ID.

The system may suggest content adaptations, but must not imply that superficial edits make unauthorized redistribution permissible.

## 7.4 Telegram Action Buttons

Family members must be able to respond with:

- Accept.
- Skip.
- Posted.
- Need Help.

If a member selects **Posted**, the bot shall request the social media post URL.

The system shall validate and store the submitted URL.

## 7.5 Assignment Lifecycle

Each assigned content opportunity follows this process:

**Approved → Queued → Sent → Accepted → Posted → Verified → Completed**

Alternative branches:

- Skipped.
- Expired.
- Delivery Failed.
- Cancelled.
- Needs Review.

Telegram delivery success means the bot successfully sent the message. It does not prove the family member viewed the message.

## 7.6 Assignment Modes

### Individual Assignment

Send an approved opportunity to one designated family member.

### Multiple Assignment

Send the opportunity to selected family members.

### Broadcast Assignment

Send an opportunity to all eligible members.

### Recommended Assignment

The system suggests which family member is most likely to benefit based on past performance and category preferences.

The administrator retains final approval.

## 7.7 Duplicate Distribution Protection

The application shall:

- Prevent accidental duplicate assignments to the same member.
- Track previous assignments.
- Warn when the same content has already been published by another member.
- Allow intentional redistribution or variation after review.
- Enforce configurable daily distribution limits.

## 7.8 Default Limits

Initial configurable defaults:

| Parameter | Default |
|---|---|
| Family members | 4 |
| Assignments per member per day | 3 |
| Low-priority notifications | Batched |
| High-priority notifications | Immediate after approval |
| Reminder after no response | 2 hours |
| Final reminder | 6 hours |
| Assignment expiry | 24 hours |

All defaults shall be configurable.

## 7.9 Telegram Delivery Rules

- Use Telegram Bot API.
- Retry temporary failures with exponential backoff.
- Respect rate limits.
- Keep a durable delivery log.
- Avoid duplicate sends during retries.
- Record Telegram message IDs.
- Support file delivery where size and permission requirements allow.
- Send secure media links when direct delivery is unsuitable.
- Protect the bot authentication token.
- Authenticate callback requests and validate assignment ownership.

## 7.10 Member Publishing Confirmation

After posting manually, a family member must be able to provide:

- Published post URL.
- Platform.
- Posting timestamp.
- Optional caption.
- Optional remarks.

The administrator may verify the post.

The system must not assume that clicking **Posted** proves publication without a submitted link or another accepted verification mechanism.

---

# 8. Module 5 — Performance Tracking and Learning

**Priority: P0 for reporting, P1 for adaptive learning**

## 8.1 Objective

Determine whether selected opportunities produce meaningful performance on the family members' accounts.

## 8.2 Performance Data

For each published assignment, track:

- Family member.
- Original discovery candidate.
- Published post URL.
- Publishing time.
- Report time.
- Views.
- Likes.
- Comments.
- Shares.
- Saves, if available.
- Followers before publishing, if reported.
- Followers after publishing, if reported.
- Engagement rate.
- Performance evaluation window.
- Data collection method.

Performance collection may use manual entry, authorized import files, or an integration explicitly permitted by the relevant platform.

## 8.3 Measurement Windows

Support the following checkpoints:

| Checkpoint | Purpose |
|---|---|
| 2 hours | Initial response |
| 6 hours | Early traction |
| 24 hours | First-day outcome |
| 48 hours | Continued spread |
| 7 days | Longer-term performance |

Missing updates should remain pending or unavailable.

Metrics entered at different checkpoints must be retained as historical snapshots rather than overwriting earlier observations.

## 8.4 Key Performance Indicators

### Discovery KPIs

- Candidates discovered.
- New candidates per day.
- Candidates by age.
- Candidates by category.
- High-scoring candidates.
- Approved percentage.
- Duplicate percentage.
- Available metric coverage.
- Discovery-to-review latency.

### Distribution KPIs

- Opportunities approved.
- Opportunities assigned.
- Telegram send success.
- Acceptance rate.
- Skipped assignments.
- Published assignments.
- Time from approval to distribution.
- Time from distribution to publication.

### Content Performance KPIs

- Total reported views.
- Median views per published post.
- Engagement rate.
- Shares per 1,000 views.
- Median views by content category.
- Results by family member.
- Results by discovery source.
- Results by trend stage.
- Follower growth where verified.

## 8.5 Follower Attribution

Follower growth must not automatically be attributed to one video.

Where follower counts are manually reported, the dashboard shall display observed follower changes and clearly label attribution as estimated or unverified.

Verified per-post follower attribution may only be shown when suitable source data exists.

## 8.6 Learning Engine

The learning engine should answer:

- Which categories consistently perform better?
- Which trend stages lead to stronger results?
- Which discovery providers produce useful candidates?
- Does faster publication correlate with higher engagement?
- Which family members perform best with particular content styles?
- Do high viral scores actually predict future outcomes?
- Are some signals over-weighted or ineffective?

## 8.7 Learning Method

**Stage 1 — Rules-Based**

Use the fixed weighted ranking algorithm.

**Stage 2 — Statistical Evaluation**

Compare scores against verified outcomes.

Measure ranking quality, error, and category-specific performance.

**Stage 3 — Adaptive Recommendations**

Allow model weights to be adjusted using historical results.

**Stage 4 — Advanced Prediction**

After a sufficient validated dataset exists, optionally train a predictive model.

No model shall automatically retrain on unreliable metrics or use unverified data as unquestioned ground truth.

## 8.8 Recommendation Explanation

Every recommendation should display a human-readable explanation.

Example:

"This candidate ranks highly because its recent view growth is strong, its available engagement signals are above the current category baseline, and its Ethiopian-language relevance is high."

Explanations must reflect the actual scoring inputs.

---

# 9. Dashboard and User Interface

## 9.1 General Design

The application shall use a responsive modern dashboard.

Requirements:

- Desktop-first administrator interface.
- Fully usable mobile interface.
- Clear navigation.
- Fast filtering and sorting.
- Video-centric layouts.
- Minimal repeated clicking.
- Ethiopian language compatibility.
- Support for English and Amharic interface localization.

## 9.2 Primary Navigation

| Menu | Function |
|---|---|
| Overview | Main analytics and operational summary |
| Trend Finder | Newly discovered and ranked opportunities |
| Rising Trends | Sounds, hashtags, and topics gaining traction |
| Video Library | All candidates and reviewed content |
| Review Queue | Pending administrator decisions |
| Distribution | Telegram assignments and schedules |
| Family Members | Team profiles and individual performance |
| Published Content | Published post records and metrics |
| Analytics | Reporting and trend evaluation |
| Learning Insights | Ranking accuracy and successful patterns |
| Sources | Discovery provider status and configuration |
| Settings | Categories, thresholds, notifications, permissions |
| System Logs | Background jobs, errors, and audit events |

## 9.3 Dashboard — Overview Page

### Summary Cards

- Videos Discovered Today.
- Breakout Candidates.
- Rising Trends.
- Pending Review.
- Approved Today.
- Sent to Telegram.
- Confirmed Published.
- Total Reported Views.

### Main Charts

- Discovery volume over time.
- Viral score distribution.
- Trending categories.
- Content freshness distribution.
- Published content performance.
- Family member performance.

### Top Candidates Table

| Video | Category | Score | Confidence | Age | Status | Action |
|---|---|---:|---|---|---|---|
| Candidate A | Comedy | 92 | High | 1h 20m | New | Review |
| Candidate B | Family | 87 | Medium | 3h 10m | Watching | Review |
| Candidate C | Lifestyle | 81 | High | 5h 05m | Approved | Assign |

This table uses illustrative sample data, not actual TikTok results.

## 9.4 Trend Finder Page

Provide grid and table views.

Filters:

- Date range.
- Publication age.
- Category.
- Language.
- Geographic relevance.
- Viral score.
- Confidence.
- Trend stage.
- Source provider.
- Engagement availability.
- Rights status.
- Review status.

Sort by:

- Viral potential.
- Freshness.
- View velocity.
- Comment velocity.
- Share velocity.
- Engagement rate.
- Score change.
- Discovery time.

Support multi-select and batch review.

## 9.5 Candidate Detail Page

Display:

1. Main video or preview panel.
2. Source information.
3. Viral score with contributing components.
4. Engagement trend chart.
5. Trend-stage history.
6. Hashtag and sound associations.
7. Related videos.
8. Content safety and rights information.
9. Review controls.
10. Telegram distribution controls.
11. Distribution history.
12. Post-performance results.

## 9.6 Rising Trends Page

Show emerging:

- Sounds.
- Hashtags.
- Phrases.
- Challenges.
- Topics.

Each trend must display:

- Number of linked candidates.
- Change in observed adoption.
- Earliest known observation.
- Latest observation.
- Relevant region/language evidence.
- Confidence.
- Representative source videos.

## 9.7 Family Performance Page

For each member, display:

- Assigned opportunities.
- Accepted opportunities.
- Posted opportunities.
- Skipped opportunities.
- Posting rate.
- Reported views.
- Median views per post.
- Engagement performance.
- Best-performing categories.
- Outstanding status reports.

## 9.8 Distribution Queue Page

Columns:

- Opportunity.
- Assigned member.
- Priority.
- Approval time.
- Send status.
- Member response.
- Posting status.
- Published URL.
- Follow-up status.

Administrators must be able to retry, cancel, reassign, or archive records.

---

# 10. End-to-End User Workflows

## 10.1 Autonomous Discovery Workflow

**Step 1:** Scheduler starts a discovery cycle.

**Step 2:** Provider adapters retrieve permitted source data.

**Step 3:** Raw candidate data is normalized.

**Step 4:** Duplicate checking runs.

**Step 5:** Ethiopian relevance signals are evaluated.

**Step 6:** Valid candidates are stored.

**Step 7:** Available metric snapshots are recorded.

**Step 8:** Viral potential and confidence are calculated.

**Step 9:** Candidates are ranked.

**Step 10:** High-priority opportunities enter the review queue.

## 10.2 Administrator Approval Workflow

**Discovery → Ranking → Review → Rights Check → Approval → Family Assignment → Telegram Delivery**

The administrator may reject or defer a candidate at any point before distribution.

## 10.3 Family Publishing Workflow

**Telegram Opportunity Received → Member Accepts → Member Creates or Uses Authorized Content → Member Posts Manually → Member Submits Link → System Records Publication → Performance Monitoring**

## 10.4 Feedback Workflow

**Publishing Results → Performance Snapshots → Outcome Analysis → Ranking Evaluation → Recommended Weight Adjustments → Administrator Review → Updated Ranking Version**

All automated learning changes must be traceable.

---

# 11. Technical Architecture

## 11.1 Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Django 5.2 LTS |
| Database | PostgreSQL |
| API | Django REST Framework |
| Admin Dashboard | Django Templates, Bootstrap 5, JavaScript |
| Charts | Chart.js |
| Background Workers | Celery |
| Queue / Cache | Redis |
| Scheduler | Celery Beat |
| Telegram | Telegram Bot API |
| Image Processing | Pillow |
| Authorized Video Processing | FFmpeg |
| File Storage | Local private storage or S3-compatible object storage |
| Web Server | Nginx |
| Application Server | Gunicorn or another supported production ASGI/WSGI server |
| Deployment | Linux with systemd or containerized services |
| Logging | Structured application logs |
| Monitoring | Job and integration health dashboard |

The exact deployment server must be configurable.

## 11.2 Django Application Structure

Recommended Django apps:

| Django App | Responsibility |
|---|---|
| accounts | Authentication, roles, permissions |
| discovery | Data providers, source discovery, ingestion |
| trends | Hashtags, sounds, topics, clusters |
| videos | Canonical candidates and metadata |
| intelligence | Snapshots, scoring, trend stages |
| moderation | Review, approval, rights checks |
| media_library | Authorized file handling and storage |
| telegram_bot | Bot configuration, inbound/outbound messages |
| distribution | Assignments, queues, delivery states |
| publishers | Family member profiles |
| performance | Publishing records and performance snapshots |
| analytics | Charts, KPIs, reports |
| learning | Ranking evaluation and adaptive recommendations |
| notifications | Alerts and reminders |
| audit | Activity history and system events |
| configuration | Global application settings |

The apps should be separated by responsibility while sharing consistent domain models and service interfaces.

## 11.3 Background Jobs

Examples:

- discover_candidates
- normalize_candidates
- resolve_duplicates
- update_engagement_snapshots
- detect_trend_clusters
- calculate_viral_scores
- recalculate_trend_stages
- expire_outdated_candidates
- process_review_notifications
- send_telegram_assignment
- retry_failed_delivery
- send_pending_reminders
- request_performance_update
- calculate_dashboard_metrics
- evaluate_ranking_quality
- clean_expired_media
- check_provider_health

All background jobs must be idempotent where applicable.

Use retries, backoff, rate limiting, and error queues.

---

# 12. Database Requirements

The recommended database is PostgreSQL.

## 12.1 Core Tables

### User

- id
- username
- email
- password_hash
- role
- is_active
- created_at
- updated_at

### PublisherProfile

- id
- user_id
- display_name
- telegram_user_id
- telegram_chat_id
- telegram_link_status
- preferred_categories
- preferred_language
- timezone
- daily_assignment_limit
- is_active

### DiscoveryProvider

- id
- name
- provider_type
- enabled
- configuration_reference
- supported_capabilities
- last_success_at
- last_failure_at
- last_observed_latency
- status

### DiscoveryRun

- id
- provider_id
- started_at
- finished_at
- status
- records_received
- records_created
- duplicates_found
- error_summary

### VideoCandidate

- id
- platform
- source_video_id
- canonical_url
- creator_identifier
- description
- published_at
- discovered_at
- latest_observed_at
- duration_seconds
- thumbnail_url
- detected_language
- language_confidence
- ethiopian_relevance_score
- category_id
- review_status
- rights_status
- created_at
- updated_at

### CandidateDiscovery

Tracks candidate appearances across providers.

- id
- candidate_id
- provider_id
- discovery_run_id
- raw_payload_reference
- first_seen_at
- last_seen_at
- provider_record_identifier

### EngagementSnapshot

- id
- candidate_id
- provider_id
- observed_at
- received_at
- views
- likes
- comments
- shares
- favorites
- data_quality_status

### ViralScore

- id
- candidate_id
- algorithm_version
- calculated_at
- total_score
- confidence_level
- completeness_score
- view_velocity
- comment_velocity
- share_velocity
- acceleration
- freshness_score
- relevance_score
- saturation_score
- trend_stage
- component_details

### TrendSignal

- id
- signal_type
- normalized_value
- display_value
- first_seen_at
- last_seen_at
- relevance_confidence
- current_stage

### CandidateTrendSignal

- id
- candidate_id
- trend_signal_id
- evidence_type
- confidence

### TrendCluster

- id
- label
- cluster_type
- first_seen_at
- last_seen_at
- candidate_count
- lifecycle_stage

### CandidateCluster

- id
- candidate_id
- cluster_id
- similarity_score
- relationship_type

### ContentCategory

- id
- name
- description
- active
- display_order

### ContentReview

- id
- candidate_id
- reviewer_id
- decision
- notes
- reviewed_at

### MediaAsset

- id
- candidate_id
- storage_key
- filename
- file_size
- checksum
- mime_type
- width
- height
- duration
- processing_status
- permission_reference
- created_at

### RightsRecord

- id
- candidate_id
- rights_holder
- authorization_type
- permitted_uses
- evidence_reference
- valid_from
- valid_until
- status
- verified_by

### DistributionAssignment

- id
- candidate_id
- publisher_id
- assigned_by
- priority
- assignment_status
- scheduled_at
- sent_at
- accepted_at
- expired_at
- created_at

### TelegramDelivery

- id
- assignment_id
- telegram_message_id
- telegram_chat_id
- attempted_at
- delivered_at
- delivery_status
- retry_count
- error_message

### PublishedPost

- id
- assignment_id
- publisher_id
- platform
- published_url
- published_at
- reported_at
- verification_status
- verified_by
- notes

### PerformanceSnapshot

- id
- published_post_id
- observed_at
- received_at
- collection_method
- views
- likes
- comments
- shares
- saves
- follower_count
- verification_status

### RankingModelVersion

- id
- version
- weights
- benchmark_configuration
- activated_at
- deactivated_at
- evaluation_summary
- approved_by

### Notification

- id
- recipient_id
- notification_type
- reference_id
- message
- status
- created_at
- read_at

### AuditLog

- id
- actor_id
- action
- object_type
- object_id
- timestamp
- previous_value
- new_value

## 12.2 Database Design Rules

- Store timestamps in UTC and display using the user's configured timezone.
- Preserve original provider timestamps.
- Use database uniqueness constraints for canonical source IDs.
- Store historical snapshots as append-only observations.
- Never overwrite historical performance measurements.
- Use foreign keys to maintain relationships.
- Avoid deleting candidate records when only an individual assignment is cancelled.
- Use secure references for credentials and sensitive storage objects.
- Retain algorithm versions for historical comparisons.
- Index frequently filtered fields.
- Use pagination on large datasets.
- Use configurable retention policies for raw provider data and media.

---

# 13. Internal API Requirements

Use versioned application APIs under `/api/v1/`.

Recommended endpoints:

| Endpoint | Method | Function |
|---|---|---|
| /api/v1/dashboard/summary/ | GET | Overview KPIs |
| /api/v1/candidates/ | GET | Filtered candidate list |
| /api/v1/candidates/{id}/ | GET | Candidate details |
| /api/v1/candidates/{id}/review/ | POST | Approve or reject |
| /api/v1/candidates/{id}/score/ | GET | Scoring explanation |
| /api/v1/trends/ | GET | Emerging trend groups |
| /api/v1/sources/ | GET | Discovery sources |
| /api/v1/discovery/runs/ | GET | Discovery history |
| /api/v1/distribution/assignments/ | GET/POST | View or create assignments |
| /api/v1/distribution/assignments/{id}/ | GET | Assignment detail |
| /api/v1/distribution/assignments/{id}/cancel/ | POST | Cancel assignment |
| /api/v1/publishers/ | GET | Family members |
| /api/v1/published-posts/ | GET/POST | Publish records |
| /api/v1/performance/ | GET/POST | Performance data |
| /api/v1/analytics/ | GET | Analytics results |
| /api/v1/settings/ | GET/PATCH | Authorized configuration |
| /api/v1/telegram/webhook/ | POST | Telegram inbound updates |

Additional endpoints may be added during implementation.

## API Requirements

- Enforce role-based authorization.
- Validate all input.
- Support cursor or page-based pagination.
- Use consistent error responses.
- Protect state-changing endpoints against CSRF or token misuse as appropriate.
- Apply rate limits.
- Audit critical mutations.
- Verify Telegram webhook authenticity.
- Avoid exposing media storage keys or private credentials.
- Return explicit null/unavailable values for missing metrics.

---

# 14. Notifications and Alerts

## 14.1 Administrator Alerts

Notify administrators when:

- A candidate exceeds the configured score threshold.
- A promising trend accelerates.
- A previously promising candidate begins declining.
- A discovery source fails repeatedly.
- Candidate ingestion stops unexpectedly.
- A Telegram delivery fails.
- Media authorization expires.
- A family member has outstanding assignments.
- A performance report is overdue.

## 14.2 Family Alerts

Notify publishers when:

- A new opportunity is assigned.
- An accepted assignment approaches expiry.
- A posting link is missing.
- A performance update is due.
- An assignment is cancelled.

## 14.3 Notification Controls

Support:

- Immediate notifications.
- Digest notifications.
- Quiet hours.
- User-specific preferences.
- Daily message limits.
- Retry suppression.
- Administrator notification thresholds.

---

# 15. Functional Requirement Register

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Discover candidates without a fixed creator list | P0 |
| FR-002 | Support interchangeable authorized discovery providers | P0 |
| FR-003 | Dynamically discover relevant Ethiopian topics | P0 |
| FR-004 | Detect Ethiopian-language relevance | P0 |
| FR-005 | Preserve source and publication metadata | P0 |
| FR-006 | Collect repeat engagement snapshots where available | P0 |
| FR-007 | Calculate explainable viral scores | P0 |
| FR-008 | Display confidence and data completeness | P0 |
| FR-009 | Detect exact duplicates | P0 |
| FR-010 | Provide administrator review and approval | P0 |
| FR-011 | Store media rights information | P0 |
| FR-012 | Create and manage family publisher profiles | P0 |
| FR-013 | Link family members to Telegram | P0 |
| FR-014 | Send approved opportunities through Telegram | P0 |
| FR-015 | Allow publishers to accept, skip, or mark posted | P0 |
| FR-016 | Record manual published-post URLs | P0 |
| FR-017 | Provide manual performance entry | P0 |
| FR-018 | Display dashboard KPIs and reporting | P0 |
| FR-019 | Provide configurable score thresholds | P0 |
| FR-020 | Provide user access controls and audit logs | P0 |
| FR-021 | Cluster related sounds, hashtags, and videos | P1 |
| FR-022 | Calculate growth acceleration | P1 |
| FR-023 | Estimate saturation | P1 |
| FR-024 | Support authorized downloadable media | P1 |
| FR-025 | Provide member-specific recommendations | P1 |
| FR-026 | Support authorized metric-file imports | P1 |
| FR-027 | Provide score-versus-outcome analysis | P1 |
| FR-028 | Generate suggested captions and content angles | P1 |
| FR-029 | Recommend algorithm weight adjustments | P1 |
| FR-030 | Support advanced predictive learning | P2 |
| FR-031 | Support additional platforms | P2 |
| FR-032 | Support additional distribution teams | P2 |
| FR-033 | Provide advanced similarity and propagation analytics | P2 |

P0 = Essential initial product  
P1 = Important enhancement  
P2 = Advanced expansion

---

# 16. Non-Functional Requirements

## 16.1 Performance

Target performance under the initial expected workload:

- Dashboard summary: under 3 seconds for typical requests.
- Candidate list page: under 3 seconds under normal load.
- Interactive review actions: under 2 seconds excluding external services.
- Background processing must not block page requests.
- Large datasets must use server-side pagination.

Targets must be tested against an agreed representative dataset and infrastructure.

## 16.2 Reliability

- Background jobs must support retry.
- Jobs must tolerate duplicate execution.
- Failed Telegram deliveries must remain visible.
- Provider outages must not corrupt candidate data.
- The system must recover after application restarts.
- Critical jobs must have monitoring and alerting.

## 16.3 Security

- Enforce HTTPS in production.
- Use secure password hashing and session handling.
- Protect all API endpoints.
- Store credentials outside source code.
- Limit access by user role.
- Validate uploaded files.
- Prevent unsafe public access to private media.
- Use signed or time-limited media links.
- Audit permissions and sensitive operations.
- Provide regular backup and restore procedures.
- Support administrator removal of users and media access.

## 16.4 Privacy and Retention

- Collect only information required for operations.
- Protect family member Telegram identifiers.
- Restrict access to private performance and profile data.
- Document external provider data use.
- Provide configurable retention periods.
- Support correction and removal requests where applicable.
- Avoid collecting private or restricted social-media account data without authorization.

## 16.5 Internationalization

Support:

- English interface.
- Amharic text.
- Unicode hashtags and captions.
- Ethiopian-language metadata.
- Optional future Afaan Oromo and Tigrinya translations.
- Africa/Addis_Ababa time display.

## 16.6 Scalability

Initial sizing target:

- Four publishers.
- Thousands of candidate records.
- Repeated metric snapshots.
- Multiple discovery providers.

Architecture shall allow increased candidate volume and more publishers without redesigning the core data model.

---

# 17. Testing and Acceptance Criteria

## 17.1 Discovery Test

**Given:** A configured working source provider returns a new video from an unknown creator.

**When:** The discovery job runs.

**Then:**

- The video is ingested.
- Metadata is stored.
- Ethiopian relevance is evaluated.
- The video enters the candidate workflow.
- The creator need not exist on a predetermined account list.

## 17.2 Velocity Test

**Given:** A video has 2,000 views at 10:00 and 8,000 views at 11:00.

**When:** Velocity is calculated.

**Then:** Recent view velocity equals 6,000 views/hour.

A single observation shall not be represented as observed recent velocity.

## 17.3 Missing Data Test

**Given:** A provider returns video details but no share count.

**Then:**

- The share metric remains unavailable.
- The score uses a documented missing-data rule.
- Confidence reflects the reduced evidence.
- The application does not generate a fictional share count.

## 17.4 Duplicate Test

**Given:** The same video arrives from two providers.

**Then:** One canonical candidate is retained, with separate source-provenance records.

## 17.5 Telegram Assignment Test

**Given:** An approved, distribution-ready candidate and an eligible publisher.

**When:** The administrator selects Send.

**Then:**

- One assignment is created.
- One delivery job is queued.
- The bot attempts delivery.
- The delivery result is stored.
- A successful retry does not create duplicate assignments or unintended repeat messages.

## 17.6 Publishing Confirmation Test

**Given:** A member receives an assignment.

**When:** The member selects Posted and submits a valid publication URL.

**Then:**

- The published record is created.
- The assignment changes state.
- The administrator can see the publishing URL.
- Performance collection can begin.

## 17.7 Permission Test

A family publisher must not be able to view another publisher's private assignment records unless explicitly authorized.

## 17.8 Rights Test

A candidate with Link Only rights cannot be automatically delivered as a downloaded video file.

The system may deliver the permitted source link and trend information.

## 17.9 Recovery Test

If a worker restarts during processing, queued tasks must either resume safely or enter a recoverable failure state.

## 17.10 Reporting Test

Given sample publishing and performance records, dashboard KPIs must reconcile with the corresponding database records and status definitions.

---

# 18. Development and Delivery Phases

## Phase 0 — Discovery Feasibility and Architecture

**Purpose:** Validate the most important external dependency before building the entire system.

Deliverables:

- Provider capability comparison.
- Access and licensing assessment.
- Representative candidate dataset.
- Source freshness measurement.
- Ethiopian relevance coverage assessment.
- Metric availability assessment.
- Working ingestion proof of concept.
- Documented fallback when real-time data is unavailable.

**Exit criterion:** A usable authorized discovery method is demonstrated, or the product owner formally approves a limited-source MVP.

## Phase 1 — Core Django Platform

Develop:

- Django project structure.
- PostgreSQL models.
- User roles and login.
- Admin configuration.
- Video candidate registry.
- Manual URL import.
- Provider interfaces.
- Data ingestion jobs.
- Basic dashboard.
- Basic ranking algorithm.
- Exact duplicate detection.

**Exit criterion:** Developers can ingest, normalize, rank, and review candidates using representative provider data.

## Phase 2 — Autonomous Discovery and Intelligence

Develop:

- Scheduled provider ingestion.
- Dynamic topic signals.
- Ethiopian relevance detection.
- Engagement snapshots.
- Velocity calculations.
- Ranking explanations.
- Trend clustering.
- Candidate filtering.
- Review queue.

**Exit criterion:** The system can repeatedly discover and rank eligible candidates without manual creator selection, subject to the validated source capabilities.

## Phase 3 — Telegram and Family Operations

Develop:

- Telegram Bot.
- Secure family account linking.
- Approval-to-assignment workflow.
- Telegram notifications.
- Authorized media attachments.
- Link-only opportunity packages.
- Status buttons.
- Posting-link capture.
- Assignment logs.
- Retry and reminder processing.

**Exit criterion:** An administrator can approve a candidate, assign it to family members, and receive structured posting feedback.

## Phase 4 — Performance Dashboard

Develop:

- Published post records.
- Manual metrics input.
- Performance snapshots.
- Discovery-to-posting analytics.
- Family performance reports.
- Content-category comparisons.
- Historical analytics.
- Exportable reports.

**Exit criterion:** Administrators can trace performance from initial discovery to member publication and reported results.

## Phase 5 — Adaptive Intelligence

Develop:

- Ranking quality evaluation.
- Historical outcome comparisons.
- Category effectiveness analysis.
- Personalized recommendations.
- Suggested weight changes.
- Ranking-model versioning.
- Optional predictive modeling.

**Exit criterion:** The system can demonstrate and explain whether proposed ranking changes improve evaluation results on historical data.

## Phase 6 — Production Hardening

Complete:

- End-to-end testing.
- Security testing.
- Background job recovery testing.
- Provider failure testing.
- Backup/restore testing.
- Documentation.
- Deployment automation.
- Administrator training.
- Operational handover.

---

# 19. Success Metrics and Product KPIs

The following are initial evaluation targets, not guarantees.

| KPI | Initial Target |
|---|---|
| Automated candidate ingestion | Working without a creator whitelist |
| Duplicate prevention | At least 99% for exact canonical IDs |
| Telegram successful send rate | At least 98% excluding unavailable chats |
| Assignment traceability | 100% of sent opportunities |
| Approved content rights checks | 100% before media-file distribution |
| Dashboard data reconciliation | 100% against validated test records |
| Candidate provenance coverage | 100% |
| Missing-metric transparency | 100% |
| Manual publishing feedback | Supported for every assignment |
| Discovery freshness | Measured and reported by source |
| Ranking prediction quality | Established after sufficient outcome data exists |

Business metrics such as follower growth and content views shall be monitored but are not guaranteed by the software.

---

# 20. Key Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| No suitable live TikTok discovery source | Critical | Validate providers in Phase 0 |
| Source data delayed by hours or days | High | Display freshness; reduce confidence |
| Insufficient Ethiopian-specific coverage | High | Combine multiple authorized signals |
| Missing view/share/comment counters | High | Missing-data scoring and confidence |
| Incorrect local-language detection | Medium | Human review and configurable rules |
| Duplicate or misleading trends | Medium | Canonical IDs, similarity clustering |
| Copyright or music restrictions | High | Rights-aware distribution and link-only workflow |
| Telegram delivery failure | Medium | Retry and delivery logs |
| Family members fail to report posting | Medium | Reminders and pending queues |
| Inaccurate self-reported metrics | Medium | Verification labels and snapshot provenance |
| Learning from incomplete data | High | Data-quality gates and model versioning |
| Source provider changes | High | Modular adapters and monitoring |
| Sensitive content misclassification | Medium | Human approval and review flags |

---

# 21. Required Developer Deliverables

The software development team must provide:

1. Complete Django source code.
2. PostgreSQL schema and migrations.
3. Discovery provider integration modules.
4. Background task configuration.
5. Viral ranking engine.
6. Duplicate detection.
7. Review and moderation interface.
8. Media permission and storage management.
9. Telegram bot and webhook handlers.
10. Family assignment and publishing workflows.
11. Analytics dashboard.
12. Performance reporting engine.
13. Role-based access controls.
14. Automated tests.
15. Environment configuration documentation.
16. Installation and deployment instructions.
17. Database backup and restoration guide.
18. Administrator user guide.
19. Telegram publisher user guide.
20. API documentation.
21. Operational monitoring and troubleshooting documentation.
22. Provider feasibility and limitation report.

Deliverables must include working features and tested integration flows, not only visual interface mockups.

---

# 22. Final Product Acceptance Definition

The initial system shall be considered ready for operational use when the following end-to-end scenario works:

**Scenario:**

1. The trend finder runs automatically against an approved source.
2. A previously unknown Ethiopian-relevant candidate is discovered.
3. The candidate is stored without creating duplicates.
4. The engine collects available engagement information.
5. A transparent viral score is generated.
6. The candidate appears in the administrator's ranked dashboard.
7. The administrator reviews the candidate and verifies distribution eligibility.
8. The administrator approves and assigns it to one or more family members.
9. The Telegram bot sends an appropriate opportunity package.
10. A family member accepts the assignment.
11. The family member manually publishes suitable authorized content or creates an original response to the identified trend.
12. The family member submits the publication URL.
13. The system records the publication.
14. Performance data is entered or collected through a permitted integration.
15. The dashboard displays results linked to the original discovery candidate.
16. The intelligence module incorporates validated outcomes into its future evaluation process.

**Final Product Vision**

A continuously improving Ethiopian trend discovery platform that finds promising opportunities early, ranks them transparently, coordinates manual publishing through Telegram, and learns which signals consistently produce valuable engagement for its family publishing team.

The application must operate without a manually maintained TikTok creator list, without automated TikTok posting, and without relying on undocumented or unverified platform capabilities.

**End of PRD — Version 1.0**