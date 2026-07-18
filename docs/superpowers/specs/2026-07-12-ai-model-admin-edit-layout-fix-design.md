# AI 模型后台编辑与表格布局修复设计

## 目标

修复 AI 模型后台点击“编辑”后未展示当前模型真实配置的问题，并调整模型与 Endpoint 列宽，使 Endpoint 完整可读。

## 已确认根因

- 编辑函数在 Modal 打开前调用 `form.setFieldsValue()`。
- Modal 使用 `destroyOnClose`，关闭后表单字段已经卸载，因此写入的数据在重新挂载时丢失。
- Endpoint 列设置了 `ellipsis: true`，并被表格压缩到约 225px。
- 模型列没有固定宽度，同样占用约 225px，超过实际需要。

## 修复方案

### 编辑弹窗

- 给 Modal 增加 `forceRender`，保证 Form 在第一次编辑前已经挂载。
- 打开新增或编辑弹窗时先执行 `form.resetFields()`，再写入当前行数据。
- 编辑时填充模型名、Endpoint、说明、启用状态和默认状态。
- API Key 输入框保持为空；空值表示保留当前数据库密钥，不将明文密钥返回前端。
- 关闭弹窗时重置表单，避免新增和编辑之间残留数据。

### 表格布局

- 模型列固定为 140px。
- Endpoint 列固定为足以完整显示当前地址的宽度，取消 `ellipsis`。
- Endpoint 使用不换行文本显示。
- 表格设置横向滚动最小宽度，窄屏时滚动而不是压缩或截断 Endpoint。

## 测试与验证

- 前端源代码回归检查确认 Modal 使用 `forceRender`，且不再使用 `destroyOnClose`。
- 检查模型列宽、Endpoint 列宽和横向滚动配置。
- 浏览器点击“编辑”，确认模型名、Endpoint、说明和两个开关与表格数据一致。
- 浏览器确认 API Key 仍为空。
- 在 1140px 和宽屏视口确认 Endpoint 完整显示，模型列明显收窄。
- 运行 `npm test`、`npm run build` 和 `git diff --check`。

## 不在本次范围

- 不修改后端模型配置接口或密钥策略。
- 不显示完整 API Key。
- 不重做后台页面视觉体系。

