# KabulCV

Multilingual resume builder for English, Dari and Pashto. The repository starts as a Docker-first Django/DRF and React/TypeScript modular monolith. PostgreSQL stores application records, Redis backs Celery, and generated/private files use a separate Docker volume.

## Local development

1. Copy `.env.example` to `.env` and change the local Django secret and database password.
2. Start all services with `docker compose up --build`.
3. Open the React app at `http://localhost:53000`, API health at `http://localhost:58000/api/v1/health/`, Django admin at `http://localhost:58000/admin/`, and OpenAPI docs at `http://localhost:58000/api/v1/docs/`.
4. Stop with `docker compose down`; keep the database between runs. To remove local data deliberately, use `docker compose down -v`.

The non-default host ports avoid common project collisions. Override `FRONTEND_PORT`, `BACKEND_PORT`, `POSTGRES_PORT`, and `REDIS_PORT` in `.env` when those ports are already occupied. Containers communicate on their private Compose network using `db:5432` and `redis:6379`; only host mappings change.

Services: `frontend`, `backend`, `db`, `redis`, `worker`, and Mailpit for local email capture at `http://localhost:58025`. PostgreSQL and Redis have health checks. Activation links appear in Mailpit instead of server logs; production SMTP credentials must be injected through deployment secrets. API startup applies migrations; private files live in the `private_media` volume. The Compose file is for local development; production must replace Django's development server, console email, debug settings and development secrets with production-grade configuration.

## Structure

```text
backend/
  config/                 Django settings, URLs, WSGI and Celery
  modules/
    accounts/             Custom UUID user and authentication boundary
    profiles/             Career profile boundary
    resumes/              CV content and ownership boundary
    exports/              Rendering and export jobs
    billing/              Plans, quota and payment lifecycle
    analytics/            Aggregate public metrics
    support/              Contact and support
frontend/src/             React application, shared UI and localization
compose.yaml              Local full-stack orchestration
```

## Product and API baseline (KCV-01-01)

- API base path is `/api/v1/`; JSON errors should use `{ "detail": "...", "code": "...", "fields": {} }`. List endpoints use page-number pagination `{ "count", "next", "previous", "results" }`.
- UI language (English/Dari/Pashto) is independent of the CV's output language. Do not translate user-authored CV content automatically. Use UTC-aware timestamps in persistence and render user-facing dates in `Asia/Kabul` unless a user-selected locale requires otherwise.
- Users own their profiles, CVs, photos, export jobs and files. Every object/file lookup must enforce owner scope. Public statistics are aggregate only.
- Free users may successfully export five distinct CVs per rolling 24 hours; active Premium users may export twenty. Charge on the first successful export for a CV identity. Drafts, previews, failed exports and re-exports are free; edits do not consume a new credit. A duplicate is a new CV identity. Deleting a CV does not refund a credit. Keep preview rendering distinct from downloadable/export jobs so it cannot bypass quota or export permissions.
- Premium is a configurable one-time 30-day purchase. Repeated provider events must be idempotent. Activate Premium only after server-verified provider evidence; never infer payment success from a browser redirect. Merchant, price, fees, provider and production payment readiness remain undecided and must be configured/approved before enabling checkout.
- Expiry preserves user CVs and existing artifacts but applies current entitlements to new exports. A proposed AFN price is configuration, not an approved price. Photo and Afghan-specific profile fields remain optional.
- Public routes: `/`, `/templates`, `/pricing`, `/contact`, `/privacy`, `/terms`, `/stats`. User routes: `/register`, `/login`, `/dashboard`, `/cvs`, `/cvs/:id/edit`, `/profile`, `/subscription`, `/settings`. Staff routes live under `/admin`; backend permissions, not route visibility, enforce staff access.
- Interface states include loading, empty, validation, unavailable, unauthorized, quota exhausted, and recoverable export failure. Never present illustrative UI values as live users, CVs, quotas, statistics or payments.

## Payments readiness

Premium checkout is disabled. No merchant, provider, approved AFN price, fees, sandbox credentials, settlement terms or refund policy have been provided. `/api/v1/billing/readiness/` returns safe public availability, price and term data without secrets. `PAYMENTS_ENABLED` and `PAYMENT_MERCHANT_APPROVED` default to false; the backend also keeps `PAYMENT_ADAPTER_READY` false until a documented provider adapter exists. Store real provider credentials in deployment secrets, never in frontend variables or committed `.env` files.

## Decisions still needed

