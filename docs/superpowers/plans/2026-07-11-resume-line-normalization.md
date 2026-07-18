# Resume Line Normalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove PDF layout soft wraps without merging genuine resume items, and enlarge the structured resume editor's small text.

**Architecture:** Keep layout extraction because plain extraction expands one real sample from 60 to 180 lines. Add one conservative normalization function before section splitting, then adjust only resume-editor CSS.

**Tech Stack:** Python, pypdf, pytest, CSS, Node assertion tests, Vite.

## Global Constraints

- Validate all five local PDF samples.
- Preserve section titles and likely new list items.
- Do not automate file uploads.
- Do not add dependencies.

---

### Task 1: Backend soft-wrap normalization

**Files:**
- Modify: `tests/test_resume_parser.py`
- Modify: `niuke_mianjing_backend/services/resume_parser.py`

**Interfaces:**
- Consumes: cleaned layout lines from `_clean_lines(text)`.
- Produces: `_join_wrapped_lines(lines: list[str]) -> list[str]` used by `parse_resume_pdf`.

- [ ] Add unit tests proving a long wrapped sentence joins, section titles and numbered/labelled items remain separate, and the Liu Ziyang sample no longer contains known split fragments.
- [ ] Run `.venv/bin/python -m pytest tests/test_resume_parser.py -q` and confirm the new tests fail.
- [ ] Implement the conservative line classifier and joiner, then apply it before name/section extraction.
- [ ] Run the parser tests and inspect all five real-sample section counts.

### Task 2: Resume editor typography

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- Consumes: existing resume editor classes.
- Produces: 12px tab titles, 10px tab metadata, 13px card titles and editable text, and 11–12px helper controls.

- [ ] Add CSS source assertions for the approved sizes.
- [ ] Run `npm test` and confirm the new assertions fail.
- [ ] Apply the minimum CSS changes without enlarging the live preview.
- [ ] Run `npm test`, `npm run build`, and `git diff --check`.
