# Permanent AI Model IDs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow duplicate upstream model names from different relay channels while every database model is permanently addressed by numeric ID.

**Architecture:** Keep the existing model registry and repository, but key database-backed configurations by `ai_model_configs.id`. Add `channel_name`, migrate away from the model-name unique index, and pass `model_id` through admin actions and AI report generation while retaining model-name lookup for legacy `.env` callers.

**Tech Stack:** Python 3, FastAPI, Pydantic v2, aiomysql/MySQL, pytest, React 18, TypeScript, Axios, Ant Design.

## Global Constraints

- Preserve existing IDs and historical report rows.
- Never return plaintext API keys.
- Do not add dependencies or implement routing, failover, weighting, or billing.
- Preserve unrelated dirty-worktree changes.

---

### Task 1: ID-keyed repository and registry

**Files:**
- Modify: `tests/test_ai_model_registry.py`
- Modify: `niuke_mianjing_backend/repositories/ai_model_repo.py`
- Modify: `niuke_mianjing_backend/services/ai_model_registry.py`

**Interfaces:**
- Produces: `AIModelConfig.id: int`, `AIModelConfig.channel_name: str`, `AIModelRegistry.resolve(model_id=...)`, `save_override(data, model_id=None)`, and repository CRUD by ID.

- [ ] **Step 1: Write the failing registry test**

Add a test that loads two database rows with the same `model`, different `id`, `channel_name`, endpoints and encrypted keys, then asserts both public entries exist and `resolve(model_id=...)` selects the exact row.

- [ ] **Step 2: Verify the test fails**

Run: `.venv/bin/python -m pytest tests/test_ai_model_registry.py -q`

Expected: FAIL because the registry currently collapses rows by model name and has no ID/channel fields.

- [ ] **Step 3: Implement the minimum repository and registry changes**

Change the table initializer to add `channel_name`, drop `uk_ai_model_name` when present, select `id`, and use insert/update/delete by ID. Keep legacy environment models under stable negative in-memory IDs, remove them when a database row with the same model exists, and retain name lookup only for old internal callers.

- [ ] **Step 4: Verify registry tests pass**

Run: `.venv/bin/python -m pytest tests/test_ai_model_registry.py -q`

Expected: PASS.

---

### Task 2: Model ID API and report persistence

**Files:**
- Modify: `tests/test_ai_model_registry.py`
- Modify: `tests/test_ai_model_live.py`
- Modify: `niuke_mianjing_backend/services/openai_client.py`
- Modify: `niuke_mianjing_backend/services/recruitment_ai.py`
- Modify: `niuke_mianjing_backend/repositories/ai_report_repo.py`
- Modify: `niuke_mianjing_backend/api/routes/recruitment.py`

**Interfaces:**
- Consumes: `AIModelRegistry.resolve(model_id=...)` from Task 1.
- Produces: admin CRUD/test endpoints keyed by `model_id`, AI report request `model_id`, and persisted nullable report `model_id`.

- [ ] **Step 1: Write a failing request-routing test**

Update the chat request test to pass `model_id` and assert that the selected duplicate channel supplies its own Endpoint/key while the JSON body retains the shared real model name.

- [ ] **Step 2: Verify the test fails**

Run: `.venv/bin/python -m pytest tests/test_ai_model_registry.py -q`

Expected: FAIL because `post_chat_completion` does not accept `model_id`.

- [ ] **Step 3: Implement ID propagation**

Add optional `model_id` to the OpenAI request helper and recruitment AI call. Change admin update/delete/test routes and report generation to resolve by ID. Add nullable `model_id` to `ai_analysis_reports`, include it in insert/select mapping, and save both ID and real model name.

- [ ] **Step 4: Verify backend tests**

Run: `.venv/bin/python -m pytest tests/test_ai_model_registry.py tests/test_ai_model_live.py -q`

Expected: registry tests PASS; live test SKIPPED unless enabled.

---

### Task 3: Admin and analysis frontend

**Files:**
- Modify: `niuke-mianjing-frontend/src/api/types.ts`
- Modify: `niuke-mianjing-frontend/src/api/recruitment.ts`
- Modify: `niuke-mianjing-frontend/src/pages/AIModels/index.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/analysisUtils.ts`
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

**Interfaces:**
- Consumes: public/admin model `id` and `channel_name`; admin/report endpoints keyed by `model_id`.
- Produces: ID-keyed table/actions and `模型名 · 渠道名称` selection cards.

- [ ] **Step 1: Add failing source regression assertions**

Assert the frontend uses `model_id`, `rowKey="id"`, renders `channel_name`, and does not key model cards by model name.

- [ ] **Step 2: Verify the regression check fails**

Run: `cd niuke-mianjing-frontend && npm test`

Expected: FAIL on the new ID/channel assertions.

- [ ] **Step 3: Implement the minimum frontend changes**

Add numeric IDs and channel names to API types, update API paths/bodies, add ID/channel columns and form input, and store/select/submit `selectedModelId` in the analysis wizard.

- [ ] **Step 4: Verify frontend**

Run: `cd niuke-mianjing-frontend && npm test && npm run build`

Expected: PASS.

---

### Task 4: Migration and live verification

**Files:**
- Modify only if failures require a scoped correction to files above.

**Interfaces:**
- Consumes: completed backend and frontend model-ID flow.
- Produces: migrated local table and evidence that the real configured model still responds.

- [ ] **Step 1: Restart/refresh the backend migration**

Ensure application startup runs `AIModelRepository.init_table()` and refreshes the registry. Query the API to confirm the existing model retained its positive ID and channel name.

- [ ] **Step 2: Run full automated verification**

Run: `.venv/bin/python -m pytest tests -q`

Run: `cd niuke-mianjing-frontend && npm test && npm run build`

Expected: all tests and build PASS, except explicitly skipped live tests.

- [ ] **Step 3: Run one real model request**

Run: `RUN_AI_MODEL_LIVE_TEST=1 .venv/bin/python -m pytest tests/test_ai_model_live.py -q -s`

Expected: PASS with non-empty response and elapsed time printed; no key is printed.
