# 轻量 AI 模型注册表设计

## 目标

在不引入 LiteLLM、LangChain 或供应商 SDK 的前提下，扩展现有 OpenAI 兼容调用层，使 OfferLens 支持多个自定义 Endpoint、模型名和 API Key，并让用户在生成报告前选择真实可用的模型。

## 配置来源与优先级

模型配置同时来自两处：

1. `.env` 中的 `AI_MODELS_JSON`，用于部署默认值。
2. MySQL 表 `ai_model_configs`，用于后台在线新增和覆盖。

模型名是唯一业务标识。同名数据库记录覆盖 `.env` 记录。未配置 `AI_MODELS_JSON` 且数据库为空时，系统把现有 `OPENAI_TEXT_MODEL`、`OPENAI_CHAT_COMPLETIONS_URL`、`OPENAI_BASE_URL` 和 `OPENAI_API_KEY` 组装成一个兼容模型，保证现有功能继续工作。

示例：

```env
AI_MODELS_JSON='[{"model":"gpt-5.5","endpoint":"https://example.com/v1","api_key":"sk-example","description":"标准分析模型","enabled":true,"is_default":true}]'
```

## 模型字段

每个模型只保存实际需要的字段：

- `model`：真实上游模型名，同时作为前端展示名称和请求参数。
- `endpoint`：完整 Chat Completions 地址或 `/v1` Base URL。
- `api_key`：上游 API Key；数据库中只保存密文。
- `description`：用户选择模型时的简短说明。
- `enabled`：是否允许用户选择和调用。
- `is_default`：是否为默认模型；系统最多保留一个启用的默认模型。

不增加供应商、价格、能力标签、上下文窗口、负载均衡或自动降级字段。

## 密钥安全

新增 `AI_MODEL_SECRET_KEY` 环境变量，使用项目已有的 `cryptography` 对数据库 API Key 做 Fernet 加密。后台列表只返回掩码，不返回明文。创建或更新模型时，空 API Key 表示保留原密钥。

若未配置 `AI_MODEL_SECRET_KEY`，文件和旧版环境变量模型仍可读取，但后台禁止写入包含 API Key 的数据库配置，并返回明确错误。同名数据库覆盖未填写新 API Key 时，沿用环境变量中的 API Key；数据库中新建的模型必须提供 API Key。

## 后端结构

新增一个轻量模型仓库负责 `ai_model_configs` 建表与增删改查；新增一个模型注册服务负责：

- 读取和校验 `AI_MODELS_JSON`。
- 合并环境变量和数据库配置。
- 解析默认模型。
- 将 Base URL 规范化为 `/chat/completions`。
- 加密和解密数据库 API Key。
- 向公开接口输出无密钥的模型信息。

现有 `openai_client.post_chat_completion()` 增加可选 `model` 参数。调用时由注册服务解析该模型对应的 Endpoint 和 API Key；未传模型时使用默认模型。请求和响应继续使用现有 OpenAI Chat Completions 格式。

## API

公开接口：

- `GET /api/recruitment/ai-models`：返回启用模型的 `model`、`description`、`is_default`。

管理员接口：

- `GET /api/recruitment/admin/ai-models`：返回合并后的模型及来源、密钥掩码。
- `POST /api/recruitment/admin/ai-models`：创建数据库模型。
- `PUT /api/recruitment/admin/ai-models`：按请求体中的模型名更新数据库模型。
- `DELETE /api/recruitment/admin/ai-models?model=...`：删除数据库覆盖，删除后同名环境变量配置可重新生效。
- `POST /api/recruitment/admin/ai-models/test`：按请求体中的模型名向真实上游发送一个最小请求并返回耗时和成功状态，不返回密钥。

管理员接口沿用现有 `X-Admin-Token` 鉴权。

## 报告生成数据流

1. 创建报告页读取公开模型列表。
2. 默认选中 `is_default` 模型；没有默认值时选第一个启用模型。
3. 用户选择模型后，前端在报告请求中提交 `model`。
4. 后端确认模型存在且已启用，再生成报告。
5. `call_ai_report()` 把模型传给统一客户端。
6. 报告表继续使用现有 `model` 字段保存真实模型名。

前端不接收 Endpoint 或 API Key。

## 管理页面

新增独立的后台“AI 模型”页面，提供列表、新增、编辑、启停、设为默认、删除数据库配置和连接测试。环境变量模型可查看和测试，但必须先创建数据库覆盖才能在线修改。

## 错误处理

- 模型不存在或未启用：报告生成前返回 400。
- Endpoint 无效、密钥缺失或配置 JSON 无效：返回不包含密钥的配置错误。
- 上游超时、网络失败或非 2xx：沿用统一错误格式，截断响应内容。
- 连接测试失败：返回安全的失败原因，不记录请求头。
- 数据库不可用：保留环境变量模型作为读取兜底；不伪装后台写入成功。

## 测试与验证

自动测试覆盖：

- Endpoint 规范化。
- `.env`、数据库和旧配置的合并优先级。
- Fernet 加解密与掩码。
- 默认模型唯一性。
- 禁用和不存在模型拦截。
- API 输出不包含 API Key。
- 前端获取、默认选择并提交模型。

真实请求验证不进入默认离线测试链。提供一个显式集成测试入口，读取本地实际模型配置，向选定模型发送短提示词，断言 HTTP 成功且返回非空文本。开发验证阶段至少实际执行一次；测试输出只显示模型名、耗时和成功状态。

## 不在本次范围

- 自动降级、重试路由和负载均衡。
- Token 成本与账号额度计费。
- 非 OpenAI 兼容协议适配。
- 图片、音频和 Embedding 模型注册。
- API Key 轮换和密钥托管服务。
