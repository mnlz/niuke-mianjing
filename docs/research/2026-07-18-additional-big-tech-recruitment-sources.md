# 更多大厂官方招聘数据源调研

> 调研快照：2026-07-18（Asia/Shanghai）
> 范围：拼多多、小米、小红书、滴滴、网易、OPPO、vivo、哔哩哔哩
> 证据标准：只使用企业官方招聘页面、官方接口和官方页面加载的一方 JavaScript；岗位数量是调研时点快照，不应作为长期固定值。

## 结论摘要

建议分三阶段扩充数据源：

| 优先级 | 数据源 | 建议首期范围 | 调研时可见规模 | 主要理由 | 主要风险 |
| --- | --- | --- | ---: | --- | --- |
| P0 | 拼多多 | 校招 | 22 | 用户明确优先；列表和详情字段完整；无需登录 | 社招接口有验证码/风控，首期不要接 |
| P0 | 小米 | 社招、校招、实习 | 全站 2,617 | 单一公开接口覆盖量大，列表直接带完整职责和要求 | 招聘类型筛选有交叉，统计不能简单相加 |
| P0 | 小红书 | 社招、校招、实习 | 社招 876；校招 333；实习 255 | API 干净，`jobType` 粒度高，大模型/算法岗位识别价值高 | 校招与实习存在包含关系 |
| P1 | 网易 | 社招、日常实习；精选校招项目 | 社招 2,044；日常实习 414 | 数据量大、分类细、JD 完整 | 社招和校招是两套门户；校招还按项目分散 |
| P1 | 滴滴 | 社招 | 1,080 | 分类标准、接口公开，覆盖量较大 | 列表无完整 JD，每个岗位需再请求详情 |
| P1 | vivo | 社招 | 689 | 社招接口稳定、无需登录 | 职责和要求合并在一个字段；校招为另一套平台 |
| P1 | OPPO | 社招、校招 | 社招 105；校招 236 | 两端接口均公开，字段完整 | 两个域名、两套模型，需要独立适配 |
| 暂缓 | 哔哩哔哩 | 暂不接 | 未可靠取得 | 官网有职位接口 | 接口要求页面生成的 `ajSessionId`，定时任务稳定性差 |

最小可行接入顺序：

1. 拼多多校招。
2. 小米全招聘类型。
3. 小红书全招聘类型。
4. 滴滴社招与网易社招/日常实习。
5. vivo 社招、OPPO 社招与校招。
6. 拼多多社招、vivo 校招、滴滴校招、B 站等存在会话或风控的数据源另行攻克。

前三个 P0 来源即可新增约 3,000+ 条公开岗位候选，并显著补强 AI、大模型、算法和互联网产品岗位覆盖。该估算按各接口当前总量粗略计算，未扣除招聘类型交叉、重复职位和国内岗位过滤。

## 对现有数据模型的影响

现有 `JobPosting` 已具备接入这些来源所需的核心字段：

- 基础字段：公司、标题、地点、部门/产品、招聘类型、职责、要求、详情 URL。
- 官网分类：`official_taxonomy`。
- 统一分类：`role_group`、`role_family`、`specialties`。
- 分析增强：`business_domains`、`tech_stack`、`classification_meta`。

因此首期不需要新增数据库字段，也不需要先设计新的通用爬虫框架。每个适配器只需完成：

1. 官网分类原样写入 `official_taxonomy`。
2. 复用现有统一分类器生成一级岗位组、二级岗位族和专业标签。
3. 保留官方返回到 `raw_data`，便于以后重新分类。
4. 将官网项目、招聘类型或用工性质映射到现有 `campus`、`intern`、`social`。

建议等至少接入 2–3 个新来源、确认重复模式后，再考虑抽象新的基类；当前直接沿用现有适配器约定更简单。

## P0：首批接入

### 1. 拼多多（PDD）

#### 官方入口

