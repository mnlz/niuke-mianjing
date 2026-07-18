# Interview Prep Report Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the company-specific static report with one role-adaptive interview preparation report that demonstrates three company/role scenarios.

**Architecture:** Keep one dependency-free standalone HTML file. A small in-page scenario data object drives the shared report shell; native JavaScript renders ByteDance backend, Meituan backend, and ByteDance Android without duplicating pages, while preserving filters, disclosures, plan tabs, and mock scoring.

**Tech Stack:** HTML5, CSS3, vanilla JavaScript, Node source regression test.

## Global Constraints

- Modify only the existing report prototype, its source test, and this approved design/plan documentation.
- Keep all data local and clearly marked as demonstration data.
- Do not add dependencies or call APIs.
- Do not modify the React sample report.

---

### Task 1: Role-adaptive report contract

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/staticAiPages.test.mjs`
- Modify: `static-prototypes/ai-report-premium-concept.html`

**Interfaces:**
- Produces: one shared report shell, three scenario buttons, eleven preparation modules, and local interactions for evidence, question filtering, answer expansion, plan switching, and mock scoring.

- [ ] **Step 1: Update the source assertions**

Require the three scenario controls, the shared report modules, and the interactive data attributes.

- [ ] **Step 2: Verify RED**

Run: `cd niuke-mianjing-frontend && npm test`

Expected: FAIL because the old prototype does not implement the new structure.

- [ ] **Step 3: Replace the static report**

Render the shared report from local scenario data. Each scenario supplies target metadata, exam modules, company traits, resume rewrites, questions, practical exercises, mock items, plan, and provenance.

- [ ] **Step 4: Verify GREEN and browser behavior**

Run: `cd niuke-mianjing-frontend && npm test`

Inspect the local prototype in the in-app browser. Verify section count, no horizontal overflow, question filters, answer disclosure, plan switching, mock score updates, and zero console errors.
