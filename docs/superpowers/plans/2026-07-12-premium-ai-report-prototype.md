# Premium AI Report Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone interactive HTML prototype for the complete OfferLens flagship job-search report.

**Architecture:** Use one dependency-free HTML file containing semantic report sections, CSS visualizations, responsive/print styles, and minimal native JavaScript for navigation, evidence disclosure, and plan switching. Keep it isolated from the React application.

**Tech Stack:** HTML5, CSS3, vanilla JavaScript, Node source regression test.

## Global Constraints

- Output only to `static-prototypes/ai-report-premium-concept.html` plus the existing static prototype test.
- Do not call APIs, load remote assets, or add dependencies.
- Mark all content as demonstration data.

---

### Task 1: Static prototype contract

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/staticAiPages.test.mjs`
- Create: `static-prototypes/ai-report-premium-concept.html`

**Interfaces:**
- Produces: a standalone report page with twelve named modules and local interactions.

- [ ] **Step 1: Add the failing source check**

Assert the target file exists and contains the report title, all twelve module anchors, evidence disclosure, plan tabs, responsive styles, print styles, and a demo-data notice.

- [ ] **Step 2: Verify RED**

Run: `cd niuke-mianjing-frontend && npm test`

Expected: FAIL because the prototype file does not exist.

- [ ] **Step 3: Implement the standalone HTML**

Create the decision-first report with sticky navigation, summary cards, CSS charts, evidence matrix, resume diff, interview questions, risk groups, action-plan tabs, strategy ranking, methodology section, responsive layout, and print rules.

- [ ] **Step 4: Verify source and rendering**

Run: `cd niuke-mianjing-frontend && npm test`

Run: `python -m http.server 8000 --directory static-prototypes` and inspect `/ai-report-premium-concept.html` in the in-app browser.

Expected: tests pass, all modules render, and local interactions work without console errors.
