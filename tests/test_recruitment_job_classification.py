import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from niuke_mianjing_backend.api.routes.recruitment import _annotate_job, _dump_jobs, _filter_saved_jobs, _is_domestic_job, _refresh_quality
from niuke_mianjing_backend.crawler.recruitment.bytedance import ByteDanceRecruitmentAdapter
from niuke_mianjing_backend.crawler.recruitment.models import JobPosting
from niuke_mianjing_backend.crawler.recruitment.official_pages import (
    AlibabaRecruitmentAdapter,
    BaiduRecruitmentAdapter,
    DeepSeekRecruitmentAdapter,
    HuaweiRecruitmentAdapter,
    JDRecruitmentAdapter,
    KimiRecruitmentAdapter,
    KuaishouRecruitmentAdapter,
    MeituanRecruitmentAdapter,
    MiniMaxRecruitmentAdapter,
    PDDRecruitmentAdapter,
    XiaomiRecruitmentAdapter,
    XiaohongshuRecruitmentAdapter,
    ZhipuRecruitmentAdapter,
    _moka_is_intern,
    _split_moka_description,
)
from niuke_mianjing_backend.crawler.recruitment.tencent import TencentRecruitmentAdapter
from niuke_mianjing_backend.utils.role_taxonomy import classify_interview_role


def job(title, category="技术", description="", requirements=""):
    return JobPosting(
        source="test",
        source_job_id=title,
        company="测试公司",
        title=title,
        category=category,
        description=description,
        requirements=requirements,
        source_url="https://example.com/job",
    )


def test_primary_role_exclusions_and_multi_axis_tags():
    product = _annotate_job(job("AI 大模型产品经理"))
    assert (product.role_group, product.role_family, product.inferred_track) == ("product", "ai_product", None)

    backend = _annotate_job(job("AI应用后端开发-国际支付", description="Java、Redis、RAG 高并发服务"))
    assert backend.role_family == "backend_software"
    assert {"ai_related", "agent_rag", "distributed_systems"} <= set(backend.specialties)
    assert {"payment_finance", "international"} <= set(backend.business_domains)
    assert {"Java", "Redis", "RAG"} <= set(backend.tech_stack)

    assert _annotate_job(job("芯片后端设计工程师")).role_family == "hardware_chip"
    assert _annotate_job(job("大模型平台 SRE 工程师")).role_family == "sre_devops"
    assert _annotate_job(job("商业数据分析师")).role_family == "data_analysis"
    assert _annotate_job(job("数据湖开发工程师")).role_family == "data_engineering"


def test_official_taxonomy_can_fill_an_ambiguous_title():
    item = job("基础研发工程师")
    item.official_taxonomy = {
        "level1": {"name": "研发", "path": "job_category.parent"},
        "level2": {"name": "后端", "path": "job_category"},
        "level3": None,
        "tags": [],
    }
    assert _annotate_job(item).role_family == "backend_software"
    assert "job_category" in item.classification_meta["source_field_paths"]


def test_live_title_edge_cases_use_specific_families():
    assert _annotate_job(job("AI 宠物-后台工程师")).role_family == "backend_software"
    assert _annotate_job(job("音视频技术支持专家")).role_family == "project_delivery"
    assert _annotate_job(job("安全合规实习生")).role_family == "legal_compliance"
    assert _annotate_job(job("隐私与采购合规实习生", category="法务")).role_family == "legal_compliance"
    assert _annotate_job(job("服务器部件计划工程师")).role_family == "supply_chain_retail"
    assert _annotate_job(job("游戏引擎专家-性能优化方向")).role_family == "game_multimedia"
    assert _annotate_job(job("全栈极客工程师（AI-Native 方向）")).role_family == "frontend_fullstack"
    assert _annotate_job(job("模型加速与部署工程师")).role_family == "ai_infra"


