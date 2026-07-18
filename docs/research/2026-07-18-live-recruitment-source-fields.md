# 8 家招聘官网实时字段核验与统一分类方案

> 核验时间：2026-07-18 14:43–14:50 CST
> 核验方式：直接运行仓库现有适配器，每个来源请求当前官网第一页（`page_size=1`，需要详情的来源开启 `include_detail=True`），只记录 HTTP 状态、响应结构、非敏感岗位字段和标准化结果。本文不记录 Cookie、签名、令牌、电话、邮箱或人员信息。官网数据会变化，数量是本次响应快照，不代表长期库存。

## 结论

8 个适配器在本次核验中都能收到官网 HTTP 200 响应；7 家返回了岗位，华为校招/实习当前返回空列表，但华为社招正常返回 4 个岗位并能取得详情。各公司不存在可直接对齐的“岗位分类字段”：有的给两级中文类目（字节、美团），有的只有粗类目（腾讯、百度），有的只给内部代码（快手），还有字段名像岗位族但语义其实是招聘批次（阿里的 `categoryType=internship`）。因此不能把各源某个同名或近似字段直接塞进统一 `role_family`。

可行方案是保留两层数据：

1. `category` / `job_family` 只保存官网原始分类语义，不能承担产品统一分类。
2. 独立生成统一分类：`role_group`（大类、单值）、`role_family`（面试体系、单值）、`specialties`、`business_domains`、`tech_stack`（多值），并保存来源字段路径、置信度和分类版本。

不用为每家公司增加数据库列，也不建议现在用 LLM 做主分类。每个适配器只需把可靠的官网类目提取到一个小型 `classification_meta` JSON，再用统一的标题/JD 规则补足缺失层级。

## 实时调用结果

