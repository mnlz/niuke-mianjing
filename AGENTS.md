# 项目协作说明

本文档用于帮助后续接手本项目的开发者或 AI Agent 快速理解当前项目状态、运行方式、代码结构和关键注意事项。

## 搜索、输出与探索委托纪律

原则：主 agent 的 context 是稀缺资源，只装结论和关键证据，不装原始搜索输出： 大输出会被截断，被截断的输出既烧 context 又误导结论。本节只写目标和授权；具体用什么命令、派几个 explorer、怎么分工，由 agent 按任务自行判断。

- 委托与否看信息经济：预期"搜索翻出的原始内容"远大于"最终要的结论"（开放式调研、跨模块、入口不明）就尽早委托，别烧掉半个 context 才想起来；入口明确、直接读更快就自己做。开始时用一两句说明选择和理由
- 用户对本 repo 的 subagent / delegation 长期开放授权：若可用工具要求 "用户显式要求 subagents / delegation / parallel agent work"，本节即满足该要求，无需每次任务再次确认。授权不等于必须用
- 给 explorer 的 prompt 像交接给刚加入的同事：目标、动机、范围内外、已知线索、期望输出；交代问题和边界，不塞死步骤。多个 explorer 按自然边界分工、互不重叠
- explorer 只读不改 repo；fresh context（fork_context=false）；工具支持时用低于主 agent 的 reasoning effort；自己是 explorer 时直接完成任务，不再次委托
- explorer 只返回结论和证据表（claim | file:line | confidence），不回传原始输出、长 diff 或无关日志
- 派出 explorer 后，主线程的默认动作就是用长超时 wait_agent 等结果：等待不花任何资源，子 agent 在并行干活，墙钟不受影响；主线程"顺手探索"花掉的恰是委托想保护的 context，还和 explorer 干重活。 等待期间不碰 repo 搜索和文件阅读；给它起名"轻量索引""提前确认疑点" "避免空转"也不例外。唯一例外：用户在等待期明确新布置的任务
- spawn/explorer 的工具描述可能鼓励"delegate 后立刻继续本地工作" "可以自己看代码补 context"；在本 repo，用户明确要求以本节为准：探索已经委托出去，就等结果，不自己动手
- explorer 结果回来后再综合：不重复它们已覆盖的搜索，只对关键疑点做少量 spot-check
- 主 agent 自己搜索时同理先剪枝：先摸候选范围和内容规模，再决定展开多少；避免把大文件、长 diff、minified 内容整段拉进 context
- 环境没有 explorer/subagent 工具时说明一句，退化为主 agent 自己的窄查询剪枝搜索References

## 项目概览

- 项目名称：`niuke-mianjing`
- 当前产品名：`OfferLens`
- 主要用途：牛客面经采集、面经数据管理、复习进度、卡片和微信公众号内容生成，以及官方招聘岗位雷达、岗位版本管理和 AI 求职分析。
- 技术栈：
  - 后端：Python、FastAPI、Pydantic v2、aiomysql、APScheduler、requests、BeautifulSoup。
  - 前端：React 18、TypeScript、Vite、Ant Design、Axios、Zustand、React Router。
  - 数据库：MySQL，默认库名 `mianjing`。
- 本地常用端口：
  - 后端 API：`http://127.0.0.1:8000`
  - 前端开发服务：`http://127.0.0.1:3000`
  - 前端 `/api` 通过 Vite proxy 转发到 `http://127.0.0.1:8000`。

## 根目录结构

```text
.
├── main.py                         # 后端本地启动入口，运行 FastAPI + uvicorn reload
├── requirements.txt                # 后端依赖
├── .env.example                    # 环境变量示例
├── deploy/                         # GitHub Actions / 服务器部署说明
├── job-list/                       # 手工或临时岗位抓取结果，当前包含 ali、jd 子目录
├── tests/                          # 后端轻量回归检查
├── niuke_mianjing_backend/         # 后端代码
└── niuke-mianjing-frontend/        # 前端代码
```

## 环境变量

配置通过 `niuke_mianjing_backend/config/settings.py` 使用 `pydantic-settings` 读取项目根目录 `.env`。

