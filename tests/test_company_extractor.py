import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from niuke_mianjing_backend.utils.extractor import extract_company_post, normalize_company_name


def test_extracts_company_from_explicit_content_field():
    assert extract_company_post(
        "原来面试也能很轻松",
        "📍面试公司：北京聚智高信息技术有限公司安徽分公司🕐面试时间：七月初",
    ) == "北京聚智高信息技术"


def test_extracts_company_from_title_prefix():
    assert extract_company_post("掌上先机-Java开发-1面-06.18") == "慧策"


def test_does_not_treat_generic_small_factory_as_company():
    assert extract_company_post("7月7日 东莞小厂面经") == "未知公司"


def test_ignores_leading_date_before_company():
    assert extract_company_post("7.8联影 Agent 开发一面") == "联影"


def test_normalizes_company_aliases():
    assert normalize_company_name("bilibil") == "哔哩哔哩"
    assert normalize_company_name("B站") == "哔哩哔哩"
    assert normalize_company_name("tme后台") == "腾讯"
    assert normalize_company_name("企微") == "腾讯"
    assert normalize_company_name("淘宝闪购") == "阿里巴巴"


def test_normalizes_branch_and_related_names():
    assert normalize_company_name("北京聚智高信息技术有限公司安徽分公司") == "北京聚智高信息技术"
    assert normalize_company_name("上海威派格智慧水务股份有限公司") == "上海威派格智慧水务"
    assert normalize_company_name("北京聚智高信息技术有限公司") == "北京聚智高信息技术"
    assert normalize_company_name("宁波神州泰岳锐智信息科技有限公司") == "宁波神州泰岳锐智信息科技"
    assert normalize_company_name("深圳美云集网络科技有限责任公司") == "深圳美云集网络科技"
    assert normalize_company_name("分叉智能科技（影刀）") == "影刀"
    assert normalize_company_name("啊哈娱乐（伍六七）") == "伍六七"
    assert normalize_company_name("掌上先机") == "慧策"
    assert normalize_company_name("爱学习集团") == "爱学习"
    assert normalize_company_name("中科曙光base天津") == "中科曙光"
    assert normalize_company_name("溢信科技2026Web") == "溢信科技"
    assert normalize_company_name("北京知道创宇（成都）") == "知道创宇"
    assert normalize_company_name("奥比中光（佛山）") == "奥比中光"
    assert normalize_company_name("钛腾（莆田）") == "钛腾"
    assert normalize_company_name("韶音科技提前批") == "韶音科技"
    assert normalize_company_name("遥望科技（") == "遥望科技"
    assert normalize_company_name("智谱") == "智谱华章"
    assert normalize_company_name("小药药武汉") == "小药药"
    assert normalize_company_name("武汉小药药") == "小药药"
    assert normalize_company_name("嘉立创深圳") == "嘉立创"
    assert normalize_company_name("宁波银行金科") == "宁波银行"
    assert normalize_company_name("西安teleperformance") == "Teleperformance"
    assert normalize_company_name("futurus北京未来黑科技") == "北京未来黑科技"


def test_rejects_title_fragments_as_company():
    assert normalize_company_name("近期事件有关的线上") == "未知公司"
    assert normalize_company_name("记一次因ThreadLocal未清理导致的内存泄漏") == "未知公司"
    assert normalize_company_name("今天投java面了一家20") == "未知公司"
    assert normalize_company_name("深圳初创") == "未知公司"
    assert normalize_company_name("成都agent") == "未知公司"


if __name__ == "__main__":
    test_extracts_company_from_explicit_content_field()
    test_extracts_company_from_title_prefix()
    test_does_not_treat_generic_small_factory_as_company()
    test_ignores_leading_date_before_company()
    test_normalizes_company_aliases()
    test_normalizes_branch_and_related_names()
    test_rejects_title_fragments_as_company()
