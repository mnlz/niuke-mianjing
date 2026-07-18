import json
import re
from functools import lru_cache
from pathlib import Path


def load_data_from_json(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


@lru_cache(maxsize=1)
def _company_mapping():
    company_json_path = Path(__file__).parent.parent / "company.json"
    data = load_data_from_json(company_json_path)
    company_aliases = data.get("company_aliases", {})

    reverse_mapping = {}
    for standard_name, aliases in company_aliases.items():
        reverse_mapping[standard_name.lower()] = standard_name
        for alias in aliases:
            reverse_mapping[alias.lower()] = standard_name
    return reverse_mapping


def _match_known_company(text: str) -> str:
    text_lower = text.lower()
    sorted_aliases = sorted(_company_mapping().keys(), key=len, reverse=True)
    for alias in sorted_aliases:
        if alias and alias in text_lower:
            return _company_mapping()[alias]
    return ""


_EXPLICIT_PATTERNS = [
    re.compile(r"(?:面试公司|公司名称|面试企业)\s*[：:]\s*([^\n\r🕐💻❓🙌]+)"),
]

_TITLE_PREFIX_PATTERNS = [
    re.compile(r"^([A-Za-z0-9\u4e00-\u9fa5（）()·&]{2,30}?)[\-—_｜|:：]"),
]

_TITLE_MARKERS = (
    "Java",
    "java",
    "前端",
    "后端",
    "客户端",
    "测试",
    "测开",
    "大模型",
    "算法",
    "Android",
    "安卓",
    "iOS",
    "C++",
    "Python",
    "Go",
    "golang",
    "Golang",
    "软件开发",
    "服务端",
    "全栈",
    "运维",
    "AI",
    "ai",
    "ai初创",
    "Agent",
    "Unity",
    "unity",
    "游戏客户端",
    "UE游开",
    "一面",
    "二面",
    "三面",
    "面经",
    "凉经",
    "笔试",
    "面试",
)

_BAD_COMPANY_WORDS = {
    "大厂",
    "小厂",
    "某厂",
    "某公司",
    "未知公司",
    "面试官",
    "技术面",
    "一面",
    "二面",
    "三面",
    "hr",
    "ai",
    "java",
    "python",
    "agent",
    "android",
    "ios",
    "软件",
    "问题",
    "大模型",
    "考虑",
    "近期",
    "后端",
    "前端",
    "测试",
    "算法",
    "运维",
    "运维岗",
    "双非",
    "海口",
}

_BAD_COMPANY_FRAGMENTS = (
    "http",
    "www.",
    "面试",
    "暑期",
    "秋招",
    "春招",
    "校招",
    "实习必备",
    "大厂",
    "小厂",
    "社招",
    "鸿蒙生态",
    "事业部",
    "最终",
    "复习",
    "指南",
    "总结",
    "分享",
    "记录",
    "第一次",
    "某",
    "怎么",
    "如何",
    "为什么",
    "threadlocal",
)

_COMPANY_NORMALIZE_OVERRIDES = {
    "bilibil": "哔哩哔哩",
    "b站": "哔哩哔哩",
    "tme": "腾讯",
    "tme后台": "腾讯",
    "企微": "腾讯",
    "淘宝": "阿里巴巴",
    "淘宝闪购": "阿里巴巴",
    "掌上先机": "慧策",
    "爱学习集团": "爱学习",
    "腾娱": "腾娱互动",
    "浩鲸": "浩鲸科技",
    "中科曙光base天津": "中科曙光",
    "北京知道创宇（成都）": "知道创宇",
    "奥比中光（佛山）": "奥比中光",
    "钛腾（莆田）": "钛腾",
    "韶音科技提前批": "韶音科技",
    "遥望科技（": "遥望科技",
    "智谱": "智谱华章",
    "小药药武汉": "小药药",
    "武汉小药药": "小药药",
    "嘉立创深圳": "嘉立创",
    "宁波银行金科": "宁波银行",
    "西安teleperformance": "Teleperformance",
    "futurus北京未来黑科技": "北京未来黑科技",
    "嘉为python": "嘉为",
    "神漫文化武汉分公司it": "神漫文化",
    "高标智能it": "高标智能",
    "分叉智能科技（影刀）": "影刀",
    "分叉智能科技(影刀)": "影刀",
    "啊哈娱乐（伍六七）": "伍六七",
    "啊哈娱乐(伍六七)": "伍六七",
    "佳杰科技(佳杰云星)": "佳杰科技",
    "佳杰科技（佳杰云星）": "佳杰科技",
}

_LEGAL_COMPANY_SUFFIXES = ("有限责任公司", "股份有限公司", "有限公司")

_BAD_COMPANY_NAMES = {
    "ai初创",
    "ai项目实施",
    "ba",
    "js千字",
    "yrkj数字",
    "上海agent初创",
    "成都agent",
    "今天投java面了一家20",
    "关于人生第一场",
    "关于知识库的一些个人",
    "凉面",
    "初创公司",
    "别再只刷",
    "双非28二战鹅",
    "双非在线等",
    "双非本科逆袭",
    "另辟蹊径的",
    "小公司",
    "深圳初创",
    "应届生必看",
    "快去可灵",
    "我以为",
    "整理一下27",
    "最有料（",
    "机器人厂",
    "第二次",
    "练完这398道",
    "网工",
    "记一次因threadlocal未清理导致的内存泄漏",
    "跳槽被问烂的",
    "近期事件有关的线上",
}


def _clean_candidate(value: str) -> str:
    value = re.split(r"(?:🕐|💻|❓|🙌|面试时间|面试岗位|面试问题|面试感想)", value, maxsplit=1)[0]
    value = re.sub(r"^\s*(?:📍|公司|面试公司)[：:：\s]*", "", value)
    value = re.sub(r"\s+\d+\s*[hH].*$", "", value)
    value = re.sub(
        r"(?:一面|二面|三面|四面|笔试|面经|凉经|面试|Java|前端|后端|客户端|测试|测开|开发|实习|工程师|Android|安卓|iOS|C\+\+|Python|Go|golang|Golang|AI|Agent|大模型).*$",
        "",
        value,
    )
    value = re.sub(r"(?:系统|智能|研发|IT岗|it岗|最终|了解性)$", "", value)
    if re.search(r"[A-Za-z]", value):
        value = re.sub(r"[一二三四]$", "", value)
    return value.strip(" \t\r\n，,。；;：:[]【】\"'")


def _clean_company_value(value: str) -> str:
    return (value or "").strip(" \t\r\n，,。；;：:[]【】\"'")


def normalize_company_name(company: str) -> str:
    company = _clean_company_value(company or "")
    if not company:
        return "未知公司"

    lowered = company.lower()
    if lowered in _BAD_COMPANY_NAMES:
        return "未知公司"

    if lowered in _COMPANY_NORMALIZE_OVERRIDES:
        return _COMPANY_NORMALIZE_OVERRIDES[lowered]

    company = re.sub(r"(.+?公司)(?:[\u4e00-\u9fa5]{1,8}分公司)$", r"\1", company)
    company = re.sub(r"(.+?公司)（[\u4e00-\u9fa5A-Za-z0-9]+）$", r"\1", company)
    company = re.sub(r"(?:20\d{2})?(?:Web|web|Python|python)$", "", company)
    company = re.sub(r"(?<=[\u4e00-\u9fa5])(?:IT|it)$", "", company)
    for suffix in _LEGAL_COMPANY_SUFFIXES:
        if company.endswith(suffix) and len(company) > len(suffix) + 1:
            company = company[: -len(suffix)]
            break

    lowered = company.lower()
    if lowered in _COMPANY_NORMALIZE_OVERRIDES:
        return _COMPANY_NORMALIZE_OVERRIDES[lowered]

    known = _match_known_company(company)
    if known and known != "未知公司":
        return known

    if not _is_good_candidate(company):
        return "未知公司"
    return company


def _is_good_candidate(value: str) -> bool:
    if not (2 <= len(value) <= 30):
        return False
    lowered = value.lower()
    if lowered in _BAD_COMPANY_WORDS:
        return False
    if any(fragment in lowered for fragment in _BAD_COMPANY_FRAGMENTS):
        return False
    if re.search(r"^\d|[？?]", value):
        return False
    if not re.fullmatch(r"[A-Za-z0-9\u4e00-\u9fa5（）()·&]+", value):
        return False
    return bool(re.search(r"[\u4e00-\u9fa5A-Za-z]", value))


def _standardize_or_literal(candidate: str) -> str:
    company = normalize_company_name(_clean_candidate(candidate))
    return "" if company == "未知公司" else company


def _extract_explicit_company(text: str) -> str:
    for pattern in _EXPLICIT_PATTERNS:
        match = pattern.search(text)
        if match:
            company = _standardize_or_literal(match.group(1))
            if company:
                return company
    return ""


def _extract_title_company(title: str) -> str:
    title = re.sub(r"^(?:\d{4}[./-]\d{1,2}(?:[./-]\d{1,2})?|\d{1,2}[./-]\d{1,2}|0\d{3})\s*", "", title.strip())
    for pattern in _TITLE_PREFIX_PATTERNS:
        match = pattern.search(title)
        if match:
            company = _standardize_or_literal(match.group(1))
            if company:
                return company
    marker_positions = [title.find(marker) for marker in _TITLE_MARKERS if title.find(marker) > 1]
    if marker_positions:
        company = _standardize_or_literal(title[: min(marker_positions)])
        if company:
            return company
    return ""


def extract_company_post(title, content: str = ""):
    title = title or ""
    content = content or ""

    known = _match_known_company(title)
    if known and known != "未知公司":
        return known

    explicit = _extract_explicit_company(content[:1200])
    if explicit:
        return explicit

    title_company = _extract_title_company(title)
    if title_company:
        return title_company

    return "未知公司"
