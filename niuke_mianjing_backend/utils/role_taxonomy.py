import re

CLASSIFICATION_CACHE_VERSION = "roles-v3"
ROLE_FAMILY_RULES = [
    ("ai_product", "product", ["AI产品", "AI 产品", "大模型产品", "智能体产品", "Agent产品", "Agent 产品"]),
    ("product", "product", ["产品经理", "产品专家", "产品负责人", "技术产品", "产品"]),
    ("product_planning", "product", ["系统策划", "数值策划", "战斗策划", "游戏策划", "策划师", "技术制片人"]),
    ("strategy_research", "corporate", ["产业研究", "战略研究", "战略分析", "战略规划", "战略实习", "战略洞察", "行业研究", "经营分析", "投资实习", "生态研究"]),
    ("legal_compliance", "corporate", ["法务", "律师", "专利", "法律", "Legal Counsel", "知识产权", "合规", "资质认证", "标准和法规", "政策研究", "公共事务", "政府关系"]),
    ("finance_audit", "corporate", ["财务", "财经", "结算", "内审", "内控", "税务", "会计", "审计", "资金管理"]),
    ("hr_admin", "corporate", ["人力资源", "HRBP", "HR", "COE", "招聘", "行政", "秘书", "接待", "校企合作", "组织发展", "组织文化", "部门助理", "薪酬", "党建"]),
    ("game_content_design", "design", ["原画", "动画", "动漫", "编剧", "制片", "导演", "影视CG", "动作TA", "游戏动作", "美术师", "3D物件", "概念设计", "游戏界面", "UI动效", "2D场景", "2D角色", "3D场景", "3D角色", "特效", "技术美术", "技术导演", "游戏美术", "3D设计", "内容创意"]),
    ("visual_design", "design", ["视觉设计", "品牌设计", "平面设计", "动效设计", "调色师"]),
    ("product_design", "design", ["交互设计", "用户体验设计", "用户体验工程", "用户研究", "人因", "UI设计", "UX设计", "工业设计", "设计师", "设计实习生"]),
    ("solution_customer_success", "sales_marketing", ["解决方案", "售前", "客户成功", "行业顾问", "技术咨询", "行业咨询", "行业专家", "方案架构"]),
    ("marketing_brand", "sales_marketing", ["内容营销", "营销", "市场推广", "市场经理", "品牌经理", "品牌营销", "品牌公关", "公关", "传播", "PR", "媒介", "UA经理", "新媒体", "技术公关", "市场"]),
    ("sales_bd", "sales_marketing", ["销售", "客户经理", "商务拓展", "业务拓展", "BD", "渠道经理", "渠道分销", "IP授权", "PDSA"]),
    ("risk_governance", "operations", ["安全策略", "风险策略", "威胁情报", "风险情报", "策略分析", "风控策略", "广告策略", "内容治理", "商家治理", "审核", "音乐评测", "内容评测", "听感评测"]),
    ("supply_chain_retail", "operations", ["物流规划", "供应链", "采购", "商品开发", "商品运营", "部件计划", "门店", "零售"]),
    ("project_delivery", "operations", ["项目管理", "项目经理", "流程管理", "设施设备管理", "产研PMO", "PMO", "配置和变更管理", "实施", "交付", "技术支持", "技术服务", "IT服务", "终端智能管理", "网络交付", "用户上云方案", "设备维养", "设备维护", "设备维修", "施工管理", "土木工程"]),
    ("operations_growth", "operations", ["运营", "用户增长", "增长策略", "活动策划", "SOP", "GTM", "业务创新孵化"]),
    ("robotics_auto", "engineering", ["自动驾驶", "无人车", "车辆工程", "车身系统", "智能座舱", "域控制器", "激光雷达", "底盘", "电控制动", "转向电控", "车载", "云端建图", "机器人", "无人机", "机电一体化", "建模仿真", "仿真开发", "仿真世界"]),
    ("hardware_chip", "engineering", ["芯片", "昆仑芯", "处理器", "RISC-V", "CPU 架构", "CPU架构", "IC设计", "数字前端", "数字后端", "模拟电路", "版图", "SoC", "FPGA", "昇腾计算", "鲲鹏计算", "存算一体", "嵌入式", "固件", "单片机", "驱动开发", "硬件工程师", "电气工程师", "机械工程师", "结构与材料", "信号完整性", "电源完整性", "光技术", "电源技术", "热设计", "光学设计", "工艺设计", "设计空间探索", "封装应力", "制造工艺", "器件工程", "功能材料", "功率器件", "天线", "模组技术", "射频", "结构工程师", "器件工程师", "工业自动化", "自动化控制", "自控工程师", "精密装备", "精密制造", "ESD工程师", "摄像头工艺", "硬件"]),
    ("sre_devops", "engineering", ["SRE", "DevOps", "AIOps", "智能运维", "AI驱动运维", "运维系统", "运维开发", "运维研发", "运维工程师", "可靠性工程师", "可靠性架构师"]),
    ("security", "engineering", ["安全工程师", "安全实习生", "安全开发", "安全蓝军", "安全工具", "安全容器", "安全研发", "安全技术", "安全情报", "研发安全", "反爬虫", "反作弊", "AI安全", "网络安全", "隐私保护", "隐私技术", "漏洞挖掘", "攻防", "风控安全", "信息安全", "Security Architect", "逆向工程"]),
    ("testing_quality", "engineering", ["测试开发", "测试工程师", "测试与质量", "质量管理工程师", "质量工程师", "质量效能", "路测工程师", "NOC验证", "SIT", "测试", "SDET", "QA"]),
    ("data_analysis", "engineering", ["数据分析", "商业分析", "BI分析", "数据科学", "Data Scientist", "效能分析师", "高级数据策略", "内容分析"]),
    ("data_engineering", "engineering", ["数据开发", "数据研发", "大数据开发", "大数据引擎", "数据工程", "AI数据", "数据应用工程", "数据中台", "数据平台", "数据仓库", "数仓", "数据湖", "数据治理", "数据生成", "数据合成", "数据闭环", "数据产线", "Data+AI平台"]),
    ("game_multimedia", "engineering", ["Gameplay", "UE5", "游戏服务器", "游戏客户端", "游戏引擎", "AI引擎工程师", "主程序", "Client Programmer", "游戏技术", "游戏AI", "Game Engineer", "音视频", "多媒体", "视频编解码", "视频编辑", "直播转码", "流媒体", "实时音频", "音频声学", "ASR", "TTS", "图形渲染", "图形学", "特效SDK", "特效开发"]),
    ("frontend_fullstack", "engineering", ["前端开发", "前端研发", "前端工程师", "Web前端", "web实习生", "H5开发", "前端", "全栈"]),
    ("client", "engineering", ["客户端开发", "客户端研发", "移动端开发", "Android", "安卓", "iOS", "鸿蒙", "Flutter", "客户端", "移动OS", "浏览器内核", "可视化引擎", "引擎开发", "创作引擎", "渲染引擎"]),
    ("backend_software", "engineering", ["后端", "后台工程师", "后台开发", "后台研发", "服务端", "服务器高级工程师", "Java开发", "Java工程师", "Go工程师", "Golang", "Go开发", "NodeJS", "Backend", "backend programmer"]),
    ("ai_infra", "engineering", ["AI Infra", "大模型Infra", "训练 Infra", "Agent Infra", "Infra 系统", "Infra系统", "机器学习系统", "AI框架", "训练框架", "推理框架", "推理平台", "训练平台", "训推平台", "模型服务", "模型部署", "模型推理", "推理系统", "推理工程", "推理引擎", "训推引擎", "AI算子", "算子优化", "高性能算子", "异构计算", "异构加速", "AI计算加速", "模型加速与部署", "分布式训练", "框架通信", "AI性能优化"]),
    ("ai_algorithm", "engineering", ["算法工程师", "算法研究", "算法专家", "算法实习", "研究科学家", "Research Scientist", "基础模型架构", "Agentic AI", "Agentic RL", "Agentic Search", "Agent研究", "Agent以及小型化研究", "RL Data", "RL环境", "奖励设计", "AI Agent优化", "AI Agent 优化", "AI for", "视觉基本问题", "多病种筛查", "数据智多星", "智能引擎研究", "Bid Optim", "广告拍卖", "预训练", "后训练", "Post-training", "强化学习", "RL研究", "模型训练", "模型评测", "AI评测"]),
    ("ai_application", "engineering", ["AI应用", "AI 应用", "AI原生", "AI 原生", "AI Technical Builder", "AI业务探索", "大模型应用", "Agent Harness", "Agent Engineer", "Code Agent", "Agent工程", "Agent 工程", "Agent开发", "Agent研发", "Agent 研发", "智能体开发", "智能体工程", "RAG应用", "RAG 应用", "AI Coding", "AI工作流", "AI原生应用", "AI知识工程", "AgentRuntime"]),
    ("ai_algorithm", "engineering", ["算法", "大模型", "机器学习", "多模态", "全模态", "跨模态", "智能对话", "智能体", "具身智能", "世界模型", "生成模型", "图像生成", "视频生成", "视频理解", "语言模型", "AIGC", "AI研究", "数据挖掘", "决策推理", "深度学习", "自然语言处理", "计算机视觉", "推荐", "搜索与复杂推理", "LLM", "Multimodal"]),
    ("backend_software", "engineering", ["IaaS研发", "平台开发", "生产系统研发", "系统研发", "系统架构", "搜索架构", "广告架构", "广告工程师", "serverless", "基础架构", "高性能计算", "数据库", "PolarDB", "查询优化", "KV Cache", "文件系统", "JVM", "HTAP", "SQL优化", "存储研发", "存储系统", "存储平台", "计算系统", "操作系统", "编译器", "云存储开发", "云计算开发", "云服务开发", "平台软件", "网络工程", "网络系统", "网络架构", "网络规划", "网络技术", "智算网络", "通信软件", "容器网络", "虚拟网络", "域名解析", "RDMA", "CXL", "数据中心", "IDC资源", "服务器资源", "数字化IT应用", "软件开发", "软件工程师", "软件研发", "Software Engineer", "研发实习生", "研发工程师", "开发工程师", "TypeScript工程师", "C++研发", "Python 工程师", "框架研发", "技术研究", "前沿技术研究", "应用研究", "软件"]),
]

