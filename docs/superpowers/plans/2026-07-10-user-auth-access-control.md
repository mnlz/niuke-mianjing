# OfferLens User Auth and Access Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add email/password user accounts, two-page anonymous browsing, account-scoped review progress, and server-backed AI reports.

**Architecture:** Keep the existing administrator authentication unchanged and add a separate signed user token in `X-User-Token`. Extend the existing `app_users` table for credentials, reuse its primary key for review ownership, and add one repository for AI reports. Frontend authentication remains localStorage-based and uses small shared guards instead of a new state-management layer.

**Tech Stack:** FastAPI, Pydantic v2, aiomysql, Python stdlib `hashlib`/`hmac`/`secrets`, React 18, TypeScript, React Router, Ant Design, Axios.

## Global Constraints

- User emails are trimmed and lowercased; passwords require at least 8 characters.
- User tokens last 30 days and cannot validate as administrator tokens.
- Anonymous users can request only list pages 1 and 2.
- Review progress and AI reports are account-scoped; no anonymous-data migration.
- Do not add dependencies.

---

### Task 1: User password and token primitives

**Files:**
- Modify: `niuke_mianjing_backend/api/security.py`
- Create: `tests/test_user_security.py`

**Interfaces:**
- Produces: `normalize_email(value) -> str`, `hash_password(password) -> str`, `verify_password(password, encoded) -> bool`, `create_user_token(user_id, days=30) -> str`, `decode_user_token(token) -> Optional[int]`.

- [ ] Write failing tests for email normalization, PBKDF2 round-trip, wrong password, valid user token, expired/malformed token, and rejection by `is_valid_admin_token`.
- [ ] Run `.venv/bin/python -m pytest -q tests/test_user_security.py` and confirm the helpers are missing.
- [ ] Implement PBKDF2-HMAC-SHA256 with `secrets.token_bytes(16)`, 260,000 iterations, and a derived signing key `HMAC(API_KEY, "offerlens-user-auth")`.
- [ ] Run the focused test and the full Python suite.
- [ ] Commit only Task 1 files with `feat: add user auth security primitives`.

### Task 2: Account registration and login API

**Files:**
- Modify: `niuke_mianjing_backend/repositories/review_repo.py`
- Create: `niuke_mianjing_backend/api/routes/user_auth.py`
- Modify: `niuke_mianjing_backend/api/app.py`
- Modify: `niuke_mianjing_backend/api/middleware/auth.py`
- Create: `tests/test_user_auth.py`

**Interfaces:**
- Consumes: Task 1 password and token helpers.
- Produces: `POST /api/user-auth/register`, `POST /api/user-auth/login`, `GET /api/user-auth/me`, `require_user_id(...) -> int`, `optional_user_id(...) -> Optional[int]`.

- [ ] Write failing tests for normalized registration, duplicate email conflict, generic invalid-credentials response, and current-user lookup.
- [ ] Run `.venv/bin/python -m pytest -q tests/test_user_auth.py` and confirm route/repository behavior is missing.
- [ ] Extend `app_users` idempotently with nullable `email` and `password_hash` columns plus a unique email index; add `create_account`, `get_account_by_email`, and `get_account_by_id`.
- [ ] Implement the three user-auth routes and token dependencies; return `{id, email, token}` after register/login and `{id, email}` from `me`.
- [ ] Add the new router and public middleware paths; keep administrator checks unchanged for all administrator routes.
- [ ] Run focused and full backend tests.
- [ ] Commit Task 2 files with `feat: add email user accounts`.

### Task 3: Anonymous pagination and account-scoped review progress

**Files:**
- Modify: `niuke_mianjing_backend/api/routes/logs.py`
- Modify: `niuke_mianjing_backend/api/routes/recruitment.py`
- Modify: `niuke_mianjing_backend/api/routes/review.py`
- Modify: `niuke_mianjing_backend/services/review_service.py`
- Create: `tests/test_user_access.py`

**Interfaces:**
- Consumes: `optional_user_id` and `require_user_id` from Task 2.
- Produces: list endpoints that return `401` after page 2 for anonymous callers; review progress methods accepting `user_id` directly.

- [ ] Write failing tests for `offset=24`, recruitment `page=3`, authenticated access, and unauthenticated progress updates.
- [ ] Run the focused tests and confirm the anonymous limits are not enforced.
- [ ] Add optional token dependencies to both list routes and reject only anonymous requests beyond page 2.
- [ ] Require a user token for review progress reads/writes and call repository methods with the authenticated `app_users.id`; keep overview public.
- [ ] Run focused and full backend tests.
- [ ] Commit Task 3 files with `feat: enforce public browsing limits`.

### Task 4: Persist AI reports by account

