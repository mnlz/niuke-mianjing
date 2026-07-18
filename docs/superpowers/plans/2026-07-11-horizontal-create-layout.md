# Horizontal Create Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the AI analysis creation flow to a horizontal stepper and full-width resume review layout matching the supplied reference.

**Architecture:** Keep existing React state and API calls. Recompose `CreatePage` around a horizontal stepper and a single full-width panel, then let `ResumeEditor` present one selected parsed section at a time.

**Tech Stack:** React 18, TypeScript, Ant Design, CSS, Node assert tests

## Global Constraints

- Do not change backend APIs or resume parsing data.
- Remove the live preview from the create page.
- Preserve all seven steps and existing validation behavior.
- Do not add dependencies.

---

### Task 1: Layout contract and horizontal stepper

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- Consumes: existing `step`, `stepNames` and `stepDetails`
- Produces: `.ai-horizontal-steps` and a full-width `.ai-wizard-layout`

- [ ] Add failing assertions for `.ai-horizontal-steps`, `确认你的简历内容`, and absence of `ai-live-preview`.
- [ ] Run `npm test` and confirm the old three-column layout fails the contract.
- [ ] Move the step navigation above the panel, remove live preview markup, and retain step click behavior.
- [ ] Add desktop and mobile horizontal stepper styles.

### Task 2: Reference-style resume review

**Files:**
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/ResumeEditor.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

**Interfaces:**
- Consumes: `ParsedResume.sections`, profile fields, file name and current edit callbacks
- Produces: `.ai-resume-file-row`, `.ai-resume-section-tabs` and one active `.ai-resume-section-card`

- [ ] Add failing assertions for the file row, section tabs and active-section state.
- [ ] Run `npm test` and confirm failure before implementation.
- [ ] Rebuild the resume result header and upload row without changing upload behavior.
- [ ] Add active section tab state to `ResumeEditor` and render only the selected section.
- [ ] Apply reference-style profile and section card CSS with responsive fallbacks.
- [ ] Run `npm test && npm run build`, then verify the current uploaded resume in the browser.
