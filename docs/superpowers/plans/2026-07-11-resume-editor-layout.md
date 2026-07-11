# Resume Editor Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge resume section previews and full editable text into one compact editor.

**Architecture:** Reuse the existing parsed resume state and textarea. Replace duplicate section cards with compact section labels inside the editor header, and adjust only local CSS.

**Tech Stack:** React 18, TypeScript, CSS, Node assert tests

## Global Constraints

- No new dependencies or components.
- Preserve resume confirmation behavior and metadata.
- Keep responsive wrapping for section labels.

---

### Task 1: Merge the resume content presentation

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- Consumes: existing `parsedResume.sections` and `resume` state
- Produces: one `.ai-resume-editor-panel` containing section labels and editable text

- [ ] **Step 1: Write the failing source-contract assertions**

Assert that `CreatePage.tsx` contains `简历内容（可编辑）` and `ai-resume-section-tags`, and no longer contains `上传时识别结果`.

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `cd niuke-mianjing-frontend && npm test`

Expected: FAIL because the merged editor markup does not exist yet.

- [ ] **Step 3: Implement the minimal merged editor**

Render compact section labels in the editor header, keep the existing textarea and confirmation controls, and remove the section summary cards.

- [ ] **Step 4: Add local responsive styles**

Style the editor panel, header and wrapping tags using the existing AI page variables.

- [ ] **Step 5: Verify tests and build**

Run: `cd niuke-mianjing-frontend && npm test && npm run build`

Expected: all tests pass and the Vite build completes.
