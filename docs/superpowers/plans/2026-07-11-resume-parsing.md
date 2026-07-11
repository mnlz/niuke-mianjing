# Resume Parsing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 PDF 简历解析为完整文本、基础信息和经历分区，并在配置页展示可核对结果。

**Architecture:** 新增纯后端解析服务，使用现有 `pypdf` 的布局提取模式；路由只校验上传并在线程池调用服务。前端扩展现有响应类型和结果卡，完整文本仍是唯一送入 AI 报告的数据源。

**Tech Stack:** Python、pypdf、FastAPI、pytest、React 18、TypeScript、Ant Design、Node assert。

## Global Constraints

- 不新增 OCR、AI 调用、数据库表或第三方依赖。
- PDF 最大 8 MB，最多提取前 12 页，返回文本最多 12000 字符。
- 保留响应中的 `text` 字段和现有 AI 报告请求行为。
- 使用 `简历/` 下 5 份 PDF 做真实回归。
- 工作区含用户未提交改动，不自动提交实现文件。

---

### Task 1: 后端布局提取与结构解析

**Files:**
- Create: `niuke_mianjing_backend/services/resume_parser.py`
- Create: `tests/test_resume_parser.py`

**Interfaces:**
- Produces: `parse_resume_pdf(content: bytes) -> dict`，返回 `text/name/phone/email/page_count/char_count/sections`。

- [ ] **Step 1: 写失败测试**

测试 `简历/` 下每份 PDF：结果文本非空，姓名、手机号、邮箱非空，至少有一个分区；再用伪 PDF 验证抛出 `ValueError`。

```python
@pytest.mark.parametrize("path", sorted((ROOT / "简历").glob("*.pdf")))
def test_real_resume_samples(path):
    result = parse_resume_pdf(path.read_bytes())
    assert result["text"]
    assert result["name"]
    assert result["phone"]
    assert result["email"]
    assert result["sections"]
```

- [ ] **Step 2: 确认测试失败**

Run: `.venv/bin/python -m pytest tests/test_resume_parser.py -q`

Expected: FAIL，模块 `resume_parser` 尚不存在。

- [ ] **Step 3: 实现最小解析器**

`resume_parser.py` 定义：

```python
SECTION_TITLES = {
    "教育经历": "education", "工作经历": "work", "实习经历": "internship",
    "项目经历": "projects", "专业技能": "skills", "技能": "skills",
    "技能/证书及其他": "skills", "荣誉奖项": "awards", "校园经历": "campus",
    "工作以外经历": "other", "个人总结": "summary", "其他": "other",
}

def parse_resume_pdf(content: bytes) -> dict:
    reader = PdfReader(io.BytesIO(content))
    pages = reader.pages[:12]
    text = "\n".join(_extract_page(page) for page in pages)
    return _parse_text(text[:12000], len(reader.pages))
```

`_extract_page` 优先调用 `page.extract_text(extraction_mode="layout")`，发生兼容性异常时回退 `page.extract_text()`；`_parse_text` 负责空白归一化、联系方式、姓名和分区切分。

- [ ] **Step 4: 验证任务 1**

Run: `.venv/bin/python -m pytest tests/test_resume_parser.py -q`

Expected: 真实样本与错误用例全部 PASS。

---

### Task 2: 接口响应与前端类型

**Files:**
- Modify: `niuke_mianjing_backend/api/routes/recruitment.py:741-760`
- Modify: `niuke-mianjing-frontend/src/api/types.ts`
- Modify: `niuke-mianjing-frontend/src/api/recruitment.ts:51-61`
- Test: `tests/test_resume_parser.py`

**Interfaces:**
- Consumes: `parse_resume_pdf(content)`。
- Produces: `ParsedResume`、`ParsedResumeSection` TypeScript 类型和兼容的 API 响应。

- [ ] **Step 1: 写失败的接口契约测试**

测试路由拒绝错误扩展名、伪 PDF 文件头，并确认有效 PDF 的响应包含 `text/name/phone/email/page_count/char_count/sections`。

- [ ] **Step 2: 确认测试失败**

Run: `.venv/bin/python -m pytest tests/test_resume_parser.py -q`

Expected: FAIL，现有路由没有文件头校验且响应只含 `text`。

- [ ] **Step 3: 修改路由和类型**

路由校验 `content.startswith(b"%PDF-")`，再执行：

```python
try:
    parsed = await run_in_threadpool(parse_resume_pdf, content)
except ValueError as exc:
    raise BadRequestException(str(exc)) from exc
return ApiResponse(message="解析成功", data=parsed)
```

前端类型：

```ts
export interface ParsedResumeSection { key: string; title: string; content: string }
export interface ParsedResume {
  text: string; name: string; phone: string; email: string
  page_count: number; char_count: number; sections: ParsedResumeSection[]
}
```

`recruitmentApi.parseResume()` 改为 `ApiResponse<ParsedResume>`。

- [ ] **Step 4: 验证任务 2**

Run: `.venv/bin/python -m pytest tests/test_resume_parser.py -q`

Expected: PASS。

---

### Task 3: 前端解析结果展示

**Files:**
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- Modify: `niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`
- Modify: `niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

**Interfaces:**
- Consumes: `ParsedResume`。
- Produces: 上传时结构化摘要、现有完整文本编辑和确认流程。

- [ ] **Step 1: 写失败的前端契约测试**

断言配置页使用 `ParsedResume`、展示 `上传时识别结果`、`page_count` 和 `sections`，并把上传提示统一为 8 MB。

- [ ] **Step 2: 确认测试失败**

Run: `cd niuke-mianjing-frontend && node scripts/aiAnalysis.test.mjs`

Expected: FAIL，页面尚未保存结构化响应。

- [ ] **Step 3: 实现最小界面**

增加 `parsedResume` 状态；上传成功后同时设置 `resume=result.text` 和 `parsedResume=result`。结果卡显示姓名、邮箱、手机号、页数、字数和分区摘要；完整文本框保持可编辑，修改只撤销确认，不重写上传时摘要。

- [ ] **Step 4: 验证任务 3**

Run: `cd niuke-mianjing-frontend && node scripts/aiAnalysis.test.mjs && npm run build`

Expected: 契约测试与构建 PASS。

---

### Task 4: 完整与浏览器验收

**Files:**
- Verify: `简历/*.pdf`
- Verify: `niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`

**Interfaces:**
- Consumes: Tasks 1–3。
- Produces: 可从前端上传并确认的完整流程。

- [ ] **Step 1: 运行完整检查**

Run: `.venv/bin/python -m pytest -q && .venv/bin/python -m compileall -q niuke_mianjing_backend main.py && cd niuke-mianjing-frontend && npm test && npm run build`

Expected: 全部 PASS；允许现有 Vite chunk-size 警告。

- [ ] **Step 2: 浏览器上传真实样本**

在 `/ai-analysis/create?report=full` 第 5 步上传 `简历/zzw_0410.pdf`，确认姓名、联系方式、页数、分区和完整文本可见。

- [ ] **Step 3: 验证编辑与确认**

修改完整文本，确认状态为“待确认”；点击“确认使用此简历”后状态变为“已确认”。

- [ ] **Step 4: 差异检查**

Run: `git diff --check`

Expected: 无空白错误，不覆盖无关工作区改动。
