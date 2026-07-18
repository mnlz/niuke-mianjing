# AI Analysis Static Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build four standalone, linked static HTML prototypes covering the complete OfferLens AI analysis flow.

**Architecture:** Each page is a self-contained HTML document with embedded CSS and page-specific vanilla JavaScript. Pages share the same visual tokens and link directly by filename, but make no API requests and require no build step.

**Tech Stack:** HTML5, CSS, inline SVG, browser-native JavaScript.

## Global Constraints

- Create the four files under `niuke-mianjing-frontend/public/` with the exact names in the approved spec.
- Keep CSS and JavaScript embedded in each HTML; add no npm dependency.
- Use static fake data only; do not call the backend.
- Preserve accessible buttons, labels, headings, and responsive layout.

---

### Task 1: Static-page contract test

**Files:**
- Create: `niuke-mianjing-frontend/scripts/staticAiPages.test.mjs`
- Modify: `niuke-mianjing-frontend/package.json`

**Interfaces:**
- Consumes: the four approved output filenames.
- Produces: a Node assertion script that validates page structure and cross-page links.

- [ ] Write a test that reads every file and asserts `<!doctype html>`, embedded `<style>` and `<script>`, the four static links, and page-specific text.
- [ ] Run `node scripts/staticAiPages.test.mjs`; expect failure because the files do not exist.
- [ ] Add the script to the existing `npm test` chain after `userAuth.test.mjs`.

### Task 2: Home and report sample

**Files:**
- Create: `niuke-mianjing-frontend/public/ai-analysis-static-home.html`
- Create: `niuke-mianjing-frontend/public/ai-analysis-static-sample-report.html`

**Interfaces:**
- Home links to create, sample report, and report center.
- Sample report links back to home and create.

- [ ] Create the home page with hero, live figures, inline SVG radar, feedback, six report modes, process, and CTA.
- [ ] Create the sample report with score, radar, evidence, resume advice, interview questions, and action plan.
- [ ] Run `node scripts/staticAiPages.test.mjs`; expect remaining failures only for create and reports pages.

### Task 3: Six-step report configuration

**Files:**
- Create: `niuke-mianjing-frontend/public/ai-analysis-static-create.html`

**Interfaces:**
- Uses `data-step` panels and native button/input events.
- Produces local resume fields `{ email, phone, length, confirmed }` and redirects to the static reports page after valid confirmation.

- [ ] Create six clickable steps with static report types, company cards, job settings, interview checkboxes, resume editor, and final summary.
- [ ] Implement local email/phone extraction, confirmation, edit-reset, and final validation using browser-native regular expressions.
- [ ] Run the static-page test; expect only the reports page to remain missing.

### Task 4: Interactive report center

**Files:**
- Create: `niuke-mianjing-frontend/public/ai-analysis-static-reports.html`

**Interfaces:**
- Consumes three in-page report records.
- Search and type filters render the visible records; view opens a dialog; delete removes one record in memory; download creates a Markdown blob.

- [ ] Create KPI cards, sidebar filters, search, report rows, empty state, and a native dialog containing a complete report preview.
- [ ] Implement filter, view, delete, and Markdown download handlers.
- [ ] Run `node scripts/staticAiPages.test.mjs`; expect pass.

### Task 5: Verification

- [ ] Run `npm test` and `npm run build` from `niuke-mianjing-frontend`.
- [ ] Open each static file through `http://127.0.0.1:3000/` and verify navigation, six-step configuration, resume confirmation, report filters, dialog, and console errors.
- [ ] Verify a narrow viewport does not create horizontal overflow.
