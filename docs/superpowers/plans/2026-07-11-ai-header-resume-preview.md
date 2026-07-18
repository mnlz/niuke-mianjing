# AI Header And Resume Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Match the supplied AI navigation header while retaining the Logo, and let users preview the PDF they just parsed.

**Architecture:** Extend the existing shared `AnalysisHeader` and `UserSessionButton` instead of introducing another header. Keep the selected PDF only in browser memory as an object URL and render it in the existing Ant Design stack with a Modal and native iframe.

**Tech Stack:** React 18, TypeScript, Ant Design, browser `URL` API, CSS, Node assertion tests.

## Global Constraints

- Keep the OfferLens Logo and its homepage navigation.
- Do not add dependencies or upload the PDF to another service.
- Preserve login checks for reports and user-controlled upload verification.

---

### Task 1: Header regression contract

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/AnalysisHeader.tsx`
- Modify: `niuke-mianjing-frontend/src/components/UserSessionButton/index.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- Consumes: existing AI routes and `openReports()` login gate.
- Produces: four-link desktop navigation and a user pill with logout menu.

- [ ] Add assertions for `新建分析`, `报告示例`, the active navigation class, user avatar pill, and report CTA.
- [ ] Run `npm test` and confirm the assertions fail because the current header lacks the new structure.
- [ ] Implement the four navigation items, user pill dropdown, and reference-image styling.
- [ ] Run `npm test` and confirm all assertions pass.

### Task 2: Local PDF preview

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- Consumes: the `File` passed to `parseResume(file)`.
- Produces: `resumePreviewUrl`, a preview button, and an iframe Modal.

- [ ] Add assertions for `URL.createObjectURL`, `URL.revokeObjectURL`, `预览简历`, and the PDF iframe.
- [ ] Run `npm test` and confirm the assertions fail because no preview URL exists.
- [ ] Store and revoke the object URL, split the file-row actions, and render the Modal.
- [ ] Run `npm test`, `npm run build`, and `git diff --check`.

### Task 3: Browser verification

**Files:** None.

- [ ] Verify the Header contains Logo, four navigation items, user pill, and report CTA.
- [ ] Verify the resume file row exposes preview and re-upload controls without selecting a new file.