| 来源 | 本次类型 | 列表/详情结果 | 本次总数 | 实际样例 | 是否必须补详情 | 官方接口与仓库证据 |
| --- | --- | --- | ---: | --- | --- | --- |
| 阿里巴巴 | 实习 | 3 个实习批次均 HTTP 200 | 790（批次合计，适配器再按岗位 ID 去重） | `AI应用研发工程师`；`categoryName=技术类`，`categoryType=internship` | 否；列表已含职责、要求 | [列表 API](https://campus-talent.alibaba.com/position/search)；[`official_pages.py:109-213`](../../niuke_mianjing_backend/crawler/recruitment/official_pages.py#L109-L213) |
| 百度 | 校招 | HTTP 200，`status=ok` | 158 | `北京-2027管培生`；`postType=综合`，`projectType=管培生项目` | 否；本次列表已含 `workContent/serviceCondition` | [列表 API](https://talent.baidu.com/httservice/getPostListNew)；[`official_pages.py:358-438`](../../niuke_mianjing_backend/crawler/recruitment/official_pages.py#L358-L438) |
| 字节跳动 | 校招 | HTTP 200，`code=0` | 217 | `…推荐模型建模（AI Infra）…`；官网类目 `研发 > 机器学习` | 否；列表 API 已含完整职责、要求和嵌套分类 | [列表 API](https://jobs.bytedance.com/api/v1/search/job/posts)；[`bytedance.py:7-117`](../../niuke_mianjing_backend/crawler/recruitment/bytedance.py#L7-L117) |
| 华为 | 社招 | 列表、详情均 HTTP 200 | 4 | `AI算子性能优化专家`；`jobFamilyName=研发族`，`jobSubcategory=J260312` | 建议；详情提供更多名称化字段，但必须与列表合并 | [列表 API](https://career.huawei.com/reccampportal/services/portal/portalpub/getJob/newHr/page/1/1)、[详情 API](https://career.huawei.com/reccampportal/services/portal/portalpub/getJobDetail/newHr)；[`official_pages.py:634-728`](../../niuke_mianjing_backend/crawler/recruitment/official_pages.py#L634-L728) |
| 京东 | 校招 | HTTP 200，`success=true` | 4 | `商务销售`；`jobCategory=销售类`，`jobDirection=一线销售方向` | 否；列表已含职责、要求 | [列表 API](https://campus.jd.com/api/wx/position/page)；[`official_pages.py:441-539`](../../niuke_mianjing_backend/crawler/recruitment/official_pages.py#L441-L539) |
| 快手 | 社招 | HTTP 200，`code` 成功 | 1,446 | `Java开发工程师（经营策略）-【商业化】`；岗位列表只返回 `positionCategoryCode=J0012` | 当前无详情调用；列表含职责、要求，分类名称可从官网标签字典解析 | [列表 API](https://zhaopin.kuaishou.cn/recruit/e/api/v1/open/positions/simple)、[标签 API](https://zhaopin.kuaishou.cn/recruit/e/api/v1/open/positions/label)；[`official_pages.py:542-631`](../../niuke_mianjing_backend/crawler/recruitment/official_pages.py#L542-L631) |
| 美团 | 校招 | 列表、详情均 HTTP 200，`status=0` | 68 | `…大模型数据抓取算法专家`；`jobFamily=技术类`，`jobFamilyGroup=算法` | 适配器当前补详情；本次列表也已有职责、要求，详情可作稳定兜底 | [列表 API](https://zhaopin.meituan.com/api/official/job/getJobList)、[详情 API](https://zhaopin.meituan.com/api/official/job/getJobDetail)；[`official_pages.py:216-327`](../../niuke_mianjing_backend/crawler/recruitment/official_pages.py#L216-L327) |
| 腾讯 | 校招 | 列表、详情均 HTTP 200，`status=0` | 96 | `软件开发-后台开发方向`；详情仅给粗类目 `tidName=技术` | **必须**；列表没有 `desc/request` | [校招列表 API](https://join.qq.com/api/v1/position/searchPosition)、[校招详情 API](https://join.qq.com/api/v1/jobDetails/getJobDetailsByPostId)；[`tencent.py:82-153`](../../niuke_mianjing_backend/crawler/recruitment/tencent.py#L82-L153) |
| 腾讯 | 社招 | 列表、详情均 HTTP 200，`Code=200` | 2,318 | `腾讯云-MaaS高级后台研发工程师`；`CategoryName=技术` | **必须**；列表有职责但没有完整要求，详情补 `Requirement/ImportantItem` | [社招列表 API](https://careers.tencent.com/tencentcareer/api/post/Query)、[社招详情 API](https://careers.tencent.com/tencentcareer/api/post/ByPostId)；[`tencent.py:39-80`](../../niuke_mianjing_backend/crawler/recruitment/tencent.py#L39-L80)、[`tencent.py:155-189`](../../niuke_mianjing_backend/crawler/recruitment/tencent.py#L155-L189) |

补充：华为 `campus` 和 `intern` 在同一时刻均返回 HTTP 200、`pageVO.totalRows=0`、`result=[]`；这应记录为“官网当前为空”，不能当成适配器网络失败。项目当前仍把华为三种招聘类型都声明为支持，见 [`recruitment.py:86-92`](../../niuke_mianjing_backend/api/routes/recruitment.py#L86-L92)。

## 官网响应结构与关键字段

| 来源 | 顶层/列表路径 | 单条岗位关键字段（本次真实返回） | 字段语义与风险 |
| --- | --- | --- | --- |
| 阿里巴巴 | `success, content, errorCode, errorMsg`；`content.datas[]` | `id, name, categoryName, categoryType, batchId, batchName, department, workLocations, description, requirement, degree, experience, circleNames, tags, publishTime, modifyTime` | `categoryName` 是粗岗位类；`categoryType=internship` 是招聘性质而非岗位族。`batchName` 是招聘项目，`circleNames` 更接近可投业务集合，不应当作当前岗位 BU。 |
| 百度 | `status, data`；`data.list[]` | `postId, jobId, name, postType, projectType, projectTypeCode, orgName, workPlace, workContent, serviceCondition, education, workYears, publishDate, updateDate` | `postType` 是粗类，`projectType` 是招聘项目（如管培生项目），两者都不足以稳定推导细岗位族。 |
| 字节跳动 | `code, data, error, message`；`data.job_post_list[]` | `id, code, title, description, requirement, job_category, city_info, department_id, recruit_type, job_subject, job_post_info, publish_time` | `job_category` 自带父子树，是 8 家里最可靠的岗位分类：本次为父级“研发”、子级“机器学习”。`recruit_type.parent` 才是校招/社招，子级“正式”是用工性质。`job_subject` 是招聘专题。 |
| 华为 | `pageVO, result[]`；详情直接返回岗位对象 | `jobId, jobname/nameCn, jobFamilyName, jobFamClsCode, jobSubcategory, jobClass, categoryName, deptName, jobArea/jobAddress, mainBusiness/mostlyDuty, demand/jobRequire, bonusPoints, degree, workYear, jobType`；详情另有 `jobSubcategoryName, jobClassName, jobFamilyName` | 列表同时有代码和中文族名；详情更适合取名称。但当前实现以详情对象完全替换列表对象，可能丢掉列表独有的 `bonusPoints` 等字段。列表还包含联系人字段，禁止整包持久化。 |
| 京东 | `success, body`；`body.items[]` | `publishId, reqId, positionName, jobCategory, jobCategoryCode, jobDirection, jobDirectionCode, positionDept, workCity, workContent, qualification, education, workYears, requirementVoList, reqTagList, planId, planName` | 当前样本中 `jobDirection` 是粗方向（如“技术方向”），`jobCategory` 是细类别（如“软件开发类”“数据与算法类”）；`planName` 是招聘计划。当前适配器只保存 `jobDirection`，丢掉了更有用的细类和标签。 |
| 快手 | `code, message, result`；`result.list[]` | `id, code, name, positionCategoryCode, positionClassCode, positionNatureCode, departmentCode, recruitProjectCode, workLocationCode, workExperienceCode, description, positionDemand, releaseTime` | 岗位列表对分类、部门、项目、经验主要只给内部代码；官网 `/positions/label` 可按招聘性质返回代码字典。本次真实映射包括 `J0012=工程类`、`J0011=算法类`、`J0005=产品类`、`J0004=运营类` 等。响应还含招聘负责人/流程类字段，禁止原样落库或对外返回。 |
| 美团 | `status, message, data`；`data.list[]`，详情在 `data` | `jobUnionId, name, jobFamily, jobFamilyGroup, jobSpecialCode, jobType, projectId, projectName, department[], cityList[], jobDuty, jobRequirement, workYear, tag, refreshTime` | `jobFamily=技术类` 是大类，`jobFamilyGroup=算法` 是细族，适合作为官网分类证据；`projectName` 是招聘项目。 |
| 腾讯校招 | `status, message, data`；`data.positionList[]` | 列表：`postId, positionTitle, positionFamily, position, bgs, projectName, recruitLabelName, workCities`；详情：`title, tid, tidName, desc, request, workCityList, projectName, techTagName, subDirectionId` | `positionFamily/tidName` 只有设计、技术、产品、市场、职能等粗类，细岗位族主要在标题“后台开发方向”等文本中；`bgs` 是可选事业群集合，不等于确定 BU。 |
| 腾讯社招 | `Code, Data`；`Data.Posts[]`，详情在 `Data` | 列表：`PostId, RecruitPostName, CategoryName, BGName, ProductName, LocationName, RequireWorkYearsName, Responsibility`；详情增加 `Requirement, ImportantItem, PostLightItem, DepartmentIntroduction` | `CategoryName=技术` 仍是粗类；`ProductName` 是产品/业务域，不是岗位族。细岗位族需从标题和 JD 判断。 |

统一模型的公共字段定义见 [`models.py:7-31`](../../niuke_mianjing_backend/crawler/recruitment/models.py#L7-L31)。上述实时结果说明，现有 `category`、`job_family` 的赋值在不同适配器间并不是同一语义，不能直接聚合统计。

## 列表与详情应如何合并

| 来源 | 当前行为 | 实际问题 | 最小修正 |
| --- | --- | --- | --- |
| 字节、阿里、百度、京东、快手 | 直接使用列表对象 | 本次职责和要求完整；快手岗位列表的分类只有代码 | 保持岗位单请求；快手每个招聘类型刷新前请求一次官方标签字典并缓存，以字典解析代码，不要为每条岗位重复请求。 |
| 美团 | 详情对象替换列表对象 | 当前样例两边字段近似，但接口未来可能各有独有字段 | `raw = {**list_item, **detail}`，详情优先。 |
| 华为 | 详情对象替换列表对象 | 已确认列表有 `bonusPoints`、联系人等详情未返回字段；分类名称也分散在两端 | `raw = {**list_item, **detail}`，随后只提取安全白名单字段；不要保存整包 raw。 |
| 腾讯校招 | `raw={列表字段, detail=详情对象}` | 信息完整，但标准化逻辑需要跨两层读 | 当前合并方式可保留；分类证据明确记录来自 `detail.tidName` 和标题。 |
| 腾讯社招 | 详情对象替换列表对象 | 详情补齐要求，但会放弃列表端独有字段 | `raw = {**list_item, **detail}`，详情优先。 |

## 真实可落地的统一分类模型

### 数据库字段

保留现有标准化 JD 字段，增加一层官网分类和一层产品统一分类。最小字段集如下：

```text
official_taxonomy    JSON          # 官网 L1/L2/L3 的 code、name、path；缺级允许 null
role_group          VARCHAR(40)   # 技术研发 / 产品 / 运营 / 设计 / 销售市场 / 职能 / 硬件制造 / unknown
role_family         VARCHAR(40)   # backend / frontend / client / algorithm / ml_engineering / data_engineering / ... / unknown
specialties         JSON          # AI应用、推荐搜索、AI Infra、支付、云原生等
business_domains    JSON          # 电商、广告、支付金融、内容、游戏、云计算等
tech_stack          JSON          # Java、Go、Redis、Flink、LLM、RAG 等
classification_meta JSON          # version、confidence、source_field_paths、matched_rules
```

`category`、`job_family` 和旧 `inferred_track` 暂时保留用于兼容，但 UI、岗位筛选、面经匹配和 AI 分析逐步切到新字段。不要假设旧 `category/job_family` 在公司间同级。JSON 数组已经足够，不需要现在为标签建立关系表。

`official_taxonomy` 只保存安全白名单，并明确层级和来源路径，例如：

```json
{
  "level1": {"code": null, "name": "研发", "path": "job_category.parent.i18n_name"},
  "level2": {"code": null, "name": "后端", "path": "job_category.i18n_name"},
  "level3": null,
  "tags": []
}
```

`classification_meta` 只保留安全、必要的分类证据，例如：

```json
{
  "version": "rules-2026-07-18",
  "confidence": 0.94,
  "official": {
    "group": {"value": "技术类", "path": "jobFamily"},
    "family": {"value": "算法", "path": "jobFamilyGroup"}
  },
  "matched_rules": ["title:大模型", "title:算法"],
  "fallback": false
}
```

### 各来源可靠字段映射

| 来源 | `role_group` 的官方证据 | `role_family` 的官方证据 | 必须依赖标题/JD补齐的内容 |
| --- | --- | --- | --- |
| 阿里 | `categoryName` | 暂无可靠细族；**不要用** `categoryType` | 后端/前端/算法/产品等主族及全部专业方向 |
| 百度 | `postType` | 通常不足；`projectType` 仅作招聘项目证据 | 主族、专业方向、业务域 |
| 字节 | `job_category.parent.i18n_name` | `job_category.i18n_name` | 专业方向、业务域、技术栈 |
| 华为 | `jobFamilyName` | 优先详情 `jobSubcategoryName/jobClassName`；无名称时保留代码作证据，不直接展示 | 代码未解析时的主族，以及专业方向 |
| 京东 | `jobDirection` | `jobCategory`，并以 `reqTagList` 作补充证据 | 专业方向、业务域、技术栈 |
| 快手 | `positionCategoryCode` 经官网 `/positions/label` 字典解析 | 官网通常仍无稳定细族 | 细岗位族、专业方向、业务域、技术栈 |
| 美团 | `jobFamily` | `jobFamilyGroup` | 专业方向、业务域、技术栈 |
| 腾讯 | 校招 `detail.tidName`；社招 `CategoryName` | 通常不足 | 主族主要依赖标题/JD；`ProductName`、`bgs/BGName` 只作业务域证据 |

### 分类顺序

1. 适配器先合并列表与详情，输出统一 JD 和 `official_taxonomy` 安全白名单。
2. 用公司自己的可靠中文类目确定 `role_group` / `role_family`；仅内部代码或粗类目时不强猜。
3. 用标题的排他规则确定主族：例如“产品经理”优先于“大模型”，“芯片后端”优先于软件“后端”，“SRE/运维”优先于 AI 关键词。
4. 用标题 + 职责 + 要求提取 `specialties/business_domains/tech_stack`，允许多值。
5. 冲突时把 `role_family=unknown` 或降低置信度，保留命中证据；不要为追求覆盖率强制错分。

这套顺序能让“AI 大模型产品经理”成为 `product_manager + AI产品`，让“AI应用后端开发-国际支付”成为 `backend + [AI应用, 支付金融]`，同时保留公司原始分类供排错。

## 当前代码中必须先处理的两个数据问题

1. **`raw_json` 不是官网 raw。** `JobPosting` 虽有 `raw_data` 字段，但刷新落库前 `_dump_jobs()` 明确排除了它；仓库随后把已经标准化的 job 字典整体写入 `raw_json`。因此当前数据库无法回放每家公司原始分类字段。证据：[`models.py:31`](../../niuke_mianjing_backend/crawler/recruitment/models.py#L31)、[`recruitment.py:424-427`](../../niuke_mianjing_backend/api/routes/recruitment.py#L424-L427)、[`recruitment_job_repo.py:243-280`](../../niuke_mianjing_backend/repositories/recruitment_job_repo.py#L243-L280)。
2. **也不能简单改成保存完整 `raw_data`。** 本次快手和华为响应都包含招聘流程、负责人或联系人类字段。正确做法是由适配器产出 `official_taxonomy` / `classification_meta` 白名单，只保存分类所需的字段名、非敏感值和来源路径；完整原包只在本地临时诊断，默认不落库、不返回前端。

## 刷新版本必须增加发布门禁

本次华为校招和实习真实返回 0 条，暴露了比分类更危险的问题：当前刷新路由即使 `jobs=[]`，仍会执行 `mark_latest_version()`。`upsert_many([])` 不写入新岗位，随后旧版本却会全部被标成 `is_latest=0`，前台看起来就像岗位被清空。

每个“来源 × 招聘类型”必须先抓取到候选版本，验证通过后才能切换最新版本：

1. 旧版本有数据而新版本为 0：记录为 `suspicious` 或 `failed`，保留旧版本。
2. 数量相对上一版骤降超过阈值（建议先用 70%，以后按来源调节）：不自动发布。
3. 校验岗位 ID、标题、链接覆盖率，以及职责/要求完整率；低于该来源基线时不发布。
4. 保存本次响应的非敏感 schema 指纹和质量指标；关键字段路径变化时告警。
5. 只有全部门禁通过后才执行 `mark_latest_version()`；官网确实清空岗位时由管理员明确确认发布空版本。

这里不需要引入复杂工作流系统：给刷新记录增加 `suspicious` 状态和质量摘要 JSON，并调整切换最新版本的调用顺序即可。

## 建议实施顺序

1. 先把美团、华为、腾讯社招改为“列表 + 详情合并”，修复华为列表字段丢失。
2. 给每个适配器增加一个小的安全 `official_taxonomy` 字典；先覆盖上表已有字段，不建新适配器框架。快手在批次开始时读取一次官网标签字典。
3. 新增统一分类字段和一组真实标题回归样本，先解决产品/运营误归 AI、芯片后端误归软件后端、SRE 误归 AI 等排他问题。
4. 面经匹配再切换到 `company + role_family + specialties + business_domains + 时间衰减`；旧 `inferred_track` 暂留作兼容筛选。
5. 为每个来源保留一份脱敏响应夹具做适配器回归，不在 CI 中实时请求官网；华为校招/实习空结果单独监控，不应阻塞其余来源分类落地。

## 可复核性说明

- 适配器注册表确实包含 8 家来源：[`registry.py:16-24`](../../niuke_mianjing_backend/crawler/recruitment/registry.py#L16-L24)。
- 项目声明的招聘类型见 [`recruitment.py:64-120`](../../niuke_mianjing_backend/api/routes/recruitment.py#L64-L120)。
- 阿里请求当前依赖仓库中固定的会话材料；本文未复制任何值。该会话失效时应把来源标记为抓取失败，而不是发布空版本。实现位置：[`official_pages.py:109-172`](../../niuke_mianjing_backend/crawler/recruitment/official_pages.py#L109-L172)。
- 本文所有“字段存在/缺失”结论来自上述时间窗口的官网响应和对应适配器，不是从数据库旧批次反推。
