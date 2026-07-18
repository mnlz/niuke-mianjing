# OfferLens 普通用户登录与访问控制设计

## 目标

为公开站点增加“邮箱 + 密码”的普通用户账户体系，并将面经收藏、复习进度、AI 报告生成和报告中心绑定到账号。管理员鉴权保持独立。

## 范围

### 普通用户账户

- 用户可使用邮箱和密码自助注册、登录、退出。
- 当前版本不发送验证邮件，不提供找回密码。
- 邮箱统一去除首尾空白并转为小写，数据库唯一。
- 密码最少 8 位，使用 Python 标准库 PBKDF2-HMAC-SHA256、随机盐和恒定时间比较。
- 用户 Token 有效期 30 天，通过 `X-User-Token` 传递。
- 用户 Token 使用从后台 `API_KEY` 派生的独立签名密钥，不能被管理员 Token 校验接受。

### 未登录访问

- 面经列表允许访问第 1、2 页；请求第 3 页及以后返回 `401`。
- 岗位列表允许访问第 1、2 页；请求第 3 页及以后返回 `401`。
- 面经和岗位的前两页详情保持可查看，公开分享链接不额外封锁。
- AI 分析首页和配置向导可查看。
- 点击生成 AI 报告或上传 PDF 简历时检查登录，未登录跳转登录页。
- 首页“查看报告示例”跳转 `/ai-analysis/sample-report`，展示固定假报告，不进入报告中心。
- 未登录点击收藏、修改掌握度或保存笔记时跳转登录页，不写匿名进度。

### 登录后能力

- 登录后可访问全部面经和岗位分页。
- 收藏、掌握度和笔记使用登录用户的 `app_users.id` 存储。
- AI 报告生成后立即写入 MySQL，并归属于当前用户。
- `/ai-analysis/reports` 仅登录可访问，按当前账号读取报告。
- 报告中心支持列表、查看单份报告和删除自己的报告。
- 用户无法读取或删除其他账号的报告。
- 当前浏览器 `localStorage` 中的旧报告和匿名收藏不迁移。

## 后端设计

### 数据库

扩展 `app_users`：

- `email VARCHAR(255) NULL`
- `password_hash VARCHAR(255) NULL`
- 邮箱唯一索引；原有 `visitor_key` 保留以兼容历史匿名数据。

新增 `ai_analysis_reports`：

- `id BIGINT AUTO_INCREMENT`
- `user_id BIGINT NOT NULL`
- `report_code VARCHAR(64) NOT NULL`
- `title VARCHAR(255) NOT NULL`
- `report_type VARCHAR(32) NOT NULL`
- `company VARCHAR(255)`
- `track VARCHAR(64)` / `track_name VARCHAR(128)`
- `recruitment_type VARCHAR(32)`
- `content MEDIUMTEXT NOT NULL`
- `model VARCHAR(128)`
- `created_at` / `updated_at`
- `report_code` 唯一，`user_id, created_at` 索引。

### API

普通用户鉴权：

- `POST /api/user-auth/register`
- `POST /api/user-auth/login`
- `GET /api/user-auth/me`

报告：

- `POST /api/recruitment/ai-report`：要求用户 Token，生成后保存并返回完整报告记录。
- `GET /api/recruitment/ai-reports`：返回当前用户的报告列表。
- `GET /api/recruitment/ai-reports/{report_code}`：只读取当前用户报告。
- `DELETE /api/recruitment/ai-reports/{report_code}`：只删除当前用户报告。

访问限制：

- `/api/logs/data` 在 `offset >= 24` 且无有效用户 Token 时返回 `401`。
- `/api/recruitment/jobs` 在 `page > 2` 且无有效用户 Token 时返回 `401`。
- `/api/review/progress` 的读取和更新要求用户 Token。
- `/api/review/overview` 和公开数据统计继续公开。

管理员中间件放行上述普通用户接口，再由路由依赖验证用户 Token；管理员 Token 不赋予普通用户数据身份。

## 前端设计

- 新增 `/login`，同页切换登录与注册，成功后返回来源页面。
- 请求拦截器同时发送 `X-Admin-Token` 和 `X-User-Token`，两者互不替代。
- 公共导航显示登录入口；登录后显示邮箱和退出操作。
- 面经、岗位翻到第 3 页时先检查用户登录。
- 收藏、掌握度、笔记、AI 生成和简历上传共用一个登录跳转方法。
- 新增公开 `/ai-analysis/sample-report`，复用报告 Markdown 展示样式和固定示例数据。
- 报告中心从服务端读取数据，移除 `localStorage` 作为正式数据源。
- `/ai-analysis/reports` 未登录时重定向 `/login`，并保留返回地址。

## 错误处理

- 重复邮箱注册返回 `409`。
- 邮箱或密码错误统一返回 `401`，不暴露邮箱是否存在。
- Token 缺失、过期或签名错误返回 `401`。
- 非本人报告统一返回 `404`，避免泄露报告存在性。
- 用户 Token 收到 `401` 时前端清理本地登录态并跳转登录；管理员 Token 处理保持原样。

## 测试与验收

- 单元测试覆盖密码散列、用户 Token、邮箱规范化和分页限制。
- API 测试覆盖注册、登录、账号隔离、报告归属、收藏登录限制。
- 前端测试覆盖登录跳转、公开页数判断和报告请求映射。
- 前端运行 `npm test`、`npm run build`。
- 后端运行 `pytest` 和 `compileall`。
- 浏览器验收：匿名前两页、第三页登录、注册登录、收藏、AI 示例、AI 生成登录检查、报告中心账号读取和退出。

## 明确不做

- 邮箱验证码、找回密码、第三方 OAuth、账号合并。
- 匿名收藏和浏览器旧报告迁移。
- 付费套餐、报告配额、管理用户后台。
