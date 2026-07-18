# Structured Resume Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the raw resume textarea with a structured, readable, section-based editor.

**Architecture:** Keep `resume` as the report payload and `parsedResume` as presentation metadata. A focused `ResumeEditor` component edits profile fields and sections, while a small pure helper safely replaces the corresponding first occurrence in the full text.

**Tech Stack:** React 18, TypeScript, Ant Design, CSS, Node assert tests

## Global Constraints

- No new dependencies.
- Preserve the existing upload, confirmation and report-generation flow.
- Every edit must update the full `resume` text and revoke confirmation.

---

### Task 1: Safe text synchronization helper

**Files:**
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/analysisUtils.ts`
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

**Interfaces:**
- Produces: `replaceFirstText(source: string, previous: string, next: string): string`

- [ ] Add failing assertions for replacing only the first exact occurrence and handling a missing value.
- [ ] Run `npm test` and confirm the missing export failure.
- [ ] Implement the helper with `indexOf` and `slice` so replacement text containing `$` is safe.
- [ ] Run `npm test` and confirm the helper assertions pass.

### Task 2: Structured editor component

**Files:**
- Create: `niuke-mianjing-frontend/src/pages/AIAnalysis/ResumeEditor.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

**Interfaces:**
- Consumes: `resume`, `parsedResume`, and `onChange(text, parsedResume)`
- Produces: editable profile fields, section reading/editing cards, and advanced raw text editing

- [ ] Add failing source-contract assertions for profile inputs, section cards, edit controls and advanced editing.
- [ ] Run `npm test` and confirm the new component contract is absent.
- [ ] Implement `ResumeEditor` using local active-section state and `replaceFirstText`.
- [ ] Replace the merged textarea markup in `CreatePage` with `ResumeEditor`.
- [ ] Add responsive card, reading and editing styles without changing unrelated page layout.
- [ ] Run `npm test && npm run build` and confirm both succeed.