ROLE_FAMILY_LABELS = {
    "ai_product": "AI 产品",
    "product": "产品经理",
    "product_planning": "产品/游戏策划",
    "operations_growth": "运营/增长",
    "project_delivery": "项目/交付",
    "risk_governance": "风控/治理",
    "supply_chain_retail": "供应链/零售",
    "product_design": "产品/体验设计",
    "visual_design": "视觉/品牌设计",
    "game_content_design": "游戏/内容设计",
    "sales_bd": "销售/商务",
    "marketing_brand": "市场/品牌",
    "solution_customer_success": "解决方案/客户成功",
    "hr_admin": "人力/行政",
    "finance_audit": "财务/审计",
    "legal_compliance": "法务/合规",
    "strategy_research": "战略/行业研究",
    "ai_algorithm": "AI 算法/研究",
    "ai_application": "AI 应用/Agent",
    "ai_infra": "AI Infra/机器学习系统",
    "backend_software": "后端/基础架构",
    "frontend_fullstack": "前端/全栈",
    "client": "客户端/跨端",
    "data_engineering": "数据工程",
    "data_analysis": "数据分析/数据科学",
    "testing_quality": "测试/质量",
    "sre_devops": "SRE/DevOps/研发效能",
    "security": "安全",
    "hardware_chip": "芯片/硬件/嵌入式",
    "game_multimedia": "游戏/音视频/图形",
    "robotics_auto": "机器人/自动驾驶",
}

