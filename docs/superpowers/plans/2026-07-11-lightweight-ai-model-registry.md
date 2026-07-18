# Lightweight AI Model Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let administrators configure OpenAI-compatible models from `.env` or MySQL and let users select the real upstream model used for AI reports.

**Architecture:** A small in-process registry merges environment models, encrypted database overrides, and the legacy single-model settings into an immutable runtime map. Existing HTTP calls remain OpenAI-compatible; no gateway or provider SDK is added. Public APIs expose only safe model metadata, while protected admin APIs mutate database overrides and refresh the registry.

**Tech Stack:** Python 3, FastAPI, Pydantic Settings, aiomysql, cryptography/Fernet, requests, React 18, TypeScript, Ant Design.

## Global Constraints

- `model` is both the user-visible name and the exact upstream model request value.
- API keys never reach the public frontend or logs.
- Database API keys are encrypted with `AI_MODEL_SECRET_KEY`.
- Existing `OPENAI_*` settings remain a backward-compatible fallback.
- Only OpenAI-compatible Chat Completions endpoints are supported.
- No new dependency, gateway, fallback router, billing, image, audio, or embedding support.
- The live model test is explicit and excluded from the default offline test chain.

---

### Task 1: Model parsing, endpoint normalization, and encryption

**Files:**
- Create: `niuke_mianjing_backend/services/ai_model_registry.py`
- Modify: `niuke_mianjing_backend/config/settings.py`
- Modify: `.env.example`
- Test: `tests/test_ai_model_registry.py`

**Interfaces:**
- Produces: `AIModelConfig`, `normalize_chat_endpoint(endpoint)`, `parse_env_models(raw)`, `encrypt_api_key(value)`, `decrypt_api_key(value)`, and `mask_api_key(value)`.
- Consumes: existing `settings.OPENAI_*` values and optional `settings.AI_MODELS_JSON`, `settings.AI_MODEL_SECRET_KEY`.

- [ ] **Step 1: Write failing pure-function tests**

Cover a `/v1` Base URL, a full `/chat/completions` URL, valid and invalid JSON, duplicate/default normalization, Fernet round trip, and masked output.

- [ ] **Step 2: Verify the tests fail**

Run: `.venv/bin/python -m pytest tests/test_ai_model_registry.py -q`

Expected: import failure because `ai_model_registry.py` does not exist.

- [ ] **Step 3: Implement the minimal model configuration functions**

Use a frozen dataclass:

```python
@dataclass(frozen=True)
class AIModelConfig:
    model: str
    endpoint: str
    api_key: str
    description: str = ""
    enabled: bool = True
    is_default: bool = False
    source: str = "env"
```

Parse `AI_MODELS_JSON` with `json.loads`, validate required strings, normalize endpoints, and fall back to the existing `OPENAI_*` model only when no JSON models exist.

- [ ] **Step 4: Verify Task 1 passes**

Run: `.venv/bin/python -m pytest tests/test_ai_model_registry.py -q`

Expected: all Task 1 tests pass.

### Task 2: Encrypted database overrides and runtime registry

**Files:**
- Create: `niuke_mianjing_backend/repositories/ai_model_repo.py`
- Modify: `niuke_mianjing_backend/services/ai_model_registry.py`
- Modify: `niuke_mianjing_backend/api/app.py`
- Test: `tests/test_ai_model_registry.py`

**Interfaces:**
- Produces: `AIModelRepository.init_table/list_all/upsert/delete`, `AIModelRegistry.refresh/list_public/list_admin/resolve`, and singleton `ai_model_registry`.
- Consumes: `AIModelConfig` and the existing repository/database patterns.

- [ ] **Step 1: Add failing merge and resolution tests**

Use a fake repository with `asyncio.run()` to prove database rows override same-name environment models, inherit the environment key when ciphertext is empty, prefer a database default, reject disabled/unknown models, and never expose `api_key` in public/admin dictionaries.

- [ ] **Step 2: Verify the new tests fail**

Run: `.venv/bin/python -m pytest tests/test_ai_model_registry.py -q`

Expected: missing registry/repository behavior.

- [ ] **Step 3: Implement repository and registry**

Create `ai_model_configs` with `model` as the unique key and columns for endpoint, encrypted key, description, enabled, default flag, and timestamps. When `is_default` is written, clear the previous database default in the same repository method. Initialize and refresh the registry during FastAPI startup.

- [ ] **Step 4: Verify Task 2 passes**

Run: `.venv/bin/python -m pytest tests/test_ai_model_registry.py -q`

Expected: all registry tests pass without MySQL access.

### Task 3: Unified model-aware calls and APIs

**Files:**
- Modify: `niuke_mianjing_backend/services/openai_client.py`
- Modify: `niuke_mianjing_backend/services/recruitment_ai.py`
- Modify: `niuke_mianjing_backend/api/routes/recruitment.py`
- Modify: `niuke_mianjing_backend/api/middleware/auth.py`
- Create: `tests/test_ai_model_live.py`
- Test: `tests/test_ai_model_registry.py`

