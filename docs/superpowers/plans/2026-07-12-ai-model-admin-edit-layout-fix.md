# AI Model Admin Edit and Layout Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the selected model's real configuration in the edit modal and display the complete Endpoint with a narrower model column.

**Architecture:** Keep the existing AIModels component and Ant Design table/form. Mount the modal form before writing values, reset it at each open/close boundary, and use explicit table widths plus horizontal scrolling instead of truncation.

**Tech Stack:** React 18, TypeScript, Ant Design, existing Node source regression script.

## Global Constraints

- API Key remains blank during editing and is never returned in plaintext.
- No backend or API contract changes.
- Model column width is 140px.
- Endpoint is not truncated or wrapped.
- Narrow screens scroll the table horizontally.

---

### Task 1: Fix edit form hydration and table columns

**Files:**
- Modify: `niuke-mianjing-frontend/src/pages/AIModels/index.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIModels/style.css`
- Test: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

**Interfaces:**
- Consumes: existing `AIModelAdmin` row returned by `recruitmentApi.adminAIModels()`.
- Produces: an edit modal populated with row values and a table that fully displays Endpoint text.

- [ ] **Step 1: Add failing source regression assertions**

```javascript
assert.match(aiModelsSource, /forceRender/)
assert.doesNotMatch(aiModelsSource, /destroyOnClose/)
assert.match(aiModelsSource, /form\.resetFields\(\)/)
assert.match(aiModelsSource, /title: '模型',[\s\S]*?width: 140/)
assert.match(aiModelsSource, /title: 'Endpoint',[\s\S]*?width: 360/)
assert.doesNotMatch(aiModelsSource, /title: 'Endpoint',[^\n]*ellipsis/)
assert.match(aiModelsSource, /scroll=\{\{ x: 1060 \}\}/)
assert.match(aiModelStyleSource, /\.ai-model-endpoint \{ white-space: nowrap; \}/)
```

- [ ] **Step 2: Run the test and confirm the expected failure**

Run: `cd niuke-mianjing-frontend && npm test`

Expected: failure because `forceRender`, explicit widths, scroll, and endpoint style are absent.

- [ ] **Step 3: Implement the minimal component fix**

In `edit()`, call `form.resetFields()` before `form.setFieldsValue()`. Keep the Form mounted with `forceRender`, remove `destroyOnClose`, and reset on cancel. Set model width to `140`, Endpoint width to `360`, render Endpoint with class `ai-model-endpoint`, remove ellipsis, and add `scroll={{ x: 1060 }}` to the table.

- [ ] **Step 4: Run automated verification**

Run: `cd niuke-mianjing-frontend && npm test && npm run build`

Expected: all tests and TypeScript/Vite build pass.

- [ ] **Step 5: Run browser verification**

At `http://127.0.0.1:3000/ai-models`, click Edit and verify model `gpt-5.5`, full Endpoint, description, enabled/default switches, and blank API Key. Verify the table model column is about 140px and the Endpoint text is fully visible at 1140px and wide viewport sizes.

- [ ] **Step 6: Check formatting and scope**

Run: `git diff --check`

Expected: no whitespace errors and no unrelated changes reverted.
