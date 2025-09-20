# CLAUDE.md

# Fake-News Detector — Project Overview

## 1) Summary

An easy-to-use Chrome extension that lets users flag suspicious posts anywhere on the web and submit a **pixel-perfect capture plus structured context** (URL, page title, selection text, etc.) to a backend. A fact-checking pipeline (retrieval + LLM adjudication) evaluates the central claim and returns a verdict with citations.

---

## 2) Purpose & Motivation

* **Problem:** False or misleading claims spread rapidly across social platforms and comment sections. Even when users are skeptical, verifying takes time and skill.
* **Our aim:** Make **one-click, source-grounded fact checks** accessible directly from the page the user is viewing—no copy/paste gymnastics.
* **Principles:**

  * Evidence over opinions (always cite sources).
  * User consent & privacy by design.
  * Low friction, high clarity.

---

## 3) What We Want to Achieve (Goals)

* **G1 – Fast capture:** One click to open an overlay, optionally select a region, and submit.
* **G2 – Hybrid context:** Combine **screenshot** (what was seen) + **structured data** (URL, title, selection text, timestamps) for robust fact extraction.
* **G3 – Grounded verdicts:** Return **True / False / Misleading / Unverifiable**, with 3–5 high-quality citations and a short rationale.
* **G4 – Trust & transparency:** Clear disclosures, user-controlled redaction, and explicit consent each time.
* **G5 – Low latency:** Aim for P50 < 5s (text-only mode), < 12s when image OCR is needed.
* **G6 – Learn & improve:** Feedback loop (“disagree / report”), error analytics, and iterative model updates.

---

## 4) Core User Scenarios (Happy Paths)

1. **Quick Check (text-first):**
   User highlights a suspicious sentence → clicks the extension → submits selection text + URL (no screenshot) → verdict + sources in seconds.
2. **Visual Post (image-first):**
   User clicks the extension → lasso a post region → redacts usernames → submit screenshot + context → verdict with citations.
3. **Link-only:**
   User triggers the extension with no selection → we capture URL + metadata → backend runs source-aware check → verdict.

---

## 5) Non-Goals (V1)

* Detecting deepfakes in video/audio.
* Moderation or takedown tooling.
* Browser automation or interaction with walled-off native apps.

---

## 6) Success Metrics (KPIs)

* **Adoption:** Weekly Active Users (WAU), new installs, capture attempts/session.
* **Quality:** User “helpfulness” rating ≥ 4/5; disagreement rate < 10%.
* **Latency:** P50 decision times (text-only vs image-OCR).
* **Coverage:** % of requests that return at least 3 independent sources.

---

## 7) Privacy, Consent & Compliance

* **In-product consent:** Show a clear notice before any capture; user must confirm.
* **Redaction tools:** Blur/blackout names, avatars, and personal info before upload.
* **Data minimization:** Prefer text-only when possible; screenshots optional.
* **Storage policy:** Retain minimal artifacts; configurable retention window.
* **User controls:** Opt-out domains, “never capture on this site”, delete my data request.
* **Documentation:** Privacy Policy + Data Use disclosure aligned with Chrome Web Store rules.

---

## 8) Tech Stack (Proposed)

### Frontend (Chrome Extension, Manifest V3)

* **UI:** Lightweight overlay modal (HTML/CSS), accessible controls, keyboard shortcuts.
* **APIs:** Tabs capture (screenshot), messaging, storage (for local prefs).
* **Internationalization:** English + Portuguese initially.

### Backend

* **API Layer:** HTTPS REST endpoints (JSON + multipart/form-data).
* **Processing:**

  * **Claim extraction:** Heuristics + NLP to isolate central statement.
  * **Retrieval:** Web/news search with quality filters & deduplication.
  * **Adjudication:** LLM with structured prompt; verdicts grounded in retrieved evidence.
* **Datastores:**

  * Object storage (screenshots),
  * Relational DB (requests, verdicts, citations),
  * Cache (claims seen before, recent evidence).
* **Observability:** Centralized logs, metrics, tracing; redaction for PII.

### ML/AI

* **OCR:** On demand (image-only cases).
* **NER & claim parsing:** Light NLP models, language detection.
* **LLM:** Provider-agnostic adapter for verdict + rationale generation.

---

## 9) High-Level Architecture (Overview)

**Browser (User)**
→ **Chrome Extension (MV3)**
→ *(POST)* **Backend API** `/submit` (image + context)
→ **Preprocess & Claim Builder** (text merge, OCR if needed, entity/date normalization)
→ **Retrieval Service** (search, filter, dedupe, timestamp normalization)
→ **LLM Adjudicator** (verdict + citations)
→ **Response Builder** (JSON payload)
→ *(200 OK)* **Extension Modal** (verdict badge, citations, share/report)

**Supporting Services:**

* AuthN for admin/ops dashboard,
* Metrics/alerts,
* Storage & retention jobs.

---

## 10) Extension Permissions (Minimum for V1)

| Permission  | Why we need it                                                                    |
| ----------- | --------------------------------------------------------------------------------- |
| `activeTab` | Allows capture after a user gesture; temporary access to the active page context. |
| `scripting` | Inject overlay UI into the current page and read selection text/metadata.         |
| `storage`   | Save local preferences (opt-out sites, UI settings).                              |

> Note: Screenshot/recording features require capture APIs invoked by user action. Sensitive pages and some iframes may be excluded by the browser.

