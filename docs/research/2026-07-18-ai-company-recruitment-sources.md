# AI 公司官方招聘源接入调研

调研日期：2026-07-18

目标：为 OfferLens 增加 DeepSeek、Kimi（月之暗面）、智谱 AI、MiniMax 的官方岗位数据，并明确真实接口、招聘类型、数据质量、分类映射和实现风险。

## 结论摘要

| 优先级 | 公司 | 官方招聘源 | 当前真实岗位快照 | 建议开放类型 | 接入结论 |
| --- | --- | --- | ---: | --- | --- |
| P0 | DeepSeek | [DeepSeek 人才官网](https://talent.deepseek.com/) / [官方 Moka 门户](https://app.mokahr.com/social-recruitment/high-flyer/140576#/) | 36 | 社招；可从标题识别少量实习 | 可立即接入，直接读取 Moka 比人才官网静态快照更新 |
| P0 | Kimi（月之暗面） | [Kimi Careers](https://careers.kimi.com/) / [社招门户](https://app.mokahr.com/apply/moonshot/148506#/jobs) / [校招与实习门户](https://app.mokahr.com/campus-recruitment/moonshot/148507#/) | 社招 96；校招门户 72 | 校招、实习、社招 | 可立即接入，岗位详情完整 |
| P0 | 智谱 AI | [智谱加入我们](https://www.zhipuai.cn/zh/joinus) / [社招门户](https://app.mokahr.com/social-recruitment/zphz/148983?locale=zh-CN#/) / [校招门户](https://app.mokahr.com/campus-recruitment/zphz/148984#/home) | 社招门户 143；校招门户 36 | 校招、实习、社招 | 可立即接入；按门户和 `commitment` 组合映射三种招聘类型 |
| P1 | MiniMax | [MiniMax Careers](https://www.minimaxi.com/careers) / [社招门户](https://vrfi1sk8a0.jobs.feishu.cn/index/) / [校招门户](https://vrfi1sk8a0.jobs.feishu.cn/379481/) | 社招门户 197；校招门户 82 | 校招、实习、社招 | 数据完整，但飞书列表请求依赖动态 `_signature`，应作为独立适配器并设置失败保护 |

推荐分两阶段：第一阶段用一个轻量 Moka 请求助手接入前三家；第二阶段单独接入 MiniMax。现有统一 `JobPosting` 已能承载这些字段，不需要新增数据库字段或依赖。

> 岗位数是调研当天调用官方接口得到的实时快照，会随招聘上下线变化，不应写成固定业务规则。

## 调研方法与可信边界

- 只使用公司官网、官网加载的前端脚本和公司官方 ATS 域名，不使用聚合招聘站、搜索摘要或第三方数据集。
- 岗位数量、字段完整率和分类分布来自调研当天对官方 ATS 列表逐页读取后的去重统计。
- “可立即接入”“建议优先级”是基于接口稳定性、字段质量和当前项目结构作出的工程判断，不是公司官方承诺。
- 本文验证的是岗位列表与详情读取，不涉及简历投递；申请流程中的登录、验证码和隐私授权不在抓取范围内。

## 共用的 Moka 接入机制

DeepSeek、Kimi 和智谱均从各自官网跳转到 `app.mokahr.com`。三个来源可以共享很小的请求与解密助手，但公司配置、招聘类型映射和岗位标准化仍由各自适配器负责。

### 启动信息

访问官方门户页面后，解析：

```html
<input id="init-data" value="...JSON...">
```

其中包含 `orgId`、`siteId`、门户模式、筛选聚合、首屏岗位和 `aesIv`。

### 岗位列表

```http
POST https://app.mokahr.com/api/outer/ats-apply/website/jobs/v2
Content-Type: application/json
```

```json
{
  "orgId": "moonshot",
  "siteId": 148506,
  "limit": 30,
  "offset": 0,
  "needStat": false,
  "site": "social",
  "locale": "zh_cn"
}
```

### 岗位详情

```http
POST https://app.mokahr.com/api/outer/ats-apply/website/job
Content-Type: application/json
```

```json
{
  "orgId": "moonshot",
  "jobId": "<官方岗位 UUID>",
  "siteId": 148506,
  "locale": "zh_cn"
}
```

### 响应解密

列表与详情响应包含 Base64 密文 `data` 和 16 字符 `necromancer`。已验证的解密方式：

- AES-128-CBC；
- key：`necromancer` 的 UTF-8 字节；
- IV：门户初始化数据中的 `aesIv`；
- PKCS#7 去填充。

项目已经依赖 `cryptography`，无需增加新依赖。请求列表和详情不需要登录或验证码；投递环节的验证码逻辑与岗位读取无关。

### 字段标准化

| Moka 字段 | `JobPosting` 字段 | 处理建议 |
| --- | --- | --- |
| 岗位 UUID | `source_job_id` | 保留原始 UUID |
| `title` | `title` | 原样保存 |
| `zhineng` | `category` / `official_taxonomy` | 官方职能质量因公司而异，原值必须保留 |
| `department` / `deptId` | `business_unit` | 详情优先，列表 ID 作为追溯信息 |
| `locations` / 地址 | `location` / `country` | 将英文区县名标准化为中文城市；多地点保留 |
| `commitment` | `employment_type` / 招聘类型判断 | 智谱区分实习最可靠的字段 |
| `jobDescription` | `description` + `requirements` | 保留完整 HTML/文本，并按“岗位职责/任职要求”等标题拆分 |
| 完整原始对象 | `raw_data` | 保存，便于重新分类和追溯 |

Moka 将职责和要求合并在 `jobDescription`。拆分时不能因未识别到标题就丢弃岗位：识别成功则分别写入；识别失败时保留完整正文，并采用可追溯的回退值满足现有详情质量检查。

## DeepSeek

### 官方来源和实时数据

[DeepSeek 官网](https://deepseek.com/) 的“加入我们”指向 [DeepSeek 人才官网](https://talent.deepseek.com/)，人才官网再以官方岗位详情链接连接到 [Moka 门户](https://app.mokahr.com/social-recruitment/high-flyer/140576#/)。Moka 配置为：

- `orgId=high-flyer`
- `siteId=140576`
- `site=social`

调研当天，DeepSeek 人才官网静态数据为 33 条，而 Moka 门户实时返回 36 条；因此抓取源应以 Moka 为准，人才官网可用于入口校验。

36 条岗位均有 `jobDescription`。主要官方职能分布为：全栈开发/算法 8、模型数据策略 5、深度学习研究员 4、运维 4、AI 核心系统研发 4，其余为产品和职能岗位。标题中明确出现两类混合岗位：`Agent Harness 研究员（实习/全职）` 和 `Agent Harness 研发工程师（全职/实习）`。

### 招聘类型映射

- 稳妥默认：只声明 `social`。
- 如果产品希望露出实习：同时声明 `intern`，仅将标题明确包含“实习”的岗位映射为实习；这两条岗位仍同时含“全职”，前端应显示“实习/全职”，不能假装是纯实习岗位。
- 当前没有从官方入口验证到独立校招门户，不建议声明 `campus`。

### 分类建议

官方职能较细但偏研究组织语义，应保留在 `official_taxonomy`；一级岗位类别和二级方向继续使用项目统一分类。AI 岗位可根据标题和正文进一步落入：大模型/算法研究、AI 应用、AI Infra/系统、数据与训练、模型安全/评测。

## Kimi（月之暗面）

### 官方来源和实时数据

[月之暗面官网](https://www.moonshot.cn/) 链接到 [Kimi Careers](https://careers.kimi.com/)。官方 Careers 前端配置的招聘地址为 [Moka 门户](https://app.mokahr.com/apply/moonshot/148506#/jobs)：

- `orgId=moonshot`
- `siteId=148506`
- `site=social`

社招门户调研当天共 96 条去重岗位，96/96 均有完整 `jobDescription`，并且全部为全职。官方职能分布：技术类 48、市场类 12、运营类 9、算法类 9、产品类 7、职能类 4、设计类 2、管理类 1，另有少量其他分类。

官网菜单中的“校招&实习职位”短链指向独立的 [siteId 148507](https://app.mokahr.com/campus-recruitment/moonshot/148507#/)；实施复核时该门户为 72 条岗位，正文均完整。ATS 的 `commitment` 显示 14 条全职、58 条实习，但其中 9 条“全职”岗位的标题明确写有“实习生”；按结构化字段与标题共同校正后，本次发布为校招 5 条、实习 67 条。岗位数量会随官网实时变化。

### 招聘类型映射

- `social`：siteId 148506 的全部岗位。
- `campus`：siteId 148507，且 `commitment != 实习`、标题不含“实习”。
- `intern`：siteId 148507，且 `commitment == 实习`或标题明确包含“实习”。

### 分类建议

官方“技术类/算法类”可以作为一级分类证据，二级技术方向仍由标题和 JD 推断。详情中的部门字段可辅助识别 Android、后端、基础设施、模型算法等方向，但不要把部门名直接当统一岗位族。

## 智谱 AI

### 官方来源和实时数据

[智谱加入我们](https://www.zhipuai.cn/zh/joinus) 明确提供社会招聘和校园招聘，并链接至两个官方 Moka 门户：

- 社招：[siteId 148983](https://app.mokahr.com/social-recruitment/zphz/148983?locale=zh-CN#/)，实时 143 条；
- 校招：[siteId 148984](https://app.mokahr.com/campus-recruitment/zphz/148984#/home)，实时 36 条；
- 两者 `orgId` 均为 `zphz`。

实时明细：

| 门户 | 全职 | 实习 | 正文非空 |
| --- | ---: | ---: | ---: |
| 社招门户 | 107 | 36 | 140/143 |
| 校招门户 | 15 | 21 | 36/36 |

两个门户的岗位 ID 无重复。因此实习不是单独门户，而是散布在社招和校招门户中。

### 招聘类型映射

- `social`：社招门户且 `commitment != 实习`、标题不含“实习”；
- `campus`：校招门户且 `commitment != 实习`、标题不含“实习”；
- `intern`：两个门户中所有 `commitment == 实习` 或标题明确包含“实习”的岗位并集。

这一规则同时利用官方门户语义和岗位实际用工类型，避免把校招门户里的实习误标为正式校招，也避免漏掉社招门户里的日常实习。

### 分类建议

官方页面展示算法/研发、销售、产品/项目、运营等入口，但 ATS 中大量岗位的 `zhineng` 为“其他”或为空。统一二级分类不能依赖 `zhineng` 单字段，必须结合标题、职责、要求；原始官方分类仍需保存在 `official_taxonomy` 和 `raw_data` 中。

## MiniMax

### 官方来源和招聘项目

[MiniMax Careers](https://www.minimaxi.com/careers) 明确展示 Top Talent、2027 届校园招聘、2028 届实习/日常实习和社会招聘，并跳转至官方飞书招聘门户：

- 社招/全部岗位：[index](https://vrfi1sk8a0.jobs.feishu.cn/index/)
- 校招/项目岗位：[379481](https://vrfi1sk8a0.jobs.feishu.cn/379481/)
- 官方前端中可见的项目 ID：Top Talent `7496820276634634537`、校园招聘 `7495675705720965415`、实习项目 `7352753013591755047` 和 `7572193079274801454`。

调研当天的实时数据：

| 门户 | 岗位数 | 类型分布 | 正文质量 |
| --- | ---: | --- | --- |
| `index` | 197 | 全职 188、顾问 1、实习 4、外包 4 | 职责 197/197；要求 191/197 |
| `379481` | 82 | 实习 57、正式 25 | 职责 82/82；要求 81/82 |

由此可映射为：社招 193 条（`index` 非实习）、校招 25 条（`379481` 正式）、实习 61 条（两个门户实习并集）。这些是当前快照，不是固定配额。

### 真实 API

官方飞书招聘前端使用：

```http
POST /api/v1/search/job/posts?_signature=<官方前端动态签名>
GET  /api/v1/job/posts/{id}?_signature=<官方前端动态签名>
GET  /api/v1/config/job/filters/{portal_type}?_signature=<官方前端动态签名>
POST /api/v1/csrf/token/
```

列表请求体包含：`keyword`、`limit`、`offset`、`job_category_id_list`、`tag_id_list`、`location_code_list`、`subject_id_list`、`recruitment_id_list`、`portal_type=6`、`job_function_id_list`、`storefront_id_list`、`portal_entrance=1`。

必须带上门户对应的 `website-path`（`index` 或 `379481`）、`Portal-Channel: saas-career`、`Portal-Platform: pc`，并先获取 CSRF token/cookie。岗位详情原生分开提供 `description` 和 `requirement`，数据结构比 Moka 更适合直接标准化。

### 动态签名风险

列表和详情请求的 `_signature` 由官方飞书前端 bundle 中的混淆模块运行时生成。调研中通过执行该官方模块成功请求了全部列表和详情，但它不是稳定公开 API：bundle 或签名算法更新后，纯 Python 复刻可能失效。

因此不建议使用浏览器自动化抓取，也不建议把当前混淆代码大段复制进业务模块。实施时建议：

1. 使用独立 MiniMax 适配器，隔离 CSRF、签名和飞书字段映射；
2. 若决定上线，可由后端以受控 Node 子进程加载官方签名模块，设置超时和输出大小限制；
3. 刷新失败、结果骤降或详情完整率不达标时，禁止切换 `is_latest`，继续展示上一成功版本；
4. 为签名失效提供明确错误信息，便于只修 MiniMax，不影响其他招聘源。

这使 MiniMax 适合作为 P1，而不是与三个 Moka 来源绑在同一次改造中。

## 与现有项目的最小改造边界

现有统一模型已经覆盖公司、标题、官方分类、岗位族、地点、业务部门、招聘类型、职责、要求、详情链接和原始数据，见 `niuke_mianjing_backend/crawler/recruitment/models.py:7`。适配器注册集中在 `niuke_mianjing_backend/crawler/recruitment/registry.py:5`，来源元数据在 `niuke_mianjing_backend/api/routes/recruitment.py:66`，前端来源 Logo 映射在 `niuke-mianjing-frontend/src/constants/recruitment.ts:12`。

建议最小变更：

- 在现有官网适配器模块内增加一个私有 Moka 请求/解密助手和三个小配置适配器，不抽象通用 ATS 框架；
- DeepSeek：`source=deepseek`，优先开放 `social`，是否开放 `intern` 取决于是否接受混合职位；
- Kimi：建议 `source=kimi`、公司名 `Kimi（月之暗面）`，开放 `campus/intern/social`；
- 智谱：建议 `source=zhipu`，开放 `campus/intern/social`；
- MiniMax：建议 `source=minimax`，开放 `campus/intern/social`，放入独立文件；
- 同步后端注册表、`SOURCE_META`、前端来源常量和 Logo；项目现有资源已有 DeepSeek、智谱、MiniMax 图标，Kimi 需要补官方品牌资源；
- 不新增数据库字段，不修改岗位落库版本机制，不引入新的 Python 加密依赖。

## 分类和 AI 分析建议

四家公司都不应直接把官方分类等同于 OfferLens 二级分类。统一处理顺序：

1. 保留 `category`、`official_taxonomy`、部门和完整 `raw_data`；
2. 一级分类沿用现有技术、产品、运营、市场、设计、职能等体系；
3. 技术类结合标题和 JD 推断二级方向，AI 重点覆盖大模型/算法研究、AI 应用、AI Infra/系统、数据与训练、模型安全/评测；
4. 招聘类型先用门户语义和结构化 `commitment/recruit_type`，标题只作为 DeepSeek 混合岗位等例外补充；
5. 地点显示优先使用城市，区县和多地信息保留在原始数据中。

这既能适配不同公司的官方分类，又不会因 AI 岗位热度把所有“算法/研发”粗暴合并为一个方向。

## 接入验收标准

每家公司完成适配后，应实际刷新一次并检查：

- 列表总数与官方页面/接口同一时刻的统计相近，分页后 `source_job_id` 无重复；
- `source_url` 可打开官方岗位详情，不指向第三方聚合站；
- 标题、地点、招聘类型、职责、要求和官方分类均有代表性样本核对；
- DeepSeek/Kimi 详情正文非空率应接近 100%；智谱允许少量官网原始空正文但须记录；MiniMax 职责和要求完整率不得明显低于本次快照；
- 智谱三种招聘类型严格按两个门户和 `commitment` 拆分，实习岗位不重复；
- MiniMax 刷新失败或岗位数异常下降时不切换最新版本；
- 前端公司筛选、招聘类型、Logo、岗位卡片和二级分类均能正常显示；
- 随机抽取每家公司至少 5 条岗位，对照官网标题、地点、职责、要求和链接。

## 已验证事实与工程推断

已验证事实：官网到 ATS 的链接关系、门户参数、实时岗位数量、接口路径、请求字段、响应字段、正文完整率、智谱的门户/用工类型分布、MiniMax 的 CSRF 和动态签名要求。

工程推断：P0/P1 优先级、Moka 助手的代码放置、DeepSeek 混合岗位是否同时暴露为实习、MiniMax 使用受控 Node 子进程、统一二级分类策略和质量阈值。实施时可根据产品希望一次上线四家还是先保证稳定性，在这些推断项上调整；不应改变前述官方数据事实。