def test_ai_roles_respect_primary_function_and_three_way_split():
    assert _annotate_job(job("AI 安全工程师")).role_family == "security"
    assert _annotate_job(job("大模型测试开发工程师")).role_family == "testing_quality"
    assert _annotate_job(job("大模型训练数据工程师")).role_family == "data_engineering"
    assert _annotate_job(job("Agent Infra 工程师")).role_family == "ai_infra"
    assert _annotate_job(job("RAG 应用开发工程师")).role_family == "ai_application"
    assert _annotate_job(job("大语言模型强化学习算法工程师")).role_family == "ai_algorithm"
    assert _annotate_job(job("机器学习工程师", description="负责推理平台、模型服务和算子优化")).role_family == "ai_infra"
    assert _annotate_job(job("机器学习工程师", description="负责 Agent 与 RAG 业务落地")).role_family == "ai_application"
    assert _annotate_job(job("机器学习工程师", description="研究模型效果与强化学习算法")).role_family == "ai_algorithm"


def test_interviews_share_role_taxonomy_with_structured_fallbacks():
    assert classify_interview_role("Java 后端面经", "后端开发")["role_family"] == "backend_software"
    assert classify_interview_role("大模型面经", "人工智能/算法", "投递岗位：RAG 应用开发工程师\n一面")["role_family"] == "ai_application"
    assert classify_interview_role("普通面经", "运维")["role_family"] == "sre_devops"