---

## 11) Data We Send to the Backend (Typical Payload)

* **Required:** `url`, `pageTitle`, `timestamp`, `userLocale`
* **Optional Structured:** `selectionText`, `og:title`, `og:site_name`, viewport size, scroll offset, nearby timestamps/handles (when chosen)
* **Optional Binary:** PNG screenshot (cropped/redacted)
* **Client Hints:** extension version, feature flags
* **Privacy Flags:** redactions applied, incognito mode indicator (no identifiers stored)

---

## 12) API Sketch (REST, subject to change)

### `POST /submit` (multipart)

* **Parts:**

  * `image` (optional PNG),
  * `context` (JSON with fields above)
* **Response:**

  * `id`, `verdict` (true/false/misleading/unverifiable),
  * `confidence` (0–1),
  * `citations` (array of {title, source, url, snippet}),
  * `rationale` (short),
  * `processing_ms`

### `GET /result/{id}`

* Polling/fetch by ID; useful if we add async flows later.

### `POST /feedback`

* User agreement/disagreement, free-text notes; stored for quality monitoring.

---

## 13) UX Overview (No Code)

1. **Trigger:** User clicks the extension button (or uses a keyboard shortcut).
2. **Consent:** Inline notice explains what will be sent; user confirms.
3. **Capture:**

   * Default: send **selection text + metadata**.
   * Optional: **lasso** region → redact → attach screenshot.
4. **Processing:** Show spinner + “we’ll cite sources” message.
5. **Result:** Display verdict badge, short rationale, citations, and a link to “How we decided”.
6. **Follow-ups:** “Check another claim”, “Share result”, “Disagree / send feedback”.

---

## 14) Performance & Reliability

* **Fast path:** Skip OCR when selection text is available.
* **Caching:** Hash by (normalized claim + domain) to reuse recent adjudications.
* **Timeouts:** Hard timeouts for retrieval and LLM; degrade gracefully to “Unverifiable” with explanation.
* **Resilience:** Circuit-breaker on external search; fallback to cached sources.

---

## 15) Security Considerations

* **Transport:** HTTPS only; HSTS enabled.
* **Input handling:** Strict size limits on images; antivirus/malware scanning for uploads.
* **Abuse prevention:** Rate limits per device/session, anomaly detection.
* **Data segregation:** Separate storage buckets for temporary vs retained artifacts, lifecycle policies.
* **PII risk:** Encourage redaction; never log raw screenshots; masked analytics.

---

## 16) Accessibility & Internationalization

* **A11y:** Focus order, ARIA roles, keyboard navigation for the overlay, text contrast compliance.
* **i18n:** Externalized strings; initial locales EN/PT-BR; right-to-left support planned.

---

## 17) Testing Strategy

* **Unit:** Claim parsing, retrieval ranking, citation formatting.
* **Integration:** End-to-end submissions (with and without OCR).
* **Cross-site manual checks:** Major social platforms, news sites, blogs.
* **Compliance tests:** Consent flows, redaction tools, domain opt-out.
* **Load tests:** Spikes around breaking news events.

---

## 18) Analytics & Telemetry (Privacy-Aware)

* **Event counts:** Captures initiated/completed, modes used (text vs image).
* **Quality signals:** User ratings, disagreement rate, time-to-first-verdict.
* **Error budgets:** OCR failures, retrieval misses, LLM timeouts.
* **Opt-in only:** No per-user tracking; sampling for metrics; hashed IDs if needed.

---

## 19) Roadmap (Milestones)

* **M1 – Prototype:** Manual retrieval + lightweight adjudication; EN only; local dev.
* **M2 – Hybrid capture:** Selection + optional screenshot with redaction; basic citations.
* **M3 – Quality pass:** Better claim extraction; date normalization; caching; PT-BR.
* **M4 – Store readiness:** Privacy policy, consent UX, minimal permissions, listing assets.
* **M5 – Feedback loop:** “Disagree/report”, reviewer dashboard, continuous eval.
* **M6 – Scale & polish:** Performance tuning, accessibility audit, more locales.

---

## 20) Acceptance Criteria (V1)

* One-click capture opens overlay and allows **text-only** submit in < 2s.
* Optional screenshot + redaction path works on top 10 target sites.
* Verdict screen shows **badge, short rationale, ≥3 citations**.
* Clear consent & privacy notice before submission.
* Extension runs with only `activeTab`, `scripting`, `storage` permissions.
* Average end-to-end latency (text-first) P50 ≤ 5s.

---

## 21) Operations & Support

* **Runbooks:** Incident response (retrieval provider down, LLM quota exceeded).
* **Monitoring:** Uptime, error rates, queue depths, latency SLOs.
* **Updates:** Semantic versioning; staged rollouts; changelog.
* **User support:** In-modal “Report an issue” linking to a form or issue tracker.

---

## 22) Open Questions (to finalize)

* Minimum set of trusted source domains vs open web search?
* Screenshot retention defaults (e.g., 7 days) and user-visible controls.
* Offline mode behavior (queue requests, warn user, or block?).
* Enterprise/education deployment needs (domain-restricted publishing).

---

### Appendix: Glossary

* **Claim extraction:** Turning noisy text (and OCR) into one central statement to verify.
* **Grounded reasoning:** Explanations tied to verifiable citations, not model guesses.
* **Lasso/redaction:** UI tools for selecting/censoring parts of the screenshot prior to upload.

---