**Interfaces:**
- Produces: `post_chat_completion(..., model: str | None = None)`, public/admin model endpoints, and a `model` field in `RecruitmentAIReportRequest`.
- Consumes: singleton `ai_model_registry` and existing admin/user authentication.

- [ ] **Step 1: Add failing request-selection tests**

Patch only `requests.post` and assert the resolved endpoint, authorization header, and exact model name are used. Assert public output contains no endpoint or key and report requests reject disabled models.

- [ ] **Step 2: Verify the tests fail**

Run: `.venv/bin/python -m pytest tests/test_ai_model_registry.py -q`

Expected: `post_chat_completion` does not accept `model` and API helpers are absent.

- [ ] **Step 3: Implement the model-aware request flow and endpoints**

Pass the selected model through `generate_recruitment_ai_report()` → `call_ai_report()` → `post_chat_completion()`. Save the selected real model name in the existing report column. Admin writes encrypt the supplied key, preserve an existing/inherited key when blank, refresh the registry, and return only masked key metadata.

- [ ] **Step 4: Add the explicit live test**

`tests/test_ai_model_live.py` exits unless `RUN_AI_MODEL_LIVE_TEST=1`. When enabled, initialize the runtime registry from local configuration, send `只回复 OK`, assert a non-empty completion, and print only model name, elapsed milliseconds, and success.

- [ ] **Step 5: Verify Task 3 passes offline**

Run: `.venv/bin/python -m pytest tests/test_ai_model_registry.py -q`

Expected: all offline backend tests pass.

### Task 4: Admin model management page

**Files:**
- Create: `niuke-mianjing-frontend/src/pages/AIModels/index.tsx`
- Create: `niuke-mianjing-frontend/src/pages/AIModels/style.css`
- Modify: `niuke-mianjing-frontend/src/api/recruitment.ts`
- Modify: `niuke-mianjing-frontend/src/api/types.ts`
- Modify: `niuke-mianjing-frontend/src/App.tsx`
- Modify: `niuke-mianjing-frontend/src/components/Layout/index.tsx`
- Test: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

**Interfaces:**
- Produces: typed public/admin model API methods and `/ai-models` admin page.
- Consumes: the Task 3 endpoints and existing admin token client behavior.

- [ ] **Step 1: Add failing frontend source assertions**

Assert that the API exposes list/create/update/delete/test methods, the page masks keys, and App/Layout register the protected route and menu item.

- [ ] **Step 2: Verify the frontend test fails**

Run: `cd niuke-mianjing-frontend && npm test`

Expected: assertions fail because the page and API methods do not exist.

- [ ] **Step 3: Implement the minimal admin page**

Use an Ant Design table and one modal form for model, endpoint, API key, description, enabled, and default. Provide edit, connection test, and delete actions. Environment rows become editable by saving a database override; secrets remain masked.

- [ ] **Step 4: Verify Task 4 passes**

Run: `cd niuke-mianjing-frontend && npm test`

Expected: all frontend tests pass.

### Task 5: Real model selection in report creation

**Files:**
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/analysisUtils.ts`
- Modify: `niuke-mianjing-frontend/src/api/recruitment.ts`
- Modify: `niuke-mianjing-frontend/src/api/types.ts`
- Test: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

**Interfaces:**
- Produces: live model picker and `model` in the AI report request.
- Consumes: public model list from Task 3 and typed API from Task 4.

- [ ] **Step 1: Add failing model-selection assertions**

Assert `mockModels` is removed, public models are loaded, the default model is selected, and `buildAnalysisRequest()` includes `model`.

- [ ] **Step 2: Verify the frontend test fails**

Run: `cd niuke-mianjing-frontend && npm test`

Expected: assertions fail on the existing mock model implementation.

- [ ] **Step 3: Implement the live model picker**

Load models with the other create-page metadata, preserve a valid local draft selection, otherwise choose the backend default or first enabled model. Disable generation with a clear message when no model is available. Replace all preview/mock copy with real model metadata.

- [ ] **Step 4: Verify Task 5 passes**

Run: `cd niuke-mianjing-frontend && npm test && npm run build`

Expected: tests and production build pass.

### Task 6: Full verification and one real request

**Files:**
- Verify only; no new production files.

**Interfaces:**
- Consumes: all preceding tasks.
- Produces: evidence that offline tests, build, database startup, APIs, and one configured upstream model work.

- [ ] **Step 1: Run backend regression checks**

Run: `.venv/bin/python -m pytest tests/test_ai_model_registry.py tests/test_resume_parser.py -q`

Run: `.venv/bin/python -m compileall -q niuke_mianjing_backend main.py`

Expected: pass with no new warnings or syntax errors.

- [ ] **Step 2: Run frontend regression checks**

Run: `cd niuke-mianjing-frontend && npm test && npm run build`

Expected: pass; the existing Vite chunk-size warning is acceptable.

- [ ] **Step 3: Run one real configured model request**

Run: `RUN_AI_MODEL_LIVE_TEST=1 .venv/bin/python tests/test_ai_model_live.py`

Expected: prints the configured model name, elapsed milliseconds, and `success`; no key or response body is printed.

- [ ] **Step 4: Verify formatting and review scope**

Run: `git diff --check`

Expected: no whitespace errors and no unrelated files reverted.