AI_HOT_FAMILIES = {"ai_algorithm", "ai_application", "ai_infra", "ai_product"}
AI_FAMILY_PRIORITY = {"ai_algorithm": 0, "ai_application": 1, "ai_infra": 2}
AI_HOT_TITLE_HINTS = ["AI", "人工智能", "大模型", "LLM", "AIGC", "Agent", "智能体", "RAG", "机器学习", "深度学习", "算法", "多模态", "具身智能", "世界模型"]
WEAK_BACKEND_HINTS = {
    "软件开发", "软件工程师", "软件研发", "Software Engineer", "研发实习生",
    "研发工程师", "开发工程师", "技术研究", "前沿技术研究", "应用研究", "软件",
}
AI_AMBIGUOUS_TITLE_HINTS = ["AI研发工程师", "AI 研发工程师", "机器学习工程师", "大模型工程师"]
AI_BODY_DISAMBIGUATION = [
    ("ai_infra", ["训练平台", "推理平台", "推理引擎", "模型服务", "算子优化", "异构计算", "分布式训练", "模型部署"]),
    ("ai_application", ["应用开发", "业务落地", "Agent", "智能体", "RAG", "知识库", "AI Coding"]),
    ("ai_algorithm", ["模型效果", "算法研究", "预训练", "后训练", "强化学习", "推荐算法", "计算机视觉", "自然语言处理"]),
]

ROLE_GROUP_LABELS = {
    "engineering": "技术",
    "product": "产品",
    "operations": "运营/交付",
    "design": "设计",
    "sales_marketing": "市场/销售",
    "corporate": "职能",
    "unknown": "其他",
}
ENGLISH_TOKEN_PATTERNS = {
    "go": re.compile(r"(?<![a-z0-9])go(?![a-z0-9])", re.IGNORECASE),
    "web": re.compile(r"(?<![a-z0-9])web(?![a-z0-9])", re.IGNORECASE),
    "qa": re.compile(r"(?<![a-z0-9])qa(?![a-z0-9])", re.IGNORECASE),
    "cv": re.compile(r"(?<![a-z0-9])cv(?![a-z0-9])", re.IGNORECASE),
    "ai": re.compile(r"(?<![a-z0-9])ai(?![a-z0-9])", re.IGNORECASE),
}