- Confirm the public product name/domain, production host and supported email provider.
- Confirm approved AFN price, merchant/provider, fees, settlement terms and refund/dispute policy before payment work is enabled.
- Confirm phone-number requirements and formats, account-retention/deletion obligations, and privacy/analytics consent requirements.
- Confirm public support contact channels; no placeholder contact details are published.
- Confirm production object-storage provider, backup/retention policy, deployment platform and operational targets.

## Current implementation boundary

This foundation establishes the modules, custom user model, Docker development environment, API health/schema endpoints and a responsive multilingual public design shell. Authentication, profile, CV builder, private asynchronous PDF previews/exports, a server-enforced rolling quota ledger and the first versioned template catalog are implemented. Premium purchase remains disabled until an approved provider and price are configured; payment verification, staff operations and production deployment are pending. Module folders alone do not imply those features are implemented. `VITE_API_BASE_URL` is public configuration only and must never contain credentials.

### Prompt progress

- KCV-01-01 through KCV-01-06: foundation and shared shell recorded above.
- KCV-02-01: pending registration API and localized registration form implemented.
- KCV-02-02: 24-hour signed activation link, one-time activation/password setting, email task and activation form implemented.
- KCV-02-03: JWT access tokens held in memory, rotated HttpOnly refresh cookie, CSRF checks and a protected dashboard shell implemented.
- KCV-02-04: Generic activation resend, per-email cooldown, Redis-backed throttling and retryable email delivery implemented.
- KCV-02-05: One-hour password reset links, single-use confirmation and refresh-token revocation implemented.
- KCV-02-06: Account settings, verified email change, old-address notice and private account-data JSON download implemented.
- KCV-03-01: Owner-scoped career profile with optional Afghan details and per-field CV inclusion preferences implemented.
- KCV-03-02: Owner-scoped employment CRUD, date validation, plain-text duties, and persisted reordering implemented.
- KCV-03-03: Owner-scoped education/training records, date validation, manual institutions, owner-history suggestions, reorder and delete support implemented.
- KCV-03-04: Language records with self-described proficiency/CEFR validation and editable ordered skill groups implemented.
- Next prompt in order: KCV-03-05 projects, awards, publications and references.
- KCV-03-05: Typed owner-scoped projects, awards, publications and referee records; explicit referee-contact consent is validated, and profile inclusion flags control which optional sections can enter a CV. UI route: `/profile/optional`.
- KCV-03-06: Owner-scoped CV creation copies selected profile sections into a schema-versioned JSON snapshot. Existing snapshots retain their copied content after profile edits or record deletion. UI route: `/cvs/new`; API `POST /api/v1/resumes/from-profile/`.
- KCV-04-01: `CVDocument` now carries owner, CV type, draft/exported/archived lifecycle, output language, content schema version, template version and revision. Owner-scoped archive/restore actions and predictable initial revision are covered by focused tests.
- KCV-04-02: Owner-scoped paginated CV list supports title search, state filtering and ordering. `/cvs` shows real API results, an empty state, retry/loading states, and archive/restore actions; storage keys are never returned.
- KCV-04-03: `/cvs/new` creates either a blank CV draft or a CV from selected profile sections, with validated title, type and English/Dari/Pashto output language.
- KCV-04-04: CV cards now offer rename, duplicate, archive and restore. Duplicate creates a new owned draft with a new ID and revision 1, carrying content only; no export/quota state is copied. Rename changes the title without changing the snapshot.
- KCV-04-05: Owner-scoped CV deletion removes document content; cascading private artifact deletion queues an idempotent Celery cleanup task with retries. Minimal export-charge identity/time records have no CV foreign key and survive document deletion. `/cvs` requires explicit confirmation and removes a card only after a successful server response.
- KCV-04-06: Stable `/cvs/<uuid>/edit` routes reload owner-scoped document metadata and saved builder step; foreign/missing IDs resolve to a safe unavailable screen. Sidebar links connect dashboard, My CVs, career profile, templates and settings.
- KCV-05-01: Four-step partial-save API (`PATCH /api/v1/resumes/<id>/steps/<step>/`) validates completion, stores `builder_step`/`last_completed_step`, and increments revision. Builder Back/Next and draft-save controls retain independent content.
- KCV-05-02: Optional CV photo upload verifies JPEG/PNG/WebP content, byte and pixel dimensions, re-encodes to metadata-free JPEG, stores under private media, and exposes only authenticated owner-scoped photo access. Replaced/deleted photo files use retryable cleanup. The builder personal step includes replace/remove and preview controls.
- KCV-05-03: Experience wizard step saves ordered plain-text entries, validates dates/current-role rules and length limits, and the builder offers add/remove/reorder cards with current-employment controls.
- KCV-05-04: Step three supports typed education/training snapshots with manual institutions and date/current-study validation. Step four validates languages/proficiency, skill groups, selected optional scholarship content and reference consent; only selected sections can be saved.
- KCV-05-05: Builder writes use per-document revisions, idempotency keys, serialized autosaves, stale-write conflicts, conflict review/merge, retry and unsaved-navigation protection. CV list mutations now send the current revision.
- KCV-05-06: The builder exposes a server readiness report for required fields and blocks export until the CV is complete.
- KCV-06-01: Added a versioned template contract and free Public Service template metadata with English, Dari and Pashto section labels.
- KCV-06-02: Export requests store an immutable copy of the CV snapshot, selected sections, language and template version before queueing.
- KCV-06-03: A Celery worker renders private PDF artifacts with pinned Playwright Chromium and Noto fonts; owner-scoped status routes, cleanup and builder feedback are connected.
- KCV-06-04: Preview and export artifacts use private storage, owner-authorized streaming and cache-control protections; deleting a CV removes its artifact.
- KCV-06-05: Preview and download use the same immutable template snapshot and renderer; identical revision previews are reused and the builder marks old previews stale.
- KCV-06-06: Render retries are bounded, permanent input failures are reported, completed jobs are reused, worker capacity is limited, and the UI can recover a saved job.
- KCV-07-01 through KCV-07-06: Plans and verified subscriptions resolve server-side; UTC rolling usage, reservation/settlement/release, identity-based re-export, template/format rights, free watermark and separate render throttles are implemented. Premium checkout is still disabled.
- KCV-08-01: Public Service, Professional and ATS-oriented versioned templates are catalogued through an API. Premium templates are exposed as locked choices until the user has a verified Premium entitlement; existing job snapshots retain their template key and version.
- KCV-08-02: A print-friendly Professional PDF layout and same-renderer preview are implemented for verified Premium access.
- KCV-08-03: An ATS-oriented single-column, text-first PDF layout omits profile photos. The product description does not promise compatibility with every applicant tracking system.
- KCV-08-04: Premium DOCX exports use editable Word paragraphs and an RTL-aware sidebar table; embedded photos are optimized, snapshotted with the job, and positioned in regular templates. Word pagination can differ from the PDF preview.
- KCV-08-05: CVs persist validated theme, font and layout choices. Blue/teal, green and maroon print palettes, sans/serif fonts and supported classic/sidebar/single-column layouts map to the PDF and DOCX renderers. Website dark mode is independent.
- KCV-08-06: Export regression checks cover all three templates and languages for long PDF fixtures and short DOCX fixtures, Free-versus-Premium template/format enforcement, editable text, RTL direction, design validation and optional-photo behavior. Reopening a builder retains its format choice.
- KCV-09-01: Added a public, fail-closed payment readiness endpoint and plan pricing data. Premium price remains null and purchase is disabled; no provider or merchant approval is invented. `PAYMENT_ADAPTER_READY` remains false in code until a provider integration is implemented.
- KCV-09-02 through KCV-09-06 remain gated: hosted checkout, webhook verification, refunds, subscription UI and provider end-to-end journeys require an approved merchant/provider, official sandbox requirements, production credentials and policy decisions. Do not enable purchases before those are supplied.


