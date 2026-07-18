# AI 分析体验优化实施计划

**目标：** 完成默认中文昵称、AI 分析首页信任内容、报告命名优化、配置页精简和简历解析确认流程。

**原则：** 保持现有 FastAPI/React 结构，不增加第三方依赖；后端昵称按需补齐，前端雷达图使用内联 SVG，简历解析只做本地文本与联系方式提取。

## 任务 1：默认中文昵称

**文件：**
- 修改：`niuke_mianjing_backend/api/routes/user_auth.py`
- 修改：`niuke_mianjing_backend/repositories/review_repo.py`
- 修改：`tests/test_user_auth.py`
- 修改：`niuke-mianjing-frontend/src/api/auth.ts`
- 修改：`niuke-mianjing-frontend/src/utils/auth.ts`
- 修改：`niuke-mianjing-frontend/src/components/UserSessionButton/index.tsx`
- 修改：`niuke-mianjing-frontend/scripts/userAuth.test.mjs`

1. 先增加昵称格式、注册返回、旧账号登录补齐的失败测试。
2. 为 `app_users` 增加 `display_name` 字段和更新方法。
3. 使用 `意象词 + 动物 + 四位数字` 生成昵称，并在注册、登录、`me` 返回。
4. 前端会话兼容旧数据，导航优先展示 `display_name`。
5. 运行后端用户鉴权测试和前端用户会话测试。

## 任务 2：首页信任内容与报告命名

**文件：**
- 修改：`niuke-mianjing-frontend/src/pages/AIAnalysis/index.tsx`
- 修改：`niuke-mianjing-frontend/src/pages/AIAnalysis/config.ts`
- 修改：`niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`
- 修改：搜索结果中所有实际页面的旧报告名称
- 修改：`niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

1. 先增加“全景求职研判”名称测试并确认失败。
2. 将“四合一作战地图”统一替换为“全景求职研判”，保持 `report_type=full` 不变。
3. 将原价值说明卡片替换为六维雷达图、报告能力摘要和三条内测反馈。
4. 增加响应式样式，不引入图表依赖。

## 任务 3：精简报告配置流程

**文件：**
- 修改：`niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- 修改：`niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`

1. 删除公司步骤顶部重复下拉框，仅保留公司卡片选择。
2. 删除页面标题区“我的报告”按钮，保留全局导航入口。
3. 清理不再使用的公司选项派生变量和导入。

## 任务 4：简历解析结果确认

**文件：**
- 修改：`niuke-mianjing-frontend/src/pages/AIAnalysis/analysisUtils.ts`
- 修改：`niuke-mianjing-frontend/src/pages/AIAnalysis/CreatePage.tsx`
- 修改：`niuke-mianjing-frontend/src/pages/AIAnalysis/style.css`
- 修改：`niuke-mianjing-frontend/scripts/aiAnalysis.test.mjs`

1. 先增加邮箱、手机号提取，以及“有简历但未确认不能生成”的失败测试。
2. 实现纯函数联系方式提取与简历确认校验。
3. 上传或粘贴后展示文件名、字数、联系方式和可编辑解析文本。
4. 增加“确认使用此简历”；编辑后自动撤销确认。
5. 在最终确认步骤展示简历确认状态，并阻止未确认的简历型报告生成。

## 任务 5：完整验证

1. 运行相关后端测试和前端脚本测试。
2. 运行后端完整测试、前端完整测试与 `npm run build`。
3. 在浏览器验证首页、公司选择、简历粘贴/编辑/确认和导航昵称。
4. 检查 `git diff`，确保没有覆盖工作区内无关改动。
