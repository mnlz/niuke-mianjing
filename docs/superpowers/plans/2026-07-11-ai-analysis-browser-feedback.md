# AI Analysis Browser Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修正 7 处 AI 分析页面批注，并增加不透传后端的前端 Mock 模型步骤。

**Architecture:** 保持现有 React 页面和请求构造器不变，只在页面组件保存 Mock 模型状态并复用当前 localStorage 草稿；样式集中修改现有 `style.css`。现有 `buildAnalysisRequest()` 继续作为唯一生成请求入口，确保模型不进入 API。

**Tech Stack:** React 18、TypeScript、Ant Design、原生 CSS、Node assert 契约测试。

## Global Constraints

- `/ai-analysis` 首页右侧报告预览内容保持不变。
- 模型仅前端 Mock：`gpt-5.4-mini`、`gpt-5.5`、`gpt-5.6-sol`，默认 `gpt-5.5`。
- 不修改后端、API 请求类型或 `buildAnalysisRequest()` 输出。
- 不新增依赖，不覆盖工作区无关改动。

---

### Task 1: 向导、模型步骤与 Header

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/AnalysisHeader.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- Consumes: `buildAnalysisRequest(config)`，输出必须继续不含 `model`。
- Produces: 7 步向导、`selectedModel: string` 前端状态、三段式 Header。

- [ ] **Step 1: 写失败的源码契约测试**

在 `aiAnalysis.test.mjs` 增加断言：`buildAnalysisRequest(baseConfig)` 无 `model`；配置页包含 `TOTAL_STEPS = 7`、三个模型 ID 和“预览配置”；不再包含 `ai-step-keyboard`、`addEventListener('keydown'`；Header 包含 `ai-header-primary-nav` 与 `ai-header-account`。

- [ ] **Step 2: 验证测试按预期失败**

Run: `cd niuke-mianjing-frontend && node scripts/aiAnalysis.test.mjs`

Expected: FAIL，首个缺失项为 `TOTAL_STEPS = 7` 或模型文案。

- [ ] **Step 3: 实现最小页面修改**

在 `CreatePage.tsx` 中：

```tsx
const TOTAL_STEPS = 7
const analysisModels = [
  { id: 'gpt-5.4-mini', name: '快速分析', desc: '适合快速预览报告结构' },
  { id: 'gpt-5.5', name: '标准分析', desc: '默认推荐，平衡速度与完整度', recommended: true },
  { id: 'gpt-5.6-sol', name: '深度分析', desc: '适合复杂岗位与完整求职研判' },
]
```

增加 `selectedModel` 状态并写入现有草稿；第 6 步渲染模型卡片，第 7 步确认并展示模型；删除键盘监听、侧栏提示和底部键盘提示。报告类型卡片把编号代号与正文改为纵向结构。

在 `AnalysisHeader.tsx` 中把品牌、主导航和账号拆成 `public-brand`、`ai-header-primary-nav`、`ai-header-account` 三个直接子区。

- [ ] **Step 4: 修正现有 CSS**

`style.css` 中使用三列 Header 网格、纵向报告类型卡片、三列模型卡片；删除 `.ai-step-keyboard` 和键盘提示样式；移动端隐藏主导航并保留账号入口。

- [ ] **Step 5: 验证任务 1**

Run: `cd niuke-mianjing-frontend && node scripts/aiAnalysis.test.mjs`

Expected: PASS，输出 `aiAnalysis tests passed`。

---

### Task 2: 示例报告依据与报告中心精简

**Files:**
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/SampleReportPage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/ReportsPage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

**Interfaces:**
- Consumes: 现有静态示例报告结构和报告列表数据。
- Produces: 带静态样本依据的问题列表、3 个 KPI 的报告中心。

- [ ] **Step 1: 写失败的源码契约测试**

增加断言：示例报告包含 `示例面经统计`、`出现 5 次`、`命中率 83%`；报告中心不含 `DATA OWNERSHIP`；CSS 的 KPI 主网格为 3 列。

- [ ] **Step 2: 验证测试按预期失败**

Run: `cd niuke-mianjing-frontend && node scripts/aiAnalysis.test.mjs`

Expected: FAIL，缺少 `示例面经统计`。

- [ ] **Step 3: 实现示例与报告中心修改**

保持 BEFORE/AFTER 左右结构和浅橙、浅绿背景；每个问题正文下增加静态依据，例如：

```tsx
<small>示例面经统计 · 出现 5 次 · 命中率 83%</small>
```

删除 `ReportsPage.tsx` 的第四个 KPI，并把桌面 KPI 网格调整为 `repeat(3, 1fr)`。

- [ ] **Step 4: 验证任务 2**

Run: `cd niuke-mianjing-frontend && node scripts/aiAnalysis.test.mjs`

Expected: PASS。

---

### Task 3: 完整与浏览器验证

**Files:**
- Verify: `niuke-mianjing-frontend/src/pages/AIAnalysis/*`

**Interfaces:**
- Consumes: Tasks 1–2 的页面和样式。
- Produces: 可构建、可浏览的最终页面。

- [ ] **Step 1: 运行前端完整测试**

Run: `cd niuke-mianjing-frontend && npm test`

Expected: 全部脚本通过。

- [ ] **Step 2: 运行生产构建**

Run: `cd niuke-mianjing-frontend && npm run build`

Expected: TypeScript 与 Vite 构建成功；允许现有 chunk-size 警告。

- [ ] **Step 3: 浏览器检查**

依次检查 `/ai-analysis/create?report=full`、`/ai-analysis/sample-report`、`/ai-analysis/reports` 和 `/ai-analysis`：类型卡无重叠，Header 对齐，7 步可点击，模型在确认页显示，样本依据可见，报告中心只有 3 个 KPI，首页保护预览文案未变。

- [ ] **Step 4: 检查差异范围**

Run: `git diff --check && git diff -- niuke-mianjing-frontend/src/pages/AIAnalysis niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

Expected: 无空白错误，修改仅覆盖计划内文件。
