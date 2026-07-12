# Interview Prep Report Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the decision-oriented static report with a company-specific interview preparation report.

**Architecture:** Keep the existing dependency-free standalone HTML delivery, but replace its content hierarchy with exam scope, recent interview intelligence, evidence-backed resume rewrites, predicted questions, answer frameworks, round playbooks, mock exam, sprint plan, and final review sheet. Native JavaScript handles question filters, disclosures, answer cards, plan tabs, and mock-exam scoring.

**Tech Stack:** HTML5, CSS3, vanilla JavaScript, Node source regression test.

## Global Constraints

- Modify only `static-prototypes/ai-report-premium-concept.html` and its existing static source test.
- Keep all data local and clearly marked as demonstration data.
- Do not add dependencies or call APIs.
- Do not modify the React sample report.

---

### Task 1: Interview-prep content contract

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/staticAiPages.test.mjs`
- Modify: `static-prototypes/ai-report-premium-concept.html`

**Interfaces:**
- Produces: eleven preparation modules and local interactions for evidence, question filtering, answer expansion, plan switching, and mock scoring.

- [ ] **Step 1: Update the source assertions**

Require “面试准备度”, “公司岗位考纲”, “最近面试情报”, “简历逐项改写”, “公司专项押题”, “核心题作答框架”, “各轮作战手册”, “模拟考试”, “七天冲刺计划”, “考前速查”, and “数据与可信度”, plus the interactive data attributes.

- [ ] **Step 2: Verify RED**

Run: `cd niuke-mianjing-frontend && npm test`

Expected: FAIL because the old prototype does not implement the new structure.

- [ ] **Step 3: Replace the static report**

Rewrite the HTML around preparation readiness. Add side-by-side resume rewrites with reasons and evidence; grouped predicted questions with provenance; expandable answer frameworks; round-specific pass criteria; a scored mock exam; sprint plans; and a printable final review sheet.

- [ ] **Step 4: Verify GREEN and browser behavior**

Run: `cd niuke-mianjing-frontend && npm test`

Inspect the local prototype in the in-app browser. Verify section count, no horizontal overflow, question filters, answer disclosure, plan switching, mock score updates, and zero console errors.