**Files:**
- Create: `niuke_mianjing_backend/repositories/ai_report_repo.py`
- Modify: `niuke_mianjing_backend/api/routes/recruitment.py`
- Modify: `niuke_mianjing_backend/api/app.py`
- Modify: `niuke_mianjing_backend/api/middleware/auth.py`
- Create: `tests/test_ai_report_accounts.py`

**Interfaces:**
- Consumes: `require_user_id` from Task 2.
- Produces: `save`, `list_by_user`, `get_by_code`, `delete_by_code`; authenticated report generation/list/detail/delete endpoints.

- [ ] Write failing tests showing generated reports are saved with the current user and another user receives `404`.
- [ ] Run the focused tests and confirm persistence/endpoints are absent.
- [ ] Create `ai_analysis_reports` idempotently and implement the four repository operations, always including `user_id` in reads and deletes.
- [ ] Require a user token on AI generation and resume parsing; save generated Markdown before returning it.
- [ ] Add list/detail/delete endpoints and initialize the table during application startup.
- [ ] Run focused and full backend tests.
- [ ] Commit Task 4 files with `feat: persist account ai reports`.

### Task 5: Frontend user session and login screen

**Files:**
- Modify: `niuke-mianjing-frontend/src/utils/auth.ts`
- Modify: `niuke-mianjing-frontend/src/api/client.ts`
- Modify: `niuke-mianjing-frontend/src/api/auth.ts`
- Modify: `niuke-mianjing-frontend/src/api/types.ts`
- Create: `niuke-mianjing-frontend/src/pages/UserLogin/index.tsx`
- Create: `niuke-mianjing-frontend/src/pages/UserLogin/style.css`
- Create: `niuke-mianjing-frontend/src/components/UserSessionButton/index.tsx`
- Modify: `niuke-mianjing-frontend/src/App.tsx`
- Create: `niuke-mianjing-frontend/scripts/userAuth.test.mjs`
- Modify: `niuke-mianjing-frontend/package.json`

**Interfaces:**
- Produces: `getUserToken`, `setUserSession`, `clearUserSession`, `requireUserLogin(navigate, from)`, `authApi.userRegister/userLogin/userMe` and `/login`.

- [ ] Write failing Node assertions for session serialization and `isAnonymousPageAllowed(page)`.
- [ ] Run `node scripts/userAuth.test.mjs` and confirm the helpers are missing.
- [ ] Add user session storage and attach `X-User-Token` in the existing Axios interceptor.
- [ ] Implement one login/register page with email and password validation and return-to navigation.
- [ ] Add the route and a small shared navigation button showing login/email/logout.
- [ ] Run the focused test, `npm test`, and `npm run build`.
- [ ] Commit Task 5 files with `feat: add public user login`.

### Task 6: Frontend gates, public sample report, and server report center

**Files:**
- Modify: `niuke-mianjing-frontend/src/pages/PublicInterviews/index.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/PublicJobs/index.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/index.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/ReportsPage.tsx`
- Create: `niuke-mianjing-frontend/src/pages/AIAnalysis/SampleReportPage.tsx`
- Modify: `niuke-mianjing-frontend/src/api/recruitment.ts`
- Modify: `niuke-mianjing-frontend/src/App.tsx`
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

**Interfaces:**
- Consumes: Task 5 session helpers and Task 4 report API.
- Produces: public `/ai-analysis/sample-report`, authenticated `/ai-analysis/reports`, login-gated actions and page 3 transitions.

- [ ] Add failing assertions for the sample-report route target and server report record mapping.
- [ ] Run the focused frontend tests and confirm failures.
- [ ] Gate page 3 transitions, favorites, mastery, notes, PDF parsing, AI generation, and report-center entry with the shared login helper.
- [ ] Point “查看报告示例” to the public sample page and render the fixed sample report there.
- [ ] Replace report-center localStorage calls with list/detail/delete API calls; redirect anonymous users to login.
- [ ] Add session buttons to public page headers without restructuring unrelated layout code.
- [ ] Run `npm test` and `npm run build`.
- [ ] Commit Task 6 files with `feat: gate user features by login`.

### Task 7: End-to-end verification

**Files:**
- No production files unless verification finds a defect; any defect begins with a failing regression test.

- [ ] Run `.venv/bin/python -m pytest -q` and confirm zero failures.
- [ ] Run `.venv/bin/python -m compileall -q niuke_mianjing_backend main.py`.
- [ ] Run `npm test && npm run build` in `niuke-mianjing-frontend`.
- [ ] Run `git diff --check`.
- [ ] In the in-app browser, verify anonymous pages 1–2, page 3 login redirect, registration, login, favorite persistence, public sample report, AI generation login gate, server report center, and logout.
- [ ] Leave the browser on `/login` or the authenticated report center according to final state.
