# OfferLens 二级岗位族：结合 2026 大厂岗位市场的收敛方案

调研日期：2026-07-18

## 结论

一级分类保持现状；二级分类不要继续把每个专业名都升级成岗位族。推荐全站采用“**少量岗位族 + 多值专业标签**”：技术一级保留 **14 个**二级，其中 AI 明确拆成 **3 个岗位族**；产品、运营、设计、市场和职能各保留 3–4 个二级。

AI 不应只叫一个宽泛的“算法”，也不应把大模型、NLP、CV、推荐、搜索、Agent、RAG、AIGC、具身智能分别做成十多个并列入口。当前一手证据最稳定的分法是：

1. **AI 算法/研究**：做模型、算法、训练方法和研究；
2. **AI 应用/Agent**：把模型能力落到产品与业务系统；
3. **AI Infra/机器学习系统**：训练、推理、框架、算子、调度和模型服务。

这不是为了追热点而拆词。阿里 2027 阿里星官网本身就把技术课题组织为“基础模型”“大模型应用”“AI Infra”三大块；字节 2027 前沿技术人才校招也明确同时招聘基础大模型、机器学习系统、大模型应用、AI Coding、AIGC 与安全/AI Safety 等方向。[阿里星官方页面](https://campus-talent.alibaba.com/campus/alistar)；[字节校园招聘官方说明](https://jobs.bytedance.com/campus/page-6272Gc)

## 当前真实岗位数据

### 数据口径

本次读取本地 `official_recruitment_jobs` 中各 `source × recruitment_type` 的 `is_latest=1` 全量岗位，共 **12,178 条**，刷新批次时间均为 2026-06-20。读取逻辑对应 [`list_latest_jobs()`](../../niuke_mianjing_backend/repositories/recruitment_job_repo.py#L194-L212)，并用当前 [`_classify_job()` 规则及岗位族词典](../../niuke_mianjing_backend/api/routes/recruitment.py#L174-L217)重新归类，以免数据库内旧分类版本影响统计。

这个快照用于判断“哪些方向跨公司持续存在”，**不能当作市场份额**：字节实习岗位 5,501 条、腾讯社招 2,099 条，来源抓取范围和去重口径不完全相同，会显著影响绝对频次。

### 当前岗位族规模与跨公司覆盖

| 当前岗位族 | 岗位数 | 覆盖公司数 | 结论 |
| --- | ---: | ---: | --- |
| 算法 | 1,971 | 8/8 | 必须保留，但需与 AI 应用、AI Infra 分清边界 |
| 后端 | 1,119 | 8/8 | 核心岗位族 |
| 机器学习工程 | 811 | 8/8 | 当前过宽，混合了 Agent、AI 应用、训推 Infra，应拆分 |
| 产品经理 | 711 | 7/8 | 核心岗位族；AI 产品已形成可见子市场 |
| 客户端 | 408 | 6/8 | 核心岗位族 |
| 前端 | 382 | 6/8 | 核心岗位族，可合并低频全栈 |
| 数据分析 | 307 | 8/8 | 面试体系与数据开发不同，独立保留 |
| 测试 | 264 | 7/8 | 核心岗位族 |
| 数据工程 | 218 | 8/8 | 核心岗位族 |
| 芯片 | 217 | 7/8 | 与硬件、嵌入式合并成一个入口，再用标签细分 |
| 游戏研发 | 183 | 3/8 | 公司集中但岗位重要，可与音视频/图形合并为一个入口 |
| 安全 | 146 | 8/8 | 面试体系独立，不能并入 SRE |
| SRE/DevOps | 78 | 7/8 | 与研发效能合并，不与安全合并 |

来源：同一份 2026-06-20 最新岗位快照；现有岗位族名称与映射见 [`ROLE_FAMILY_LABELS`](../../niuke_mianjing_backend/api/routes/recruitment.py#L219-L262)。

### AI 热度信号

在岗位标题中匹配 `AI / 人工智能 / 大模型 / LLM / AIGC / Agent / RAG / 算法 / 机器学习 / 多模态 / 智能体 / 具身智能 / 世界模型` 等明确技术信号：

- 4,295 条标题包含至少一个 AI 信号，占快照的 **35.3%**；
- 其中技术一级 3,498 条，产品一级 405 条；
- 标题词频（可重叠）：`AI` 2,014、`算法` 1,687、`大模型` 1,354、`Agent` 435、`多模态` 400、`AIGC` 226；
- AI 标题岗位覆盖全部 8 个招聘来源；当前 `algorithm` 与 `ml_engineering` 两族合计承接了 2,617 条，但另有大量 AI 后端、AI 产品、AI 测试、AI 安全岗位，说明“AI”还必须是一个跨岗位族标签。

这些数字只证明 AI 已经是结构性招聘主题，不用于宣称精确市场占比。官方页面也给出同样的方向性证据：

- 阿里星把课题明确分成基础模型、大模型应用、AI Infra，并列出 Agentic、训推、AI Coding、具身智能、AI Safety 等大量方向。[阿里星官方页面](https://campus-talent.alibaba.com/campus/alistar)
- 字节官方把 Seed 岗位概括为基础大模型、机器学习系统、视觉/语音智能、AI 搜索、模型个性化、具身智能；前沿技术校招还包括大模型应用、AI Coding、AIGC、AI Safety 和 AI for Science。[字节官方校园招聘说明](https://jobs.bytedance.com/campus/page-6272Gc)
- 美团官网已经把“LongCat 大模型人才招聘”设为独立招聘入口，真实岗位同时出现“大模型推理系统工程师”“AI Agent 工程师”“基础模型-预训练”等不同面试体系。[美团招聘首页](https://zhaopin.meituan.com/web/home)；[推理系统岗位](https://zhaopin.meituan.com/web/position/detail?jobUnionId=4554665111)；[AI Agent 岗位](https://zhaopin.meituan.com/web/position/detail?jobUnionId=4533842729)；[基础模型岗位](https://zhaopin.meituan.com/web/position/detail?jobUnionId=4530553724)
- 腾讯校招同时存在“AI应用开发”以及推荐、机器学习、视觉、NLP、多模态等算法方向。[AI应用开发官方岗位](https://join.qq.com/post_detail.html?postid=1242578894281124864)；[腾讯官网分类调研证据](./2026-07-18-official-job-taxonomy-levels.md#腾讯)

## 推荐的统一二级分类

### 技术：14 个

| 排序 | 二级 ID | 展示名 | 承接范围 | 不再作为二级的细方向 |
| ---: | --- | --- | --- | --- |
| 1 | `ai_algorithm` | AI 算法/研究 | 基础模型、传统机器学习算法、推荐/搜索算法、预训练/后训练研究、模型评测研究 | LLM、NLP、CV、推荐、搜索、多模态、AIGC、AI for Science |
| 2 | `ai_application` | AI 应用/Agent | AI 应用开发、Agent 工程、RAG 应用、AI Coding 产品工程、LLM 应用架构 | Agent、RAG、Prompt、AI Coding、知识库 |
| 3 | `ai_infra` | AI Infra/机器学习系统 | 训练/推理平台、模型服务、框架、算子、编译优化、异构计算、资源调度 | 训练、推理、GPU/NPU、模型部署、分布式训练 |
| 4 | `backend_software` | 后端/通用软件 | 后端、服务端、通用软件、基础架构、存储/数据库、网络系统、非 AI 系统研发 | Java/Go/C++、云原生、存储、数据库、网络、分布式 |
| 5 | `frontend_fullstack` | 前端/全栈 | Web 前端、跨 Web 工程、全栈 | React/Vue/Node、小程序、低代码 |
| 6 | `client` | 客户端/跨端 | Android、iOS、鸿蒙、桌面端、非游戏客户端和跨端 | Android/iOS/Flutter/鸿蒙/桌面端 |
| 7 | `data_engineering` | 数据工程 | 大数据、数仓、数据平台、数据治理、实时/离线计算 | Flink/Spark/Hive、数仓、数据湖、Data for AI |
| 8 | `data_analysis` | 数据分析/数据科学 | 数据分析、BI、数据科学、商业分析中的技术分析岗 | BI、实验分析、因果推断、增长分析 |
| 9 | `testing_quality` | 测试/质量 | 测试开发、自动化测试、质量平台、SDET | 性能测试、安全测试、AI 测试 |
| 10 | `sre_devops` | SRE/DevOps/研发效能 | SRE、运维开发、AIOps、研发效能、构建与发布平台 | 可观测性、CI/CD、稳定性、AIOps |
| 11 | `security` | 安全 | 安全研发、攻防、隐私技术、反作弊、AI 安全工程 | 攻防、数据安全、隐私、AI Safety、风控安全 |
| 12 | `hardware_chip` | 芯片/硬件/嵌入式 | 芯片、驱动、嵌入式、射频、电气、机械、结构 | IC/SoC/FPGA、驱动、嵌入式、射频、服务器硬件 |
| 13 | `game_multimedia` | 游戏/音视频/图形 | 游戏客户端/服务端/引擎、图形渲染、音视频、多媒体 | UE/Unity、图形学、编解码、流媒体、ASR/TTS |
| 14 | `robotics_auto` | 机器人/自动驾驶 | 机器人、无人机、自动驾驶、智能座舱、仿真和具身系统工程 | 具身智能、感知、规划控制、仿真、车载 |

14 个已经是上限。不要再把“基础架构、数据库、网络、音视频、CV、NLP、推荐、搜索、AIGC、具身智能”继续提升为同级入口；它们是用户精准筛选和报告生成需要的**专业标签**。

### 产品：3 个

| 二级 ID | 展示名 | 说明 |
| --- | --- | --- |
| `product` | 产品经理 | 通用产品、平台产品、商业产品、技术产品 |
| `ai_product` | AI 产品 | 标题明确为 AI/大模型/Agent/RAG 产品；当前快照已有大量 AI 产品标题，面试会额外考模型边界、评测、数据与成本 |
| `product_planning` | 产品/游戏策划 | 系统、数值、玩法、内容和产品策划 |

AI 产品应独立，不只是标签；但“电商产品、广告产品、支付产品、国际化产品”等仍是业务域标签。

### 运营/交付：4 个

| 二级 ID | 展示名 | 合并范围 |
| --- | --- | --- |
| `operations_growth` | 运营/增长 | 用户、内容、产品、商家、活动、增长运营 |
| `project_delivery` | 项目/交付 | 项目管理、PMO、实施、交付、非售前技术支持 |
| `risk_governance` | 风控/治理 | 风险策略、内容治理、审核、反作弊策略 |
| `supply_chain_retail` | 供应链/零售 | 采购、物流、供应链、门店、商品运营 |

### 设计：3 个

| 二级 ID | 展示名 | 合并范围 |
| --- | --- | --- |
| `product_design` | 产品/体验设计 | UI、UX、交互、用户研究 |
| `visual_design` | 视觉/品牌设计 | 视觉、品牌、平面、动效 |
| `game_content_design` | 游戏/内容设计 | 原画、3D、技术美术、内容创意 |

### 市场/销售：3 个

| 二级 ID | 展示名 | 合并范围 |
| --- | --- | --- |
| `sales_bd` | 销售/商务 | 销售、客户经理、BD、渠道 |
| `marketing_brand` | 市场/品牌 | 市场、品牌、公关、媒介、内容营销 |
| `solution_customer_success` | 解决方案/客户成功 | 售前方案、解决方案架构、行业顾问、客户成功 |

### 职能：4 个

| 二级 ID | 展示名 | 合并范围 |
| --- | --- | --- |
| `hr_admin` | 人力/行政 | HR、招聘、行政 |
| `finance_audit` | 财务/审计 | 财务、税务、会计、审计 |
| `legal_compliance` | 法务/合规 | 法务、知识产权、隐私合规、政策 |
| `strategy_research` | 战略/行业研究 | 战略、行业研究、经营分析 |

无法可靠判断的岗位进入“其他/待归类”，但不在首页放一个长期高曝光的“未知”按钮；仅在有数据时显示。

## 现有岗位族如何合并

| 现有 family | 新二级 |
| --- | --- |
| `algorithm` | `ai_algorithm` |
| `ml_engineering` | 依据标题/JD拆为 `ai_algorithm`、`ai_application`、`ai_infra` |
| `backend`、`software_engineering`、`network_engineering`、`datacenter_operations` | `backend_software` |
| `frontend`、`fullstack` | `frontend_fullstack` |
| `client` | `client` |
| `data_engineering` | `data_engineering` |
| `data_analysis` | `data_analysis` |
| `testing` | `testing_quality` |
| `sre_devops`、`developer_productivity` | `sre_devops` |
| `security` | `security` |
| `chip`、`hardware`、`embedded`、`automation_engineering` | `hardware_chip` |
| `game_development`、`multimedia` | `game_multimedia` |
| `automotive`、`robotics`、`simulation_engineering` | `robotics_auto` |
| `research_engineering` | 有强 AI 研究信号进 `ai_algorithm`；否则进 `backend_software` |
| `solution_architect`、`technical_support`、`customer_success` | `solution_customer_success` 或 `project_delivery`，由是否售前/客户经营判断 |
| `product_manager` | 标题明确 AI 产品进 `ai_product`；其余进 `product` |
| `product_planning` | `product_planning` |
| `operations` | `operations_growth` |
| `project_management` | `project_delivery` |
| `risk_strategy`、`content_evaluation` | `risk_governance` |
| `supply_chain`、`equipment_maintenance`、`construction_engineering` | 依职责进入 `supply_chain_retail` 或 `project_delivery` |
| `sales` | `sales_bd` |
| `marketing` | `marketing_brand` |
| `corporate` | 按标题拆到 4 个职能二级 |
| `design` | 按标题拆到 3 个设计二级 |
| `unknown` | 仅在标题、官网分类或 JD 达到阈值时重判；否则保持待归类 |

## 边界与优先级规则

### 1. 先定一级，再定二级

“AI 产品经理”先归产品一级，再归 `ai_product`；“AI Agent 运营”仍归运营；“AI 安全工程师”归安全。不能因为 JD 出现 AI 就把所有岗位吸进技术 AI 三族。

### 2. 标题强信号高于 JD 泛化信号

- 标题或官网二级明确岗位职责，可决定二级；
- JD 中只出现“使用 AI、了解大模型、用 Copilot 提效”，只增加 `ai_related` 标签，不改变岗位族；
- 这样可避免后端、产品、运营岗位因公司统一写入 AI 要求而被错误重分类。

当前实现已区分标题、官网分类、正文三个证据场，并优先使用标题/官网分类，见 [`_classification_text()` 与 `_classify_job()`](../../niuke_mianjing_backend/api/routes/recruitment.py#L507-L586)。

### 3. AI 三族的判定顺序

1. 明确出现训练/推理平台、框架、算子、编译器、模型服务、GPU/NPU、异构计算、调度等系统职责 → `ai_infra`；
2. 明确出现 AI 应用开发、Agent 工程/应用架构、RAG 应用、AI Coding 产品工程 → `ai_application`；
3. 明确出现算法、模型研究、预训练/后训练算法、推荐/搜索/CV/NLP/多模态研究 → `ai_algorithm`；
4. 只有 `AI研发工程师`、`Agent研发` 等模糊标题时，读 JD：主要交付在线应用进 `ai_application`，主要做模型效果进 `ai_algorithm`，主要做平台性能进 `ai_infra`；无法判断则保留 `backend_software + ai_related`，不要硬猜。

三个典型边界样例：美团“大模型推理系统工程师”属于 `ai_infra`，[官方岗位](https://zhaopin.meituan.com/web/position/detail?jobUnionId=4554665111)；腾讯“AI应用开发”属于 `ai_application`，[官方岗位](https://join.qq.com/post_detail.html?postid=1242578894281124864)；字节“大语言模型强化学习算法工程师”属于 `ai_algorithm`，[官方岗位](https://jobs.bytedance.com/campus/position/7622492141250070789/detail)。

### 4. 具身智能、AI 安全、AI 数据是交叉方向

- 具身模型/算法研究 → `ai_algorithm + embodied_ai`；机器人系统、控制、硬件 → `robotics_auto + embodied_ai`；
- 模型对齐、红队研究 → `ai_algorithm + ai_safety`；安全平台、攻防、隐私工程 → `security + ai_safety`；
- 训练数据、Data for AI、数据湖 → `data_engineering + ai_data`；模型数据算法与合成方法研究 → `ai_algorithm + ai_data`。

### 5. 官网原始分类不能被覆盖

官网一级/二级仍保存在 `official_taxonomy`；OfferLens 的二级是独立 `normalized role_family`。字节、美团、腾讯有可见官网二级，阿里和拼多多只有页面一级，这个边界已经由官网页面核验。[既有官网分类层级调研](./2026-07-18-official-job-taxonomy-levels.md)

## 标签体系

二级之外只保留少量有求职意义的多值标签：

- AI：`llm`、`agent_rag`、`recommendation`、`search`、`cv`、`nlp_speech`、`multimodal_aigc`、`ai_safety`、`embodied_ai`、`ai_coding`、`training_inference`、`ai_chip`；
- 技术：`cloud_native`、`distributed_systems`、`storage_database`、`network`、`audio_video`、`graphics`、`game_engine`；
- 业务域：电商、广告、支付金融、游戏、云、企业服务、内容社交、国际化；
- 技术栈：Java、Go、Python、C++、前端框架、数据栈、云原生栈。

现有代码已经把 `specialties`、`business_domains`、`tech_stack` 分开保存，适合直接承接这些维度，不需要新增第三层分类。[当前专业/业务域/技术栈规则](../../niuke_mianjing_backend/api/routes/recruitment.py#L293-L334)

## 前端展示建议

1. 二级列表按“当前筛选结果数量”排序，但前三个 AI 二级在技术一级中固定置顶；没有岗位的二级不显示。
2. 增加一个聚合的 **“AI 热门岗位”** 快捷入口：包含三个 AI 技术族、AI 产品，以及其他岗位族上的 `ai_related` 标签。它是查询入口，不是新的岗位族。
3. 每个卡片只展示一个二级岗位族，再展示最多 2 个专业标签，例如“AI Infra/机器学习系统 · 推理优化 · 分布式训练”。
4. 不展示“官网推断二级”这种内部术语；详情页可显示“官网分类”和“OfferLens 分类”两行，并在低置信度时标记“根据标题/JD归类”。

## 最小实施范围

不需要改表。复用现有 `role_group`、`role_family`、`specialties`、`business_domains`、`tech_stack` 和 `classification_meta` 即可。只需：

1. 收敛 `ROLE_FAMILY_RULES` 与 `ROLE_FAMILY_LABELS`；
2. 把 `ml_engineering` 拆成三个 AI family，并把被合并的小 family 映射到新 family；
3. 扩充 AI 专业标签；
4. 前端按一级动态展示新二级，并增加“AI 热门岗位”聚合查询。

不建议现在引入 LLM 分类服务。标题 + 官网分类 + JD 的版本化规则已经能覆盖主要岗位，且可解释、可回归；只有当“待归类”在连续刷新中仍高于 5%，再考虑用 LLM 仅处理低置信度尾部。