def test_source_specific_taxonomy_mapping():
    ali = AlibabaRecruitmentAdapter()._normalize_job({"id": 1, "name": "后端", "categoryName": "技术类"}, "intern")
    baidu = BaiduRecruitmentAdapter()._normalize_job({"postId": 1, "name": "后端", "postType": "技术"}, "social", "SOCIAL")
    byte = ByteDanceRecruitmentAdapter()._normalize_job({
        "id": 1,
        "title": "后端",
        "job_category": {"id": "b", "i18n_name": "后端", "parent": {"id": "a", "i18n_name": "研发"}},
    })
    huawei = HuaweiRecruitmentAdapter()._normalize_job({
        "jobId": 1,
        "jobname": "后端",
        "jobFamilyName": "研发族",
        "jobFamClsCode": "J26",
        "jobClass": "J2603",
        "jobClassName": "软件",
        "jobSubcategory": "J260312",
        "jobSubcategoryName": "后端",
    }, "social")
    jd = JDRecruitmentAdapter()._normalize_job({
        "publishId": 1,
        "positionName": "后端",
        "jobDirection": "技术方向",
        "jobDirectionCode": "T",
        "jobCategory": "软件开发类",
        "jobCategoryCode": "BE",
    }, "intern")
    kuaishou = KuaishouRecruitmentAdapter()._normalize_job(
        {"id": 1, "name": "后端", "positionCategoryCode": "J0012"}, "social", {"J0012": "工程类"}
    )
    meituan = MeituanRecruitmentAdapter()._normalize_job({
        "jobUnionId": 1,
        "name": "后端",
        "jobFamily": "技术类",
        "jobFamilyGroup": "软件",
    }, "social")
    pdd = PDDRecruitmentAdapter()._normalize_job({
        "id": 1,
        "name": "AI Infra研发工程师",
        "job": "technology",
        "jobName": "技术",
        "jobDuty": "训练平台",
        "serveRequirement": "熟悉 PyTorch",
    }, "campus")
    xiaomi = XiaomiRecruitmentAdapter()._normalize_job({
        "jobPostId": 1,
        "title": "Android 开发实习生",
        "type": 3,
        "levelOneDeptName": "手机部",
        "description": "客户端开发",
        "requirement": "熟悉 Kotlin",
        "url": "https://example.com/xiaomi/1",
    }, "intern")
    xiaohongshu = XiaohongshuRecruitmentAdapter()._normalize_job({
        "positionId": 1,
        "positionName": "多模态大模型算法工程师",
        "jobType": "大模型",
        "duty": "模型训练",
        "qualification": "熟悉 PyTorch",
    }, "social")
    deepseek = DeepSeekRecruitmentAdapter()._normalize_job({
        "id": "ds-1",
        "title": "Agent Harness 研发工程师",
        "commitment": "全职",
        "zhineng": {"id": 1, "name": "AI 核心系统研发"},
        "locations": [{"cityName": "Gongshu", "country": "China"}],
        "jobDescription": "<p>岗位职责</p><p>研发 Agent 系统</p><p>任职要求</p><p>熟悉 Python</p>",
        "_moka_portal_url": DeepSeekRecruitmentAdapter.PORTAL,
    }, "social")
    kimi = KimiRecruitmentAdapter()._normalize_job({
        "id": "kimi-1",
        "title": "大模型算法实习生",
        "commitment": "实习",
        "zhineng": {"id": 2, "name": "算法类"},
        "locations": [{"cityName": "Haidian", "country": "China"}],
        "jobDescription": "<p>岗位职责</p><p>模型训练</p><p>岗位要求</p><p>熟悉 PyTorch</p>",
        "_moka_portal_url": KimiRecruitmentAdapter.CAMPUS_PORTAL,
    }, "intern")
    zhipu = ZhipuRecruitmentAdapter()._normalize_job({
        "id": "zhipu-1",
        "title": "预训练算法工程师",
        "commitment": "全职",
        "zhineng": {"id": 3, "name": "算法研究"},
        "department": {"id": 4, "name": "基础模型部"},
        "jobDescription": "<p>职位描述</p><p>负责预训练</p><p>职位要求</p><p>熟悉 Transformer</p>",
        "_moka_portal_url": ZhipuRecruitmentAdapter.CAMPUS_PORTAL,
    }, "campus")
    minimax = MiniMaxRecruitmentAdapter()._normalize_job({
        "id": "minimax-1",
        "title": "大模型推理平台实习生",
        "description": "负责推理平台研发",
        "requirement": "熟悉 Python 与 Kubernetes",
        "publish_time": 1784270461089,
        "job_category": {
            "id": "infra",
            "name": "基础架构",
            "parent": {"id": "rd", "name": "研发", "parent": {"id": "tech", "name": "互联网 / 电子 / 网游"}},
        },
        "recruit_type": {"id": "intern", "name": "实习"},
        "city_list": [{"code": "CT_11", "name": "北京"}, {"code": "CT_125", "name": "上海"}],
        "_minimax_portal": "379481",
    }, "intern")
    tencent = TencentRecruitmentAdapter()._normalize_campus_job({
        "postId": 1,
        "positionFamily": 2,
        "detail": {"title": "后台开发", "tid": 2, "tidName": "技术", "subDirectionId": 12, "techTagName": "后台"},
    }, "campus")

    assert ali.official_taxonomy["level1"]["name"] == "技术类"
    assert baidu.official_taxonomy["level1"]["name"] == "技术"
    assert byte.official_taxonomy["level2"]["name"] == "后端"
    assert huawei.official_taxonomy["level3"]["name"] == "后端"
    assert jd.official_taxonomy["level2"]["name"] == "软件开发类"
    assert kuaishou.official_taxonomy["level1"]["name"] == "工程类"
    assert meituan.official_taxonomy["level2"]["name"] == "软件"
    assert pdd.official_taxonomy["level1"]["name"] == "技术"
    assert pdd.requirements == "熟悉 PyTorch"
    assert xiaomi.business_unit == "手机部"
    assert xiaomi.recruitment_type == "intern"
    assert xiaohongshu.official_taxonomy["level1"]["name"] == "大模型"
    assert deepseek.location == "杭州" and deepseek.requirements.endswith("熟悉 Python")
    assert kimi.recruitment_type == "intern" and kimi.employment_type == "实习" and kimi.location == "北京"
    assert zhipu.business_unit == "基础模型部" and zhipu.employment_type == "校招" and zhipu.requirements.endswith("熟悉 Transformer")
    assert minimax.official_taxonomy["level3"]["name"] == "基础架构"
    assert minimax.employment_type == "实习" and minimax.location == "北京、上海"
    assert tencent.official_taxonomy["level1"]["name"] == "技术"
    assert "raw_data" not in _dump_jobs([jd])[0]