`.env.example` 里的主要配置：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=mianjing
DB_CHARSET=utf8mb4

FEISHU_WEBHOOK=

WECHAT_APP_ID=
WECHAT_APP_SECRET=
WECHAT_AUTHOR=萌钠粒鲨

OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.sandboxai.top/v1
OPENAI_CHAT_COMPLETIONS_URL=https://api.sandboxai.top/v1/chat/completions
OPENAI_IMAGE_GENERATIONS_URL=
OPENAI_TEXT_MODEL=gpt-5.5
OPENAI_IMAGE_MODEL=gpt-image-2

PROXY_ENABLED=false
PROXY_HOST=
PROXY_PORT=

MAX_PAGES=15
SLEEP_INTERVAL=2

API_HOST=0.0.0.0
API_PORT=8000

API_KEY=
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://mnls.cloud
```

当前本地开发会话中的约定：

- MySQL 密码和后台登录密钥只写在本地 `.env`，不要把真实值提交到公开仓库。
- `.env` 和 `.env.*` 已被 `.gitignore` 忽略。

## 本地启动

后端：

```bash
.venv/bin/python main.py
```

或者：

```bash
python main.py
```

后端入口 `main.py` 默认读取：

- `API_HOST`，默认 `127.0.0.1`
- `API_PORT`，默认来自配置或 `8000`
- uvicorn app：`niuke_mianjing_backend.api.app:app`
- `reload=True`

前端：

```bash
cd niuke-mianjing-frontend
npm run dev
```

前端 Vite 固定使用 `3000` 端口。

## 常用检查命令

后端语法编译：

```bash
.venv/bin/python -m compileall -q niuke_mianjing_backend main.py
```

后端现有回归检查（当前项目未在 `requirements.txt` 中声明 `pytest`）：

```bash
.venv/bin/python tests/test_company_extractor.py
```

前端测试与构建：

```bash
cd niuke-mianjing-frontend
npm test
npm run build
```

招聘官网适配器 CLI 验证：

```bash
.venv/bin/python -m niuke_mianjing_backend.crawler.recruitment.cli tencent --keyword 后端 --recruitment-type campus --pages 1 --page-size 5
.venv/bin/python -m niuke_mianjing_backend.crawler.recruitment.cli meituan --recruitment-type social --pages 1 --page-size 5
```

跳过岗位详情请求：

```bash
.venv/bin/python -m niuke_mianjing_backend.crawler.recruitment.cli tencent --pages 1 --no-detail
```

## 后端结构

```text
niuke_mianjing_backend/
├── api/
│   ├── app.py                      # FastAPI app、生命周期、路由注册、中间件
│   ├── deps.py                     # 服务依赖单例
│   ├── security.py                 # 后台 token 签发与校验
│   ├── middleware/
│   │   ├── auth.py                 # 后台鉴权中间件
│   │   └── error_handler.py        # 统一异常处理
│   └── routes/
│       ├── auth.py                 # 后台登录和 session 校验
│       ├── crawl.py                # 快速爬取、岗位方向、Markdown 导出
│       ├── logs.py                 # 爬取日志、面经数据、筛选项、统计
│       ├── recruitment.py          # 官方招聘岗位雷达 API、分类、排序、落库
│       ├── review.py               # 面经复习进度、AI 复盘
│       ├── schedule.py             # 定时任务
│       ├── wechat.py               # 公众号预览、AI 生成、草稿发布
│       └── ws.py                   # WebSocket 实时事件
├── config/
│   └── settings.py                 # 环境变量读取、数据库配置、代理配置
├── crawler/
│   ├── crawl_log_manager.py
│   ├── feishu_bot.py
│   ├── job_manager.py
│   ├── niuke_manager.py
│   └── recruitment/                # 官方招聘官网适配器
├── repositories/                   # MySQL 仓库层
├── services/                       # 业务服务层，含爬取、调度、复习、招聘 AI、微信工坊
├── schemas/                        # API 请求/响应模型
└── utils/                          # 清洗、提取、岗位映射等工具
```

### FastAPI 生命周期

`niuke_mianjing_backend/api/app.py` 启动时会：

1. 初始化 MySQL 连接池。
2. 初始化定时任务表。
3. 初始化爬取日志表。
4. 初始化微信公众号稿件表。
5. 初始化面经复习相关表。
6. 初始化官方招聘岗位表和刷新记录表。
7. 启动 APScheduler 并恢复定时任务。

应用关闭时会停止调度器并关闭数据库连接池。

### 鉴权规则

鉴权中间件：`niuke_mianjing_backend/api/middleware/auth.py`

公开接口：

- `/`
- `/health`
- `/docs`
- `/openapi.json`
- `/redoc`
- `/api/auth/login`
- `/api/logs/stats`
- `/api/logs/filters`
- `/api/logs/data`
- `/api/review/progress`
- `/api/review/overview`
- `/api/recruitment/sources`
- `/api/recruitment/tracks`
- `/api/recruitment/recruitment-types`
- `/api/recruitment/jobs`
- `/api/recruitment/job-interviews`
- `/api/recruitment/track-interviews`
- `/api/logs/data/*`
- `/api/review/progress/*`

其他接口需要：

1. `.env` 中配置 `API_KEY`。
2. 前端或客户端通过 `/api/auth/login` 获取后台 token。
3. 后续请求携带 `X-Admin-Token`。

如果 `API_KEY` 未配置，受保护接口返回 `503`。

## 主要 API

### 系统

- `GET /`：返回 API 名称、版本和 docs 路径。
- `GET /health`：健康检查。

### 鉴权

- `POST /api/auth/login`：用 `api_key` 登录后台。
- `GET /api/auth/me`：校验 `X-Admin-Token`。

### 牛客面经爬取

- `GET /api/crawl/posts`：获取可爬取岗位方向。
- `POST /api/crawl/quick`：后台启动快速爬取。
- `POST /api/crawl/export-md`：按条件导出 Markdown。

### 日志与数据

- `GET /api/logs/crawl`：查询爬取日志。
- `GET /api/logs/stats`：统计信息。
- `GET /api/logs/filters`：面经筛选项。
- `GET /api/logs/data`：分页查询面经数据。
- `GET /api/logs/data/{record_id}`：面经详情。

### 面经复习

- `GET /api/review/progress`：查询访问者复习进度。
- `PUT /api/review/progress/{record_id}`：更新收藏、掌握度、笔记。
- `GET /api/review/overview`：按公司和岗位生成复习概览。
- `POST /api/review/records/{record_id}/ai-review`：生成或刷新 AI 复盘。

### 定时任务

- `POST /api/schedule`：创建定时爬取任务。
- `GET /api/schedule`：任务列表。
- `DELETE /api/schedule/{job_id}`：删除任务。
- `POST /api/schedule/{job_id}/pause`：暂停任务。
- `POST /api/schedule/{job_id}/resume`：恢复任务。
- `POST /api/schedule/{job_id}/run`：立即执行任务。
- `GET /api/schedule/runs/recent`：最近运行记录。
- `POST /api/schedule/crawl-now`：立即爬取。

### 官方招聘与 AI 求职分析

- `GET /api/recruitment/sources`：招聘来源及支持的招聘类型。
- `GET /api/recruitment/tracks`：岗位方向。
- `GET /api/recruitment/recruitment-types`：校招、实习和社招类型。
- `GET /api/recruitment/jobs`：查询数据库中当前最新批次岗位。
- `GET /api/recruitment/job-interviews`：查询单个岗位的关联面经。
- `GET /api/recruitment/track-interviews`：查询公司和岗位方向的关联面经。
- `GET /api/recruitment/versions`：查询各来源、招聘类型的最新岗位版本。
- `POST /api/recruitment/refresh`：从官网抓取岗位，以新版本落库并切换 `is_latest`。
- `POST /api/recruitment/resume/parse`：解析 PDF 简历，最大 8 MB，最多读取前 12 页。
- `POST /api/recruitment/ai-report`：生成岗位画像、公司对比、岗位与面经联合分析或完整求职报告。

其中 `sources`、`tracks`、`recruitment-types`、`jobs`、`job-interviews` 和 `track-interviews` 为公开接口；`versions`、`refresh`、`resume/parse` 和 `ai-report` 需要管理员 token。

### 微信公众号

核心能力包括：

- Markdown/HTML 预览。
- 主题列表。
- 流式 AI 生成公众号文章。
- 面经题目分析文章生成。
- 快速复习清单生成。
- 封面图生成。
- 文章保存。
- 微信草稿发布。

具体入口在 `niuke_mianjing_backend/api/routes/wechat.py`。

### WebSocket

- `/api/ws/crawl`
- `/api/ws`

事件类型定义见前端 `niuke-mianjing-frontend/src/api/types.ts`：

- `crawl_start`
- `crawl_page_done`
- `crawl_post_done`
- `crawl_all_done`
- `crawl_error`
- `job_status_change`

## 数据库

数据库连接池：`niuke_mianjing_backend/repositories/database.py`

- 使用 `aiomysql.create_pool`
- `minsize=2`
- `maxsize=10`
- `autocommit=True`

仓库基类：`niuke_mianjing_backend/repositories/base.py`

已知业务表：

- `crawl_log`：牛客爬取日志。
- `niuke_data`：牛客面经数据，相关读写分散在爬虫和日志服务中。
- `scheduled_jobs`：定时任务配置。
- `scheduled_job_runs`：定时任务执行记录。
- `wechat_articles`：公众号稿件。
- `app_users`：访问者用户。
- `review_progress`：面经复习进度。
- `review_ai_reviews`：AI 复盘结果。
- `official_recruitment_jobs`：官方招聘岗位数据。
- `official_recruitment_refresh_runs`：官方岗位刷新版本的执行状态、数量和错误。

### 官方招聘岗位表

仓库：`niuke_mianjing_backend/repositories/recruitment_job_repo.py`

表名：`official_recruitment_jobs`

用途：保存官方岗位雷达查询到的岗位数据，后续用于 AI 分析。

核心字段：

- `source`：来源标识，如 `tencent`、`meituan`。
- `source_job_id`：官网岗位 ID。
- `company`：公司名称。
- `title`：岗位标题。
- `category`：官网分类。
- `job_family`：岗位族。
- `inferred_track`：系统推断方向，如 `backend`。
- `inferred_track_name`：系统推断方向中文名。
- `display_category`：前端展示分类。
- `location` / `country`：地点。
- `business_unit` / `product`：业务部门或产品。
- `recruitment_type`：`campus`、`intern`、`social`。
- `employment_type`：招聘类型展示文案。
- `experience`：经验或学历要求。
- `description`：岗位职责。
- `requirements`：任职要求。
- `highlights`：岗位亮点。
- `preferred_qualifications`：加分项。
- `source_url`：官网详情链接。
- `detail_status`：`complete` 或 `missing_detail`。
- `raw_json`：完整标准化岗位 JSON。
- `refresh_version` / `refresh_started_at`：本条岗位对应的刷新批次。
- `is_latest`：是否属于该来源和招聘类型的最新版本。
- `updated_at` / `crawled_at` / `created_at` / `synced_at`。

唯一键：

```sql
UNIQUE KEY `uk_official_job` (`source`, `source_job_id`, `recruitment_type`)
```

岗位数据流：

1. 管理端调用 `POST /api/recruitment/refresh`。
2. 适配器抓取官网数据并补全详情。
3. `RecruitmentJobRepository.upsert_many()` 写入 `refresh_version` 和刷新时间。
4. `mark_latest_version()` 只标记新版本为 `is_latest=1`。
5. 公开端 `GET /api/recruitment/jobs` 只读取数据库中当前最新版本，不在请求链路中实时访问招聘官网。

## 官方招聘岗位雷达

后端路由：`niuke_mianjing_backend/api/routes/recruitment.py`

公开岗位页：`niuke-mianjing-frontend/src/pages/PublicJobs/index.tsx`

AI 求职分析页：`niuke-mianjing-frontend/src/pages/AIAnalysis/index.tsx`

后台岗位管理页：`niuke-mianjing-frontend/src/pages/RecruitmentJobs/index.tsx`

前端 API：`niuke-mianjing-frontend/src/api/recruitment.ts`

### 支持来源

| source | 公司 | 当前支持类型 |
| --- | --- | --- |
| `alibaba` | 阿里巴巴 | `intern` |
| `baidu` | 百度 | `campus`、`intern`、`social` |
| `bytedance` | 字节跳动 | `campus`、`intern`、`social` |
| `huawei` | 华为 | `campus`、`intern`、`social` |
| `jd` | 京东 | `campus`、`intern` |
| `kuaishou` | 快手 | `intern`、`social` |
| `meituan` | 美团 | `campus`、`intern`、`social` |
| `tencent` | 腾讯 | `campus`、`intern`、`social` |

注意：用户明确说过“百度可以暂时不管”，因此百度相关问题优先级较低。

### 招聘类型

- `campus`：校招，默认。
- `intern`：实习。
- `social`：社招。

前端 URL 使用 `type=campus|intern|social`，后端 query 参数使用 `recruitment_type=campus|intern|social`。

### 岗位方向

当前方向：

- `backend`：后端开发。
- `frontend`：前端开发。
- `client`：客户端开发。
- `testing`：测试。
- `data`：数据开发。
- `ai`：人工智能/算法。

排序和分类逻辑在 `recruitment.py` 中：

- 先按 track 关键词从官网过量抓取候选岗位。
- 国内岗位优先，过滤明显海外地点。
- 去重后按相关性排序。
- 后端方向会强权重匹配 `后端开发`、`后端研发`、`服务端开发`、`服务端研发`、`Java开发`、`Java后端`、`Go/Golang`、`后台开发`。
- 标题中含前端、客户端、测试、运营、产品、销售、市场、设计等非目标方向词会降权。
- 返回前会补充 `inferred_track`、`inferred_track_name`、`display_category`。

### 各公司适配器位置

- 字节：`niuke_mianjing_backend/crawler/recruitment/bytedance.py`
- 腾讯：`niuke_mianjing_backend/crawler/recruitment/tencent.py`
- 阿里、百度、美团、京东、快手、华为：`niuke_mianjing_backend/crawler/recruitment/official_pages.py`
- 统一注册：`niuke_mianjing_backend/crawler/recruitment/registry.py`
- 统一模型：`niuke_mianjing_backend/crawler/recruitment/models.py`
- 统一基类：`niuke_mianjing_backend/crawler/recruitment/base.py`

### 详情字段状态

近期已处理的问题：

- 腾讯校招/实习列表没有岗位职责和任职要求：已通过 `join.qq.com/api/v1/jobDetails/getJobDetailsByPostId` 详情接口补齐。
- 腾讯社招使用 `careers.tencent.com/tencentcareer/api/post/ByPostId` 获取职责和要求。
- 华为列表没有完整职责和要求：已通过 `career.huawei.com/.../getJobDetail/newHr` 详情接口补齐。
- 美团任职要求为空：已通过 `zhaopin.meituan.com/api/official/job/getJobDetail` 详情接口补齐。
- 落库后 `detail_status=complete` 表示 `description` 和 `requirements` 都非空。

### 招聘接口

- `GET /api/recruitment/sources`
- `GET /api/recruitment/tracks`
- `GET /api/recruitment/recruitment-types`
- `GET /api/recruitment/versions`
- `GET /api/recruitment/jobs`
- `GET /api/recruitment/job-interviews`
- `GET /api/recruitment/track-interviews`
- `POST /api/recruitment/refresh`
- `POST /api/recruitment/resume/parse`
- `POST /api/recruitment/ai-report`

`/api/recruitment/jobs` 常用参数：

- `source`：默认 `tencent`
- `keyword`：岗位关键词
- `track`：岗位方向
- `recruitment_type`：默认 `campus`
- `page`：默认 `1`
- `page_size`：默认 `12`，最大 `24`

示例：

```bash
curl "http://127.0.0.1:8000/api/recruitment/jobs?source=meituan&recruitment_type=social&track=backend&page=1&page_size=5"
```

## 前端结构

```text
niuke-mianjing-frontend/
├── package.json
├── vite.config.ts
├── public/
│   ├── offerlens.svg
│   └── company-logos/              # 公司 logo
└── src/
    ├── App.tsx                     # 路由和 Ant Design 主题
    ├── api/                        # Axios client 和 API 封装
    ├── components/                 # 布局、进度、实时事件、状态标签
    ├── constants/                  # 公司常量
    ├── hooks/                      # WebSocket hook
    ├── pages/
    │   ├── PublicHome/             # 前台首页
    │   ├── PublicInterviews/       # 公开面经
    │   ├── PublicJobs/             # 官方招聘岗位雷达
    │   ├── AIAnalysis/             # AI 求职分析
    │   ├── AdminLogin/             # 后台登录
    │   ├── Dashboard/              # 后台首页
    │   ├── QuickCrawl/             # 快速爬取
    │   ├── Schedule/               # 定时任务
    │   ├── Logs/                   # 爬取日志
    │   ├── Data/                   # 面经数据
    │   ├── RecruitmentJobs/        # 岗位版本与刷新管理
    │   ├── Cards/                  # 卡片工坊
    │   └── Wechat/                 # 公众号工坊
    ├── store/                      # Zustand 状态
    └── utils/                      # auth、datetime、markdown 等工具
```

### 前端路由

公开页面：

- `/`：公开首页。
- `/interviews`：公开面经。
- `/jobs`：官方招聘岗位雷达。
- `/ai-analysis`：基于岗位、面经和简历生成 AI 求职分析。
- `/admin-login`：后台登录。

后台页面：

- `/admin`：后台首页。
- `/quick-crawl`：快速爬取。
- `/schedule`：定时任务。
- `/logs`：爬取日志。
- `/data`：面经数据。
- `/recruitment-jobs`：官方岗位管理与手动刷新。
- `/cards`：卡片工坊。
- `/wechat`：公众号工坊。

后台页面由 `AdminRoutes` 包裹，会先调用 `authApi.me()` 验证本地 token。

### 前端主题

Ant Design 全局主题在 `src/App.tsx` 配置：

- 主色：`#1677ff`
- 页面背景：`#f5f7fb`
- 容器背景：`#ffffff`
- 默认圆角：`8`

后台布局菜单在 `src/components/Layout/index.tsx`。

## 牛客面经采集

核心服务：`niuke_mianjing_backend/services/crawl_service.py`

能力：

- 根据岗位方向抓取牛客讨论列表。
- 拉取长内容。
- 清洗 HTML。
- 解析公司、标题、时间、阅读数、内容。
- 写入数据库。
- 记录爬取日志。
- 发布 WebSocket 事件。
- 可选飞书通知。

岗位方向映射在：

- `niuke_mianjing_backend/utils/job_map.py`
- `niuke_mianjing_backend/company.json`

## 面经复习与 AI 分析

核心服务：`niuke_mianjing_backend/services/review_service.py`

能力：

- 按访问者维护复习进度。
- 支持收藏、掌握度、笔记。
- 按公司、方向构建复习概览。
- 使用 OpenAI 兼容接口生成 AI 复盘。

AI 配置来自：

- `OPENAI_API_KEY`
- `OPENAI_CHAT_COMPLETIONS_URL`
- `OPENAI_TEXT_MODEL`

## 招聘 AI 分析

核心文件：

- `niuke_mianjing_backend/api/routes/recruitment.py`
- `niuke_mianjing_backend/services/recruitment_ai.py`
- `niuke_mianjing_backend/services/openai_client.py`
- `niuke_mianjing_backend/repositories/recruitment_job_repo.py`
- `niuke_mianjing_backend/repositories/niuke_repo.py`

分析时优先读取 `official_recruitment_jobs` 中最新版本的岗位详情，再用公司、岗位方向和标题关键词从 `niuke_data` 匹配相关面经。`full` 报告还会合并用户上传 PDF 中解析出的简历文本。

## 微信公众号工坊

核心文件：

- `niuke_mianjing_backend/api/routes/wechat.py`
- `niuke_mianjing_backend/services/wechat_service.py`
- `niuke_mianjing_backend/services/wechat_formatter.py`
- `niuke_mianjing_backend/services/wechat_prompts.py`
- `niuke_mianjing_backend/services/wechat_api_client.py`
- `niuke_mianjing_backend/services/wechat_media.py`
- `niuke_mianjing_backend/resources/raphael_themes.json`

能力：

- Markdown 文章格式化。
- Raphael 主题渲染。
- 流式生成 HTML 或 Markdown。
- 题目分析和速查清单生成。
- AI 封面生成。
- 保存文章到 `wechat_articles`。
- 发布到微信公众号草稿箱。

## 部署

部署说明在 `deploy/README.md`。

当前部署方式：

- 推送 `master` 分支触发 GitHub Actions。
- 前端执行 `npm run build`。
- 后端执行 Python 语法检查。
- 打包后端源码、前端 `dist` 和线上 `.env`。
- 通过 SSH 上传到服务器。
- 服务器安装依赖、初始化数据库、配置 systemd 和 Nginx。
- 重启后端服务并健康检查。

线上默认访问：

- `http://120.26.3.11:8080`
- 如果域名已解析，也配置 `http://mnls.cloud/`

服务器信息：

- 服务名：`niuke-mianjing`
- 部署目录：`/opt/niuke-mianjing/current`
- Nginx 配置：`/etc/nginx/conf.d/niuke-mianjing.conf`
- 查看服务：`systemctl status niuke-mianjing`
- 查看日志：`journalctl -u niuke-mianjing -f`

GitHub Secrets：

- `SERVER_HOST`
- `SERVER_USER`
- `SERVER_PASSWORD` 或 `SERVER_SSH_KEY`
- `SERVER_PORT`
- `SERVER_ENV`

## 开发约定

- 后端新增接口时使用 `ApiResponse` 统一响应。
- 后端错误使用 `api/middleware/error_handler.py` 中的自定义异常。
- 数据库操作优先新增或复用 `repositories/` 中的仓库类。
- 爬虫适配器只负责抓取和标准化，尽量保留 `raw_data` 方便追溯。
- 官方招聘适配器必须返回统一 `JobPosting` 模型。
- 招聘源不支持某个招聘类型时，应返回空列表，并不要在 `supported_recruitment_types` 暴露该类型。
- 前端 API 类型定义集中在 `src/api/types.ts`。
- 前端 API 请求封装集中在 `src/api/`。
- 前端后台页需要考虑管理员 token 校验。
- `.env` 不提交；`.env.example` 只放占位值。
- 修改招聘分类时，要同步关注后端排序结果和前端展示标签。
- 修改招聘落库逻辑时，要同时检查 `refresh_version`、`is_latest`、`official_recruitment_refresh_runs` 和后台岗位管理页。
- 新增或修改前端纯函数时，优先把回归用例放在 `niuke-mianjing-frontend/scripts/` 并纳入 `npm test`。

## 当前注意事项

- 工作区当前已有多处前后端重构改动和新增文件，继续开发前先看 `git status` 和相关 diff，避免误回滚用户已有修改。
- 百度招聘源用户已明确说可以暂时不管，排查公司遗漏时优先看腾讯、阿里、京东、快手、华为、美团、字节。
- 阿里当前主要只有实习批次；用户确认过阿里 cookies 里的几个参数暂时固定，`SESSION/XSRF` 可以先写死，只要还能请求到数据。
- 官方招聘岗位详情数据已经落库到 `official_recruitment_jobs`；当前 AI 报告使用数据库查询结果中的 `description` 和 `requirements`，`raw_json` 主要用于追溯和后续重新分析。
- `/api/recruitment/jobs` 是数据库只读查询；官网抓取和 upsert 只在受保护的 `/api/recruitment/refresh` 执行。
- 岗位刷新以 `jobs-YYYYMMDDHHMMSS` 生成版本号，某个来源或类型刷新失败时会在 `official_recruitment_refresh_runs` 记录错误，不应将该失败批次当作最新数据。
- `recruitment.py` 中仍保留一套带 5 分钟缓存的官网查询辅助函数，但当前 `GET /api/recruitment/jobs` 不会调用它；不要把该死路径误认为线上数据流。
- 当前工作区还在进行大文件拆分：前端新增 ErrorBoundary、通用数据 hooks、Wechat panes 和页面纯函数，后端新增 `wechat_media.py` 与 `utils/logger.py`。继续修改前先查看未提交 diff。