- [拼多多校园招聘](https://careers.pddglobalhr.com/campus/grad)
- [拼多多社会招聘](https://careers.pddglobalhr.com/jobs)

#### 校招接口与数据

- 列表：`POST https://careers.pddglobalhr.com/api/careers/api/recruit/position/list`
- 请求体示例：`{"page":1,"pageSize":20}`
- 详情：`POST https://careers.pddglobalhr.com/api/careers/api/recruit/position/detail`
- 请求体示例：`{"id":"岗位 ID"}`
- 分类：`POST https://careers.pddglobalhr.com/api/careers/api/recruit/position/detail/type`
- 分页字段：`page`、`pageSize`；响应为 `result.list`、`result.total`。
- 调研时未附加筛选的毕业生岗位总数：22。
- 无需登录、Cookie 或签名；普通 JSON 请求即可。

列表已提供：

- `id`、`name`、`code`
- `workLocation`、`workLocationName`
- `job`、`jobName`
- `releaseTime`、`jobDuty`
- `labelList`、`recruitTypeName`、`graduationYear`

详情补充：

- `serveRequirement`：任职要求
- `jobDuty`：岗位职责
- `bonus`：加分项
- 招聘批次、招聘类型、毕业年份等信息

官网一级分类为：设计、职能、运营、语言、市场营销、产品、技术、视觉类、区域业务。它适合作为 `official_taxonomy`，二级岗位族继续依据标题、职责和要求由现有分类器推断。

#### 实习和社招风险

实习使用另一组接口：

- `POST .../api/recruit/position/train/list`
- `POST .../api/recruit/position/detail/train/type`

未附加官网活动短链参数 `t` 时，实习列表返回 0。这里不能据此判断“当前没有实习岗位”，更可能是活动/短链作用域限制。因此首期不应依赖无作用域的实习总数。

社招公开字典类接口可用：

- 分类：`POST https://careers.pddglobalhr.com/api/recruit/job/query/list`
- 最新职位：`POST https://careers.pddglobalhr.com/api/recruit/position/latest_list`
- 地点：`POST https://careers.pddglobalhr.com/api/recruit/position/workLocation/list`

社招分类包括：技术、产品、市场营销、招商运营、平台管理、综合、客服、区域业务、语言、商务、视觉设计、其他。

但社招主列表和详情接口当前会返回错误码 `400023`，页面脚本把这些请求包装在验证码/风险校验流程中。定时刷新若直接接入，容易出现间歇失败或需要人工验证。

#### 接入建议

- 首期只接校招毕业生列表和详情。
- 使用独立 `pdd.py`，为以后加入实习短链上下文和社招风控逻辑留出边界。
- 社招不要用浏览器自动化作为默认采集链路；等确认稳定的公开请求上下文后再接。
- 难度：校招低；实习中；社招高。

### 2. 小米

#### 官方入口

- [小米招聘机会页](https://hr.xiaomi.com/website/opportunities.html)
- [小米校园招聘](https://hr.xiaomi.com/campus/)
- [小米社会招聘](https://hr.xiaomi.com/job)
- [机会页官方脚本](https://hr.xiaomi.com/website/assets/js/jobs.js)

#### 接口与数据

统一接口：

`GET https://hr.xiaomi.com/website/api/agent/searchJobPage`

主要参数：

- `keyword`
- `cityZhNames`
- `pageNum`
- `pageSize`
- 招聘项目类型参数，官方脚本映射为：1 社招、2 校招、3 实习、4 顶尖人才。

无需登录、Cookie 或特殊请求头。调研时：

- 全站总数：2,617
- 社招筛选：1,900
- 校招筛选：184
- 实习筛选：533
- 顶尖人才筛选：162

筛选数量之和高于全站总数，说明岗位可能同时属于多个项目类型，统计页不能直接相加。

列表直接返回完整分析所需字段：

- `id`、`title`
- `cityZhNames`
- `levelOneDeptName`
- `description`、`requirement`
- `expectedJobLevel`
- `publishTime`
- `larkJobCode`、`jobId`、`jobPostId`
- `type`、`url`

无需逐岗位请求详情即可获得职责和要求，是新增来源中成本最低、覆盖量最大的一个。

#### 官方分类

小米校招页公开分类包括：

- 软件研发类、算法类、测试类、运维类、硬件研发类
- 产品类、运营类、服务类、供应链类
- 外语外派类、设计类、市场类、销售类、职能类
- 交付类、生产制造类

API 未稳定提供同等细度的二级分类。接入时可将官方项目类型和页面分类保留到 `official_taxonomy`，再依据标题、部门、职责和要求生成统一二级岗位族。

#### 接入建议

- 一次实现覆盖社招、校招和实习。
- 适合用一个轻量适配器沿用 `OfficialSearchPageAdapter` 的约定，不需要新抽象。
- `url` 可直接作为岗位来源链接。
- 对跨项目岗位继续依赖现有唯一键和去重规则，避免将相同岗位重复落库。
- 难度：低。

### 3. 小红书

#### 官方入口

- [小红书招聘官网](https://job.xiaohongshu.com/)
- [官方岗位详情示例](https://job.xiaohongshu.com/social/position/18875)
- [招聘站官方脚本](https://fe-static.xhscdn.com/formula-static/ats-website/public/js/main.8305ae7.js)

#### 接口与数据

列表：

`POST https://job.xiaohongshu.com/websiterecruit/position/pageQueryPosition`

请求体示例：

```json
{"recruitType":"social","pageNum":1,"pageSize":10}
```

`recruitType` 可使用 `social`、`campus`、`intern`。无需登录、Cookie 或特殊请求头。调研时：

- 社招：876
- 校招：333
- 实习：255

校招项目集合包含实习子集，校招与实习数量不能相加作为独立总量。

响应 `data` 提供 `pageNum`、`pageSize`、`total`、`totalPage` 和 `list`。列表已包含：

- `positionId`、`positionName`
- `workplaceIds`、`workplace`
- `publishTime`、`recruitStatus`
- `duty`、`qualification`
- `jobType`、`jobProjectName`
- `labels`

详情：

`GET https://job.xiaohongshu.com/websiterecruit/position/queryPositionDetail?positionId={id}`

详情还提供 `positionType`、`workNature`、`recruitType`、工作经验、学历和招聘项目等字段。

接口当前会把较大的 `pageSize` 规范回 10，适配器应按返回的页码和总页数迭代，不假设请求值一定生效。

#### 分类价值

`jobType` 粒度高，实际值包括“大模型”“后端开发”“基础后端”“行业销售”等。建议：

- `jobType` 原样进入 `official_taxonomy`。
- 直接作为统一 `role_family` 和 `specialties` 的强证据。
- “大模型”等类型同时写入 AI 热门标签，方便 `/jobs?ai_hot=1` 精准筛选。
- 一级 `role_group` 仍由统一映射生成，避免小红书官网粒度与其他公司不一致。

#### 接入建议

- 一次接入社招、校招和实习。
- 列表已经带完整职责和要求，通常无需为每条职位请求详情；详情仅用于补充学历、经验、工作性质时按需获取。
- 可先使用轻量适配器；若后续需要招聘项目、标签等更多差异逻辑，再拆成独立文件。
- 难度：低。

## P1：第二批接入

### 4. 网易

#### 官方入口

- [网易校园招聘](https://campus.163.com/)
- [网易社会招聘与日常实习](https://hr.163.com/job-list.html?workType=1)
- [校招站官方脚本](https://campus.163.com/static/js/main.991a98d7.js)

网易需要按两套门户处理，不建议强行做成一个请求模板。

#### 社招与日常实习

列表：

`POST https://hr.163.com/api/hr163/position/queryPage`

请求体示例：

```json
{"pageNo":1,"pageSize":10,"workType":0}
```

调研时已确认：

- `workType=0`：社会招聘，2,044
- `workType=1`：日常实习，414
- `workType=2`：57，但官网含义未充分验证，不应擅自映射

列表已提供完整字段：

- `id`、`name`、`workType`
- `firstPostTypeName`
- `recruitNum`
- `requirement`、`description`
- `reqEducationName`、`reqWorkYearsName`
- `firstDepName`
- `workPlaceList`、`workPlaceNameList`
- `updateTime`
- `product`、`productName`
- `geekPassionateTalentFlag`、`beeUrl`

详情：

`GET https://hr.163.com/api/hr163/position/query?id={id}`

分类：

`GET https://hr.163.com/api/hr163/options/positionType/queryItemList`

官网分类很细：技术、游戏策划、游戏程序、游戏艺术、游戏测试、产品、人工智能、运营、用户体验及设计、项目管理、市场、销售、内容、客服、电商、职能支持、高管、教育、企业服务、其他。

其中“人工智能”可直接成为 AI 热门强证据；游戏策划、程序、美术、测试应分别映射到不同二级岗位族，而不是统一归为“游戏”。

#### 校招项目

项目导航：

`GET https://campus.163.com/api/campuspc/project/navigation/list`

调研时公开项目包括：

- 项目 69：网易互联网 2026 校招，9 个岗位
- 项目 75：蛋仔派对 AI 实习专项，5 个岗位
- 项目 76：智邮 27 届精英实习，3 个岗位

项目岗位列表：

`GET https://campus.163.com/api/campuspc/position/getJobList?projectId={projectId}&pageNo=1&pageSize=10`

列表已包含 `positionName`、`positionTypeName`、工作地、面试城市、`positionDescription`、`positionRequirement`、热门标签和更新时间。详情接口为：

`GET https://campus.163.com/api/campuspc/position/getJobDetails`

校招项目可能跳转到不同的官方子域名，因此采集前应先枚举导航，不要把项目 ID 写死成唯一入口。

#### 接入建议

- 先接社招和 `workType=1` 日常实习。
- 校招按“导航 → 项目 → 岗位”抓取，只选择当前有效的官方项目。
- 使用独立 `netease.py`，隔离社招与校招门户差异。
- 难度：社招低；校招中。

### 5. 滴滴

#### 官方入口

- [滴滴招聘官网](https://talent.didiglobal.com/?PageIndex=1)
- [滴滴社会招聘](https://talent.didiglobal.com/social/list/1)
- [官方岗位详情示例](https://talent.didiglobal.com/social/p/63396)
- [招聘站官方脚本](https://talent.didiglobal.com/static/js/main.77dbb079.js)

#### 社招接口与数据

列表：

`GET https://talent.didiglobal.com/recruit-portal-service/api/job/front/list`

无需登录、Cookie 或特殊请求头。调研时社会招聘总数为 1,080。

列表字段：

- `jdId`、`jdNo`
- `workArea`
- `deptName`
- `jobType`
- `jobName`
- `refreshTime`

列表中的职责和要求为空，需要逐岗位获取详情：

`GET https://talent.didiglobal.com/recruit-portal-service/api/job/front/view/{jdId}`

详情提供：

- `jobDesc`、`qualification`
- `jobName`、`deptName`
- `publishTime`、`refreshTime`
- `recruitType`、`workArea`
- `recruitNum`、`jobType`、`labelCode`

分类字典：

`GET https://talent.didiglobal.com/recruit-portal-service/api/job/jdpublish/confirm/listJdTypes`

分类为：技术、产品、运营、销售与客户服务、市场与公关、职能与支持、设计、安全、商业分析、战略、供应链。

地点字典：

`GET https://talent.didiglobal.com/recruit-portal-service/api/job/job_locations`

#### 校招风险与接入建议

校招位于独立入口 `https://campus.didiglobal.com/`。当前访问存在重定向/会话行为，并出现 `acw_tc` 等防护 Cookie，不适合和社招适配器一起匆忙接入。

- 首期只接社会招聘。
- 增量刷新时先比对 `jdId` 和 `refreshTime`，只为新增或更新岗位请求详情，降低详情请求量。
- 适合放入现有官方页面适配器模块；暂不需要独立框架。
- 难度：社招中；校招高。

### 6. vivo

#### 官方入口

- [vivo 社会招聘](https://hr.vivo.com/jobs)
- [vivo 校园招聘](https://hr.vivo.com/campus)
- [社招站官方脚本](https://hr.vivo.com/assets/useJobsRecommend.02a9ab82.js)

#### 社招接口与数据

列表：

`POST https://hr.vivo.com/api/social/webSite/portal/page`

请求体示例：

```json
{
  "city_code_list": [],
  "company_id": 1,
  "group_id": 1,
  "user_id": null,
  "job_category_id_list": [],
  "keyword": "",
  "max_results": 10,
  "page": 1,
  "yoe_list": []
}
```

无需登录或 Cookie。调研时社会招聘总数为 689。

列表字段：

- `job_id`、`job_code`、`job_title`
- `requirement_org_name`
- `degree_range_code`、`degree_range_name`
- `yoe_min`、`yoe_max`
- `job_location_list`
- `head_count`、`fuzzy_head_count`
- `job_desc`
- `job_category_id`、`job_category`
- `hot`、`publish_timestamp`

详情：

`POST https://hr.vivo.com/api/social/webSite/portal/job/detail`

请求体：`{"job_id":"岗位 ID"}`。

分类：

`POST https://hr.vivo.com/api/social/webSite/portal/jobCategory`

官网分类为：营销类、设计类、研发类、供应链类、品质类、公共类、产品运营类、制造类、市场类。响应虽然包含两层 ID，但子节点名称大多与父节点重复，不能当作有效的细分岗位族。

`job_desc` 把“工作职责”和“职位要求”合并在一个文本中。适配器应按标题分段；分段失败时保留全文并把 `detail_status` 标为需关注，不能丢掉原始文本。

#### 校招风险与接入建议

校招实际跳到独立的 `https://hr-campus.vivo.com/jobs`，使用另一套招聘平台。响应暴露了明确的频率限制和平台会话特征，需单独调研和适配。

- 首期只接社招。
- 使用独立 `vivo.py`，封装合并 JD 的拆分规则。
- 校招以后单独接，不与社招共用分页假设。
- 难度：社招中；校招高。

### 7. OPPO

#### 官方入口

- [OPPO 社会招聘](https://career.oppo.com/official/oppo/recruitment/post)
- [OPPO 校园招聘](https://careers.oppo.com/university/oppo/campus/post)
- [社招站官方脚本](https://career.oppo.com/assets/js/oppo-CgxPOmYN.js)
- [校招站官方脚本](https://careers.oppo.com/assets/js/campus_oppo-FkBjReNU.js)

所有已验证接口都需要请求头 `Tenant-Id: 1000`，但不需要登录 Token、Cookie 或签名。

#### 社招

列表：

`POST https://career.oppo.com/ats-candidate-api/open-api/position/queryPositionList`

请求体示例：

```json
{
  "pageNum": 1,
  "pageSize": 10,
  "publishName": "",
  "workCityCodeList": [],
  "jobTypeList": [],
  "recruitTypeList": ["SOCIAL-RECRUITMENT"],
  "shareId": ""
}
```

调研时社会招聘总数为 105。列表直接提供完整字段：

- `positionId`、`publishName`、`jobNo`、`jobCode`、`jobName`
- `workCityCode`、`workCityName`
- `jobType`
- `minWorkYears`、`maxWorkYears`
- `educationRequire`
- `jobDuty`、`workRequire`
- `publishDate`
- `recruitType`、`recruitTypeName`
- `unifiedName`、`jobDirectionList`

分类字典：

`GET https://career.oppo.com/ats-candidate-api/open-api/enum/dictionaries?dictTypes=JOB-TYPE`

分类为：软件类、硬件类、职能类、大数据类、测试类、设计类、产品及运营类、市场营销类、供应链及制造类、其他。

地点接口：

`POST https://career.oppo.com/ats-candidate-api/open-api/position/queryPositionCityList`

#### 校招

项目列表：

`GET https://careers.oppo.com/openapi/position/project/list`

调研时项目包括 Intern、Graduate、doctor。

岗位列表：

`POST https://careers.oppo.com/openapi/position/pageNew`

请求体示例：

```json
{
  "pageNum": 1,
  "pageSize": 10,
  "positionName": "",
  "projectList": [],
  "positionTypeList": [],
  "workCityCodeList": [],
  "shareId": ""
}
```

调研时校招站总数为 236。列表已带完整 `positionDesc`、`positionRequire`，并提供项目、招聘类型、职位类型、地点、人数、发布时间、专项招聘和 AI 能力等级等字段。

#### 接入建议

- 社招与校招都可以接，但要作为两套传输逻辑处理。
- 使用独立 `oppo.py`，共享 `Tenant-Id` 常量和标准化方法，不引入新的通用平台抽象。
- 校招项目名称可直接映射 `campus`、`intern`；doctor 保留为标签，不发明新的顶层招聘类型。
- `aiCapabilityLevel` 和 AI 相关 `jobDirectionList` 可作为 AI 热门筛选辅助证据。
- 难度：中。

## 暂缓来源

### 8. 哔哩哔哩

#### 官方入口和已确认接口

- [哔哩哔哩招聘官网](https://jobs.bilibili.com/)
- [哔哩哔哩官方招聘动态示例](https://www.bilibili.com/opus/965738076970156040)
- [招聘站官方脚本](https://s1.hdslb.com/bfs/static/zhaopin-toc/assets/js/app.6a8da9f3.js)

官方脚本中可以确认以下接口路径：

- 校招列表：`/api/campus/position/positionList`
- 校招详情：`/api/campus/position/detail`
- 校招城市：`/api/campus/position/cityList`
- 校招类别：`/api/campus/dict/post`
- 社招列表：`/api/srs/position/positionList`
- 社招详情：`/api/srs/position/detail`
- 社招城市：`/api/srs/position/cityList`

但直接 GET/POST 都返回：

```json
{"code":-101,"message":"ajSessionId不能为空"}
```

首页访问没有提供可直接复用的简单 Cookie，说明接口依赖页面生成的会话或风控上下文。当前无法可靠验证岗位总数、分页模型和字段结构。

官方招聘动态曾披露技术类、游戏类、内容类、产品运营类等六大类，但未在当前接口中验证完整分类，因此不应补全或固化为系统字典。

#### 接入建议

- 暂不纳入定时刷新。
- 不使用脆弱的浏览器自动化冒充稳定 API。
- 若业务强需求再专项分析 `ajSessionId` 的官方生成流程、有效期和频率限制，并采用独立适配器。
- 难度：高。

## 统一分类映射建议

各官网一级分类应保留原文，同时映射到现有统一一级岗位组。以下只是稳定的首层映射；二级岗位族仍由标题、JD 和官网细分类综合判断。

| 官网分类例子 | 统一一级岗位组 | 二级分类提示 |
| --- | --- | --- |
| 技术、研发、软件、大数据 | 技术 | 后端、前端、客户端、数据、AI、测试、运维、安全等 |
| 算法、人工智能、大模型、AI 能力方向 | 技术 | 优先进入 AI/算法，并加 AI 热门标签 |
| 硬件、品质、制造、供应链 | 技术或供应链/制造 | 硬件研发与生产制造不能混为一类 |
| 产品、产品及运营、产品运营 | 产品或运营 | 必须结合标题拆分产品经理、产品运营、用户运营等 |
| 运营、内容、电商、招商运营、平台管理 | 运营 | 内容、用户、商业化、电商、商家/招商等 |
| 市场、市场营销、市场与公关 | 市场营销 | 品牌、公关、增长、投放等 |
| 销售、商务、区域业务、行业销售 | 销售/商业 | 行业销售、渠道、商务拓展、客户成功等 |
| 设计、视觉、用户体验及设计、游戏艺术 | 设计 | UI/UX、视觉、交互、工业设计、游戏美术等 |
| 职能、综合、公共、职能支持 | 职能 | 人力、财务、法务、行政、战略等 |
| 游戏策划、游戏程序、游戏测试 | 按真实职能分组 | 分别映射策划/产品、技术开发、测试，不只打“游戏”标签 |

特别处理：

- “AI 热门”不应只看官网一级分类。标题、`jobType`、`jobDirectionList`、职责和要求中的大模型、LLM、多模态、推荐、搜索、机器学习、Agent 等都应计入。
- 同一岗位允许一个 `role_family` 加多个 `specialties`，例如“大模型平台后端”可归后端开发，同时包含大模型平台、AI Infra 标签。
- 官网只有宽泛一级分类时，不要制造“官方二级分类”；统一二级分类应明确标记为系统推断。

## 最小实施计划

### 第一阶段

1. 新增拼多多校招适配器。
2. 新增小米统一机会页适配器，覆盖社招、校招、实习。
3. 新增小红书适配器，覆盖社招、校招、实习。
4. 注册来源、公司名称、支持招聘类型和 Logo。
5. 为各来源各抓一批最新岗位，检查：
   - 标题、地点、部门、招聘类型是否正确。
   - 职责与要求是否完整。
   - 官网分类是否原样保存。
   - AI、大模型、后端、前端、客户端、测试、数据等关键岗位是否进入正确二级岗位族。
   - 同一官网岗位在招聘类型交叉时是否被错误重复展示。

### 第二阶段

1. 滴滴社招：列表后按增量请求详情。
2. 网易社招与日常实习；校招按导航动态枚举项目。
3. vivo 社招：增加合并 JD 的职责/要求拆分。
4. OPPO 社招与校招：固定公共 `Tenant-Id` 请求头，分别处理两个域名。

### 暂不做

- 拼多多社招验证码绕过。
- 用浏览器自动化维护 B 站 `ajSessionId`。
- 在只有一个来源需要时建立新的通用 ATS 框架。
- 为官网未提供的分类伪造“官方二级分类”。

## 验收口径

每个新来源刷新一个最新批次后，至少核对：

1. 接口声明的总数与分页抓取数量一致，或明确记录官网过滤造成的差异。
2. 抽查技术、产品、运营、设计、市场、职能各类岗位，一级映射无系统性偏差。
3. 抽查至少 10 个技术岗位，后端、前端、客户端、AI/算法、数据、测试、运维/安全等二级岗位族合理。
4. 所有 `detail_status=complete` 的记录同时具备非空职责和要求。
5. 官网岗位 URL 可打开，`raw_data` 可追溯原始分类、项目和招聘类型。
6. 对社招/校招/实习交叉数据做去重抽查。
7. 接口遇到风控或会话错误时，该批次标记失败，不切换为最新版本。

## 最终建议

首批不要追求“公司数量最多”，而应优先接入稳定、完整、能直接服务 AI 求职分析的数据源。拼多多校招满足明确业务优先级；小米带来最大覆盖量；小红书提供对 AI、大模型和细分技术岗位最有价值的官网类型。这三家完成后，再用网易和滴滴扩充岗位规模，最后补 vivo 与 OPPO。

拼多多社招和 B 站当前都存在明显风控/会话依赖。把它们留在后续专项，而不是用脆弱方案塞进日常定时刷新，能避免一次失败抓取污染最新岗位版本。