def test_new_source_page_sizes_match_official_limits():
    assert PDDRecruitmentAdapter()._page_size(100) == 10
    assert XiaohongshuRecruitmentAdapter()._page_size(100) == 10


def test_moka_description_fallback_preserves_full_text():
    description, requirements = _split_moka_description("<p>负责模型训练与评测</p>")
    assert description == requirements == "负责模型训练与评测"
    assert _moka_is_intern({"title": "Agent Engineer（实习生）", "commitment": "全职"})
    assert not _moka_is_intern({"title": "Agent Engineer", "commitment": "全职"})


def test_domestic_filter_keeps_unlisted_chinese_and_mixed_locations():
    domestic = job("审核标注专员")
    domestic.location = "河北雄安新区"
    assert _is_domestic_job(domestic)
    mixed = job("国际业务")
    mixed.location = "北京市，上海市，美国"
    assert _is_domestic_job(mixed)
    overseas = job("海外销售")
    overseas.location = "慕尼黑"
    assert not _is_domestic_job(overseas)


def test_refresh_quality_blocks_data_loss():
    assert not _refresh_quality([], 100, "new", {})["publishable"]
    assert not _refresh_quality([{"source_job_id": "1", "title": "后端", "source_url": "u"}], 10, "new", {})["publishable"]
    complete = [{
        "source_job_id": str(index),
        "title": "后端",
        "source_url": "u",
        "description": "职责",
        "requirements": "要求",
        "official_taxonomy": {"level1": {"name": "技术"}},
        "role_family": "backend_software",
    } for index in range(10)]
    assert _refresh_quality(complete, 10, "same", {"schema_fingerprint": "same"})["publishable"]


def test_role_group_facets_and_filters_are_nested():
    jobs = [
        job("Java 后端开发").model_dump(),
        job("支付后端开发", description="使用 AI 工具提升研发效率").model_dump(),
        job("Web 前端开发").model_dump(),
        job("大模型算法工程师").model_dump(),
        job("产品经理", category="产品类").model_dump(),
        job("用户运营", category="运营类").model_dump(),
    ]

    result = _filter_saved_jobs(jobs, "", "", 1, 20)
    groups = {group["id"]: group for group in result["role_groups"]}
    assert groups["engineering"]["count"] == 4
    assert {family["id"] for family in groups["engineering"]["role_families"]} == {"backend_software", "frontend_fullstack", "ai_algorithm"}
    assert [family["id"] for family in groups["engineering"]["role_families"][:3]] == ["ai_algorithm", "backend_software", "frontend_fullstack"]

    engineering = _filter_saved_jobs(jobs, "", "", 1, 20, role_group="engineering")
    assert engineering["total"] == 4
    backend = _filter_saved_jobs(jobs, "", "", 1, 20, role_group="engineering", role_family="backend_software")
    assert {item["title"] for item in backend["items"]} == {"Java 后端开发", "支付后端开发"}

    ai_hot = _filter_saved_jobs(jobs, "", "", 1, 20, ai_hot=True)
    assert [item["title"] for item in ai_hot["items"]] == ["大模型算法工程师"]


if __name__ == "__main__":
    test_primary_role_exclusions_and_multi_axis_tags()
    test_official_taxonomy_can_fill_an_ambiguous_title()
    test_live_title_edge_cases_use_specific_families()
    test_ai_roles_respect_primary_function_and_three_way_split()
    test_interviews_share_role_taxonomy_with_structured_fallbacks()
    test_source_specific_taxonomy_mapping()
    test_new_source_page_sizes_match_official_limits()
    test_moka_description_fallback_preserves_full_text()
    test_domestic_filter_keeps_unlisted_chinese_and_mixed_locations()
    test_refresh_quality_blocks_data_loss()
    test_role_group_facets_and_filters_are_nested()