GROUP_FALLBACK_RULES = [
    ("engineering", ["硬件", "芯片", "制造"]),
    ("product", ["产品"]),
    ("operations", ["运营", "审核", "客服"]),
    ("design", ["设计", "交互", "视觉"]),
    ("sales_marketing", ["销售", "市场", "商务"]),
    ("corporate", ["职能", "人力", "财务", "法务", "行政"]),
    ("engineering", ["技术", "研发", "软件", "工程", "算法", "数据"]),
]


def contains_hint(text: str, hint: str) -> bool:
    lowered = hint.lower()
    if lowered in ENGLISH_TOKEN_PATTERNS:
        return bool(ENGLISH_TOKEN_PATTERNS[lowered].search(text))
    return lowered in text.lower()


def classify_role(title: str = "", official: str = "", body: str = "") -> dict:
    role_family = role_group = matched_rule = None
    confidence = 0.0
    weak_title_match = None
    if any(contains_hint(title, hint) for hint in AI_AMBIGUOUS_TITLE_HINTS):
        for family, hints in AI_BODY_DISAMBIGUATION:
            hint = next((value for value in hints if contains_hint(body, value)), None)
            if hint:
                role_family, role_group = family, "engineering"
                matched_rule, confidence = f"body:{hint}", 0.78
                break
    for family, group, hints in ROLE_FAMILY_RULES:
        if role_family:
            break
        hint = next((value for value in hints if contains_hint(title, value)), None)
        if hint:
            if family == "backend_software" and hint in WEAK_BACKEND_HINTS:
                weak_title_match = (family, group, hint)
                continue
            role_family, role_group = family, group
            matched_rule, confidence = f"title:{hint}", 0.95
            break
    if not role_family:
        for family, group, hints in ROLE_FAMILY_RULES:
            hint = next((value for value in hints if contains_hint(official, value)), None)
            if hint:
                role_family, role_group = family, group
                matched_rule, confidence = f"official:{hint}", 0.85
                break
    if not role_family and weak_title_match:
        role_family, role_group, hint = weak_title_match
        matched_rule, confidence = f"title:{hint}", 0.75
    if not role_group:
        combined = f"{title} {official}"
        for group, hints in GROUP_FALLBACK_RULES:
            hint = next((value for value in hints if contains_hint(combined, value)), None)
            if hint:
                role_group, matched_rule, confidence = group, f"group:{hint}", 0.65
                break
    return {
        "role_group": role_group or "unknown",
        "role_family": role_family or "unknown",
        "classification_meta": {
            "version": CLASSIFICATION_CACHE_VERSION,
            "confidence": confidence,
            "source_field_paths": [],
            "matched_rules": [matched_rule] if matched_rule else [],
            "fallback": not bool(role_family),
        },
    }


INTERVIEW_POST_ROLES = {
    "后端开发": ("engineering", "backend_software"),
    "前端开发": ("engineering", "frontend_fullstack"),
    "客户端开发": ("engineering", "client"),
    "测试": ("engineering", "testing_quality"),
    "运维": ("engineering", "sre_devops"),
    "数据开发": ("engineering", "data_engineering"),
    "人工智能/算法": ("engineering", "ai_algorithm"),
}
INTERVIEW_ROLE_DECLARATION = re.compile(
    r"(?:面试(?:的)?|投递(?:的)?|应聘(?:的)?)(?:岗位|职位|方向)\s*(?:是|为|[:：])\s*([^\n，。；;:：?？❓~]{1,30})"
)


def classify_interview_role(title: str, post: str, content: str = "") -> dict:
    body = (content or "")[:1500]
    declaration = INTERVIEW_ROLE_DECLARATION.search(body)
    for source, candidate in (("declaration", declaration.group(1).strip() if declaration else ""), ("title", title or "")):
        if not candidate:
            continue
        result = classify_role(candidate, "", body)
        if result["role_family"] != "unknown" and (source == "declaration" or result["role_group"] == "engineering"):
            result["classification_meta"]["matched_rules"].insert(0, f"interview:{source}")
            return result

    group, family = INTERVIEW_POST_ROLES.get(post, ("unknown", "unknown"))
    result = classify_role("", post or "", "")
    if result["role_family"] == "unknown" and family != "unknown":
        result.update(role_group=group, role_family=family)
        result["classification_meta"].update(confidence=0.7, fallback=False)
    result["classification_meta"]["matched_rules"].insert(0, "interview:post")
    return result
