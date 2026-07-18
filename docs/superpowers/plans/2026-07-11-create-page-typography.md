# Create Page Typography Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refine Header sizing, resume readability, long-section height, and upload spacing.

**Architecture:** Change only existing AI analysis CSS and lock the values with the current source assertion test. Preserve parsed text and upload behavior.

**Tech Stack:** CSS, Node assertion tests, Vite.

## Global Constraints

- Do not change resume parsing or upload behavior.
- Do not automate file upload verification.
- Do not add dependencies.

---

### Task 1: Typography and spacing regression

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- Consumes: existing Header, upload drop zone, and resume section markup.
- Produces: smaller Header text, 13px resume text, 360px scroll cap, and wider upload spacing.

- [ ] Add CSS source assertions for Header font size, resume font size, removed minimum height, maximum height, overflow, and upload gap.
- [ ] Run `npm test` and confirm the new assertions fail.
- [ ] Apply the minimum CSS changes matching the approved values.
- [ ] Run `npm test`, `npm run build`, and `git diff --check`.
