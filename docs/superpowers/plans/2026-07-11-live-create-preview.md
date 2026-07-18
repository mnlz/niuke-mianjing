# Live Create Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep a live report preview visible through all seven configuration steps and progressively include each confirmed choice, including parsed resume details.

**Architecture:** Reuse the existing `CreatePage` state and dormant preview styles. Render one compact preview beside the wizard at every step; derive its rows directly from current state without introducing another store or API.

**Tech Stack:** React 18, TypeScript, Ant Design, CSS, Node assertion tests.

## Global Constraints

- Do not add dependencies.
- Keep the parsed resume editor usable by using a narrower preview column and responsive stacking.
- Remove the version tag and resume avatar, and replace the account icon.

---

### Task 1: Lock the requested UI behavior

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

- [ ] Add source assertions for the always-visible preview, seven progressive entries, resume summary, removed version/avatar, and new account icon.
- [ ] Run `npm test` and confirm the new assertions fail for the missing behavior.

### Task 2: Implement the progressive preview

**Files:**
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/AnalysisHeader.tsx`
- Modify: `niuke-mianjing-frontend/src/components/UserSessionButton/index.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/ResumeEditor.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

- [ ] Derive seven preview rows from current wizard state and reveal rows up to the current step.
- [ ] Include parsed name, section count, page count, and confirmation status in the resume row.
- [ ] Render the preview at every step and keep it responsive.
- [ ] Remove the version tag/avatar and switch the account icon.
- [ ] Run `npm test` and `npm run build` until both pass.

### Task 3: Browser verification

**Files:** None.

- [ ] Verify steps 1, 5, and 7 show the preview and progressively richer data.
- [ ] Verify the header changes and resume layout without performing another upload.