## Public pages and analytics

- KCV-10-01: The homepage uses live public template/plan APIs, and its registration, templates and pricing actions lead to working routes. Public navigation links now include FAQ, contact, statistics, privacy and terms.
- KCV-10-02: `/pricing`, `/faq`, `/privacy` and `/terms` render safe public plan/content data. FAQ content is published; privacy and terms remain explicitly labeled drafts until operational and legal details are confirmed. Content is editable in Django admin and versioned.
- KCV-10-03: `/stats` reports real activated-account, first-export and public-view aggregates, including today counts by Asia/Kabul day; counts are cached without returning identities.
- KCV-10-04: Optional page-view events require affirmative local analytics consent, are bot-filtered and rate-limited, contain only an allowlisted public path, store daily aggregates without visitor identifiers, and prune rows older than 90 days. Views are not described as unique people.
- KCV-10-05: `/contact` stores validated, rate-limited submissions, rejects obvious honeypot spam, and queues notification to a configured `SUPPORT_EMAIL`. Delivery remains visibly unavailable until support is configured; only real configured contact channels are shown.
- KCV-10-06: Safe public API responses have short cache headers; other API responses are `private, no-store`, including contact submissions. Public routes include responsive layouts, semantic sections, focus-visible keyboard outlines and page metadata.

Deployment owners still need to configure a genuine support address/channels and review/publish the legal drafts. Contact records remain in the database until a retention/deletion policy is selected.
