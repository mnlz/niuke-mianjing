# AI Analysis HTML-to-React Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the four user-edited HTML designs into the existing AI analysis React routes without replacing real application behavior.

**Architecture:** Keep the current React components, API calls, authentication, report generation, and account-scoped report storage. Update component markup and the shared AI analysis stylesheet to match the supplied designs, while keeping the existing home hero report preview component byte-for-byte unchanged.

**Tech Stack:** React 18, TypeScript, React Router, Ant Design, existing CSS and Node assertion scripts.

## Global Constraints

- Do not modify the JSX inside `.ai-report-sample`, including `.sample-body`.
- Preserve current login, API, resume parsing, report generation, deletion, and download behavior.
- Do not add dependencies or backend changes.
- Do not inject static report or recruitment data into real API-backed screens.

---

### Task 1: Visual migration contract

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

**Interfaces:**
- Consumes the four AI analysis TSX source files.
- Produces assertions for supplied-design markers and the protected home preview content.

- [ ] Add source assertions for `AI · v2`, `RPT-SAMPLE-0711`, `REPORT WORKSPACE`, `FULL SCAN`, and the protected preview strings `83`, `招聘信号`, and `面试重点`.
- [ ] Run `node --experimental-strip-types scripts/aiAnalysis.test.mjs`; expect failure on the new design markers.

### Task 2: Shared header and home

**Files:**
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/AnalysisHeader.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/index.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- `AnalysisHeader` continues to consume `active: 'home' | 'create' | 'reports'`.
- Home continues to read `logApi.stats()` and `recruitmentApi.sources()` and route report cards through `start(reportType)`.

- [ ] Add the static design's version tag, compact user area, trend labels, radar metadata, report mode indices/tags, and CTA structure.
- [ ] Preserve the `.ai-report-sample` JSX without edits.
- [ ] Add matching shared and home CSS with existing responsive breakpoints.
- [ ] Run the AI analysis test and `npm run build`.

### Task 3: Six-step create page

**Files:**
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- Retains current state, API calls, `validate()`, `parseResume()`, and `generate()`.
- Adds keyboard navigation that ignores `INPUT`, `TEXTAREA`, `SELECT`, and contenteditable targets.

- [ ] Add step subtitles, choice metadata, company counts from available API data only, relevance labels, save status, keyboard hint, richer summary badges, and preview syncing state.
- [ ] Add guarded ArrowLeft, ArrowRight, and Enter navigation.
- [ ] Update CSS to match the supplied create design.
- [ ] Run AI analysis tests and the TypeScript build.

### Task 4: Full sample report

**Files:**
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/SampleReportPage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- Fixed public sample; no API calls.
- Copy uses `navigator.clipboard`; print uses `window.print`; CTA routes to create.

- [ ] Replace the short Markdown sample with React sections matching the supplied cover, metrics, capability matrix, evidence table, resume rewrite, interview prep, and action plan.
- [ ] Implement copy feedback through existing Ant Design `message`.
- [ ] Add sample report CSS and print rules.
- [ ] Run tests and build.

### Task 5: Account report workspace

**Files:**
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/ReportsPage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- Continues to consume `recruitmentApi.aiReports()` and account auth.
- Keeps `filterReports`, drawer viewing, Markdown download, and API deletion.

- [ ] Add supplied-design title metadata, account-backed KPIs, sidebar counts, sort control, richer rows, and drawer report header.
- [ ] Keep the real empty state when `reports.length === 0`.
- [ ] Update report workspace CSS.
- [ ] Run tests and build.

### Task 6: Verification

- [ ] Run `npm test`, `npm run build`, and `git diff --check`.
- [ ] Verify all four routes in the in-app browser, including login-dependent states and the protected home preview.
- [ ] Verify 390 px layouts have no horizontal overflow and inspect console errors.
