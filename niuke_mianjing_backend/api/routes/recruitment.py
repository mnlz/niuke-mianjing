import re
import time
from datetime import datetime
from types import SimpleNamespace
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, File, Header, Query, UploadFile
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from niuke_mianjing_backend.api.middleware.error_handler import BadRequestException, NotFoundException
from niuke_mianjing_backend.api.routes.user_auth import optional_user_id, require_public_window, require_user_id
from niuke_mianjing_backend.api.security import is_valid_admin_token
from niuke_mianjing_backend.config import settings
from niuke_mianjing_backend.crawler.recruitment import create_adapter, list_adapters
from niuke_mianjing_backend.repositories.niuke_repo import NiukeRepository
from niuke_mianjing_backend.repositories.ai_report_repo import AIReportRepository
from niuke_mianjing_backend.repositories.recruitment_job_repo import RecruitmentJobRepository
from niuke_mianjing_backend.schemas import ApiResponse
from niuke_mianjing_backend.services.recruitment_ai import call_ai_report, interviews_brief, job_brief, jobs_brief
from niuke_mianjing_backend.services.resume_parser import parse_resume_pdf as parse_resume_content


router = APIRouter(prefix="/api/recruitment", tags=["公开招聘岗位"])
recruitment_job_repo = RecruitmentJobRepository()
ai_report_repo = AIReportRepository()
niuke_repo = NiukeRepository()


class RecruitmentRefreshRequest(BaseModel):
    source: str = Field("all", description="招聘来源，all 表示全部")
    recruitment_type: str = Field("all", description="招聘类型，all 表示该来源支持的全部类型")
    max_pages: Optional[int] = Field(None, ge=1, le=200, description="可选：限制每个来源类型最多刷新页数")


class RecruitmentAIReportRequest(BaseModel):
    report_type: str = Field(..., description="job/company_compare/job_interviews/resume_job/full/resume_match")
    source: str = "tencent"
    recruitment_type: str = "campus"
    source_job_id: Optional[str] = None
    track: str = ""
    company: str = ""
    resume: str = ""
    compare_sources: List[str] = Field(default_factory=list)
    selected_interview_ids: List[int] = Field(default_factory=list)

SOURCE_META = {
    "alibaba": {
        "source": "alibaba",
        "company": "阿里巴巴",
        "description": "阿里巴巴招聘官网公开岗位",
        "logo": "/company-logos/阿里巴巴.svg",
        "supported_recruitment_types": ["intern"],
    },
    "baidu": {
        "source": "baidu",
        "company": "百度",
        "description": "百度招聘官网公开岗位",
        "logo": "/company-logos/icon_百度logo.svg",
        "supported_recruitment_types": ["campus", "intern", "social"],
    },
    "bytedance": {
        "source": "bytedance",
        "company": "字节跳动",
        "description": "字节跳动招聘官网公开岗位",
        "logo": "/company-logos/字节跳动.svg",
        "supported_recruitment_types": ["campus", "intern", "social"],
    },
    "huawei": {
        "source": "huawei",
        "company": "华为",
        "description": "华为招聘官网公开岗位",
        "logo": "/company-logos/华为.svg",
        "supported_recruitment_types": ["campus", "intern", "social"],
    },
    "jd": {
        "source": "jd",
        "company": "京东",
        "description": "京东招聘官网公开岗位",
        "logo": "/company-logos/jd.svg",
        "supported_recruitment_types": ["campus", "intern"],
    },
    "kuaishou": {
        "source": "kuaishou",
        "company": "快手",
        "description": "快手招聘官网公开岗位",
        "logo": "/company-logos/快手.svg",
        "supported_recruitment_types": ["intern", "social"],
    },
    "meituan": {
        "source": "meituan",
        "company": "美团",
        "description": "美团招聘官网公开岗位",
        "logo": "/company-logos/美团.svg",
        "supported_recruitment_types": ["campus", "intern", "social"],
    },
    "tencent": {
        "source": "tencent",
        "company": "腾讯",
        "description": "腾讯招聘官网公开岗位",
        "logo": "/company-logos/腾讯-01.svg",
        "supported_recruitment_types": ["campus", "intern", "social"],
    },
}

RECRUITMENT_TYPES = {
    "campus": {"id": "campus", "name": "校招"},
    "intern": {"id": "intern", "name": "实习"},
    "social": {"id": "social", "name": "社招"},
}

TRACKS = {
    "backend": {
        "id": "backend",
        "name": "后端开发",
        "description": "服务端、分布式系统与基础架构",
        "keywords": ["后端开发", "后端研发", "后端", "服务端开发", "服务端研发", "服务端", "Java开发", "Java后端", "后台开发", "Golang", "Go"],
    },
    "frontend": {
        "id": "frontend",
        "name": "前端开发",
        "description": "Web、跨端与前端工程化",
        "keywords": ["前端", "Web", "React", "小程序"],
    },
    "client": {
        "id": "client",
        "name": "客户端开发",
        "description": "Android、iOS、游戏客户端与引擎",
        "keywords": ["客户端", "Android", "iOS", "游戏开发"],
    },
    "testing": {
        "id": "testing",
        "name": "测试",
        "description": "测试开发、质量平台与自动化",
        "keywords": ["测试开发", "测试", "质量", "QA"],
    },
    "data": {
        "id": "data",
        "name": "数据开发",
        "description": "大数据、数据平台与数据分析",
        "keywords": ["数据开发", "大数据", "数据工程", "数据分析"],
    },
    "ai": {
        "id": "ai",
        "name": "人工智能/算法",
        "description": "大模型、机器学习、推荐与搜索",
        "keywords": ["大模型", "算法", "机器学习", "人工智能"],
    },
}

CACHE_TTL_SECONDS = 300
CLASSIFICATION_CACHE_VERSION = "tracks-v2"
_page_cache: Dict[Tuple[str, str, str, str, int, int, str], Tuple[float, dict]] = {}

DOMESTIC_LOCATION_HINTS = {
    "中国",
    "中国大陆",
    "北京",
    "上海",
    "深圳",
    "杭州",
    "广州",
    "成都",
    "武汉",
    "南京",
    "西安",
    "苏州",
    "重庆",
    "天津",
    "厦门",
    "长沙",
    "合肥",
    "全国",
    "国内",
    "远程",
}
OVERSEAS_LOCATION_HINTS = {
    "新加坡",
    "Singapore",
    "美国",
    "United States",
    "London",
    "伦敦",
    "Dubai",
    "迪拜",
    "麦纳麦",
    "Manama",
    "Japan",
    "日本",
    "Korea",
    "韩国",
}

NEGATIVE_TITLE_HINTS = ["前端", "客户端", "测试", "QA", "运营", "产品经理", "销售", "市场", "设计"]
BACKEND_TITLE_HINTS = ["后端开发", "后端研发", "服务端开发", "服务端研发", "Java开发", "Java后端", "后台开发"]
BACKEND_GENERAL_HINTS = ["后端", "后台", "服务端", "Java", "Golang", "Go", "Server", "Backend"]

GENERIC_OFFICIAL_CATEGORIES = {
    "",
    "技术",
    "技术类",
    "技术方向",
    "研发",
    "研发族",
    "软件",
    "综合岗位",
    "J0011",
    "J0012",
    "JFC1",
}

DISPLAY_CATEGORY_HINTS = [
    ("运营", ["运营", "产品运营", "用户增长", "内容治理", "商家", "达人治理", "策略负责人"]),
    ("产品", ["产品经理", "产品专家", "产品策划", "策划", "产品类", "硬件产品"]),
    ("市场营销", ["市场", "营销", "媒介", "品牌"]),
    ("销售/商务", ["销售", "商务", "客户经理", "渠道", "BD", "商业化"]),
    ("项目管理", ["项目管理", "PMO"]),
    ("商业分析", ["商业分析", "战略分析"]),
    ("设计", ["设计", "UX", "交互", "视觉", "ID与UX"]),
    ("硬件", ["硬件", "芯片", "嵌入式", "无人机飞行器"]),
    ("法务", ["法务", "律师", "合规", "知识产权"]),
    ("财经", ["财经", "财务", "会计"]),
    ("人力资源", ["HRBP", "人力资源"]),
]

TRACK_CLASSIFIERS = {
    "backend": {
        "title": [
            "后端开发", "后端研发", "后端工程师", "后端实习生", "后端", "后台开发", "后台研发", "后台",
            "服务端开发", "服务端研发", "服务端", "Java开发", "Java后端", "Java工程师", "Go开发",
            "Golang", "Server", "Backend", "数据库内核", "数据库研发", "分布式系统", "系统架构",
            "全栈开发", "全栈工程师", "平台开发工程师", "操作系统", "编译器", "数据存储",
            "存储研发", "存储系统", "计算系统", "基础架构软件",
        ],
        "category": ["后端", "后台", "服务端", "Backend", "基础架构"],
        "body": ["高并发", "微服务", "分布式", "服务治理", "接口开发", "存储系统", "数据库", "缓存"],
        "negative": ["前端", "客户端", "测试", "运营", "产品经理", "销售", "市场", "设计"],
    },
    "frontend": {
        "title": [
            "前端开发", "前端研发", "前端工程师", "前端实习生", "Web前端", "Web开发", "H5开发",
            "React", "Vue", "Node.js", "小程序", "低代码平台前端",
        ],
        "category": ["前端", "Frontend"],
        "body": ["React", "Vue", "TypeScript", "JavaScript", "浏览器", "Web端", "页面性能"],
        "negative": ["后端", "服务端", "客户端", "测试", "运营", "产品经理"],
    },
    "client": {
        "title": [
            "客户端开发", "客户端研发", "客户端工程师", "客户端实习生", "Android", "安卓", "iOS", "移动端", "鸿蒙",
            "Flutter", "端开发", "游戏客户端", "PC客户端", "移动客户端",
        ],
        "category": ["客户端", "Client", "移动端"],
        "body": ["Android", "iOS", "Flutter", "Objective-C", "Swift", "Kotlin", "移动应用"],
        "negative": ["后端", "服务端", "前端", "测试", "运营", "产品经理"],
    },
    "testing": {
        "title": ["测试开发", "测试工程师", "测试", "质量工程师", "质量效能", "QA", "SDET", "自动化测试"],
        "category": ["测试", "质量", "Testing", "QA"],
        "body": ["自动化测试", "测试平台", "质量保障", "稳定性测试", "性能测试", "测试工具"],
        "negative": ["产品经理", "运营", "销售"],
    },
    "data": {
        "title": [
            "数据开发", "数据研发", "数据工程师", "大数据开发", "大数据研发", "数据平台", "数据仓库",
            "数仓", "数据湖", "实时计算", "离线计算", "ETL", "BI工程师", "数据治理",
        ],
        "category": ["大数据", "数据工程", "数据开发", "数据平台", "Data", "数据"],
        "body": ["Hadoop", "Spark", "Flink", "Hive", "数仓", "数据链路", "数据模型", "数据治理", "ETL"],
        "negative": ["数据分析师", "策略运营", "产品经理"],
    },
    "ai": {
        "title": [
            "算法", "算法工程师", "算法实习生", "算法研究", "机器学习", "深度学习", "人工智能", "大模型",
            "AIGC", "LLM", "NLP", "自然语言处理", "计算机视觉", "CV", "多模态", "推荐算法",
            "搜索算法", "风控算法", "语音大模型", "图像生成", "模型训练", "模型推理", "Agent算法",
            "AI", "AI算法", "AI应用", "AI模型", "AI Infra", "AI安全", "AI Agent", "Agent Infra",
            "Agent优化", "模型", "训练", "推理", "评测", "运筹优化研究员",
        ],
        "category": ["算法", "机器学习", "人工智能", "大模型", "Algorithm", "AI"],
        "body": ["模型训练", "模型推理", "深度学习", "机器学习", "多模态", "推荐系统", "大语言模型", "Prompt"],
        "negative": ["产品经理", "运营", "销售", "市场"],
    },
}

ENGLISH_TOKEN_PATTERNS = {
    "go": re.compile(r"(?<![a-z0-9])go(?![a-z0-9])", re.IGNORECASE),
    "web": re.compile(r"(?<![a-z0-9])web(?![a-z0-9])", re.IGNORECASE),
    "qa": re.compile(r"(?<![a-z0-9])qa(?![a-z0-9])", re.IGNORECASE),
    "cv": re.compile(r"(?<![a-z0-9])cv(?![a-z0-9])", re.IGNORECASE),
    "ai": re.compile(r"(?<![a-z0-9])ai(?![a-z0-9])", re.IGNORECASE),
}


def _is_domestic_job(item) -> bool:
    location_only = str(item.location or "")
    location_text = " ".join(
        str(value or "")
        for value in [
            item.location,
            item.country,
            item.business_unit,
            item.title,
        ]
    )
    if any(hint in location_text for hint in OVERSEAS_LOCATION_HINTS):
        return False
    if location_only:
        return any(hint in location_only for hint in DOMESTIC_LOCATION_HINTS)
    if not item.location and not item.country:
        return True
    return any(hint in location_text for hint in DOMESTIC_LOCATION_HINTS)


def _contains_hint(text: str, hint: str) -> bool:
    lowered = hint.lower()
    if lowered in ENGLISH_TOKEN_PATTERNS:
        return bool(ENGLISH_TOKEN_PATTERNS[lowered].search(text))
    return lowered in text.lower()


def _field_score(text: str, hints: List[str], weight: int) -> int:
    return sum(weight for hint in hints if _contains_hint(text, hint))


def _classification_text(item) -> Tuple[str, str, str]:
    title = str(item.title or "")
    category = " ".join(str(value or "") for value in [item.category, item.job_family, item.product])
    body = " ".join(
        str(value or "")
        for value in [
            item.description,
            item.requirements,
            item.highlights,
            item.business_unit,
        ]
    )
    return title, category, body


def _track_scores(item) -> Dict[str, int]:
    title, category, body = _classification_text(item)
    scores: Dict[str, int] = {}
    for track_id, config in TRACK_CLASSIFIERS.items():
        score = 0
        score += _field_score(title, config["title"], 100)
        score += _field_score(category, config["category"], 70)
        score += _field_score(body, config["body"], 16)
        score -= _field_score(title, config["negative"], 120)
        scores[track_id] = score
    return scores


def _infer_track(item) -> Tuple[Optional[str], Optional[str], int]:
    scores = _track_scores(item)
    if not scores:
        return None, None, 0
    track_id, score = max(scores.items(), key=lambda entry: entry[1])
    if score < 70:
        return None, None, score
    return track_id, TRACKS[track_id]["name"], score


def _official_category(item) -> str:
    return str(item.category or item.job_family or "").strip()


def _is_generic_official_category(value: str) -> bool:
    return value in GENERIC_OFFICIAL_CATEGORIES or bool(re.fullmatch(r"J(?:FC)?\d+", value))


def _display_category_from_text(item) -> Optional[str]:
    text = " ".join(
        str(value or "")
        for value in [
            item.title,
            item.category,
            item.job_family,
            item.business_unit,
            item.product,
        ]
    )
    for label, hints in DISPLAY_CATEGORY_HINTS:
        if any(_contains_hint(text, hint) for hint in hints):
            return label
    return None


def _annotate_job(item):
    track_id, track_name, _ = _infer_track(item)
    item.inferred_track = track_id
    item.inferred_track_name = track_name
    official = _official_category(item)
    if track_name:
        item.display_category = track_name
    else:
        inferred_display = _display_category_from_text(item)
        if inferred_display:
            item.display_category = inferred_display
        elif official and not _is_generic_official_category(official):
            item.display_category = official
        else:
            item.display_category = "综合岗位"
    return item


def _dump_jobs(items) -> List[dict]:
    return [
        _annotate_job(item).model_dump(mode="json", exclude={"raw_data"})
        for item in items
    ]


def _as_job_object(job: dict):
    return SimpleNamespace(**job)


def _annotate_job_dict(job: dict) -> dict:
    item = _as_job_object(job)
    track_id, track_name, _ = _infer_track(item)
    official = _official_category(item)
    job["inferred_track"] = job.get("inferred_track") or track_id
    job["inferred_track_name"] = job.get("inferred_track_name") or track_name
    if not job.get("display_category"):
        if track_name:
            job["display_category"] = track_name
        else:
            inferred_display = _display_category_from_text(item)
            job["display_category"] = inferred_display or (official if official and not _is_generic_official_category(official) else "综合岗位")
    return job


def _score_job(item, track: str, keyword: str) -> int:
    title = item.title or ""
    category = " ".join(str(value or "") for value in [item.category, item.job_family])
    body = " ".join(str(value or "") for value in [item.description, item.requirements, item.highlights])
    score = 0
    if keyword:
        score += 90 if keyword.lower() in title.lower() else 0
        score += 30 if keyword.lower() in category.lower() else 0
        score += 10 if keyword.lower() in body.lower() else 0
    if track:
        track_scores = _track_scores(item)
        score += track_scores.get(track, 0)
        inferred_track, _, inferred_score = _infer_track(item)
        if inferred_track and inferred_track != track:
            score -= max(inferred_score, 120)
        if inferred_track == track:
            score += 80
    return score


def _score_saved_job(job: dict, track: str, keyword: str) -> int:
    return _score_job(_as_job_object(job), track, keyword)


def _filter_saved_jobs(jobs: List[dict], keyword: str, track: str, page: int, page_size: int) -> dict:
    keyword = keyword.strip()
    filtered = [_annotate_job_dict({**job}) for job in jobs]
    if keyword:
        lowered = keyword.lower()
        filtered = [
            job for job in filtered
            if lowered in " ".join(
                str(job.get(key) or "")
                for key in ("title", "category", "job_family", "description", "requirements", "business_unit")
            ).lower()
        ]
    if track:
        filtered = [
            job for job in filtered
            if (job.get("inferred_track") == track or _score_saved_job(job, track, keyword) > 0)
        ]
    if keyword or track:
        filtered.sort(
            key=lambda job: (
                _score_saved_job(job, track, keyword),
                str(job.get("updated_at") or job.get("crawled_at") or job.get("synced_at") or ""),
            ),
            reverse=True,
        )
    start = (page - 1) * page_size
    return {
        "items": filtered[start:start + page_size],
        "total": len(filtered),
        "has_more": start + page_size < len(filtered),
    }


def _interview_keywords(job: dict) -> List[str]:
    values = [
        job.get("inferred_track_name"),
        job.get("display_category"),
        job.get("category"),
        job.get("job_family"),
        job.get("title"),
    ]
    words = []
    for value in values:
        text = str(value or "")
        if "后端" in text or "后台" in text or "服务端" in text:
            words.extend(["后端", "服务端", "Java", "Go"])
        elif "前端" in text:
            words.extend(["前端", "Web"])
        elif "算法" in text or "AI" in text or "大模型" in text:
            words.extend(["算法", "AI", "大模型"])
        elif "测试" in text:
            words.extend(["测试", "测开"])
        elif "数据" in text:
            words.extend(["数据", "大数据"])
    return list(dict.fromkeys(words or [str(job.get("title") or "")[:20]]))


def _interview_post_keywords(job: dict) -> List[str]:
    track = job.get("inferred_track") or ""
    if track == "backend":
        return ["后端", "服务端", "后台", "Java", "Go"]
    if track == "frontend":
        return ["前端", "Web"]
    if track == "client":
        return ["客户端", "Android", "iOS"]
    if track == "testing":
        return ["测试", "测开", "质量"]
    if track == "data":
        return ["数据", "大数据"]
    if track == "ai":
        return ["算法", "AI", "大模型", "机器学习"]
    return [job.get("inferred_track_name") or job.get("display_category") or job.get("category") or ""]


async def _job_samples(source: str, recruitment_type: str, track: str, limit: int = 8) -> List[dict]:
    source = source.strip().lower()
    recruitment_type = recruitment_type.strip().lower() or "campus"
    track = track.strip().lower()
    if source not in SOURCE_META:
        raise BadRequestException(f"不支持的招聘来源：{source}")
    if recruitment_type not in RECRUITMENT_TYPES:
        raise BadRequestException(f"不支持的招聘类型：{recruitment_type}")
    if track and track not in TRACKS:
        raise BadRequestException(f"不支持的岗位方向：{track}")
    jobs = await recruitment_job_repo.list_latest_jobs(source, recruitment_type)
    return _filter_saved_jobs(jobs, "", track, 1, limit)["items"]


async def _related_interviews_for_jobs(jobs: List[dict], limit: int = 12) -> List[dict]:
    if not jobs:
        return []
    company = jobs[0]["company"]
    keywords = []
    post_keywords = []
    for job in jobs[:3]:
        keywords.extend(_interview_keywords(job))
        post_keywords.extend(_interview_post_keywords(job))
    return await niuke_repo.search_related_interviews(
        company,
        list(dict.fromkeys(keywords)),
        limit,
        list(dict.fromkeys(post_keywords)),
    )


def _fetch_jobs(source: str, keyword: str, track: str, recruitment_type: str, page: int, page_size: int) -> dict:
    cache_key = (source, keyword, track, recruitment_type, page, page_size, CLASSIFICATION_CACHE_VERSION)
    cached = _page_cache.get(cache_key)
    if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
        return {**cached[1], "cached": True}

    adapter = create_adapter(source, sleep_interval=0.05)
    if not track and not keyword:
        request_size = min(adapter.max_page_size, max(page_size * max(page, 1) * 3, page_size))
        result = adapter.fetch_page(
            page=1,
            page_size=request_size,
            keyword="",
            recruitment_type=recruitment_type,
            include_detail=True,
        )
        domestic_items = [item for item in result.items if _is_domestic_job(item)]
        total = result.total
        has_more = result.has_more
        start = (page - 1) * page_size
        payload = {
            "source": source,
            "company": adapter.company,
            "track": None,
            "recruitment_type": recruitment_type,
            "keywords": [],
            "items": _dump_jobs(domestic_items[start:start + page_size]),
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_more": has_more,
            "cached": False,
        }
        _page_cache[cache_key] = (time.time(), payload)
        return payload

    keywords: List[str] = [keyword] if keyword else list((TRACKS.get(track) or {}).get("keywords") or [""])
    request_size = min(adapter.max_page_size, max(page_size * max(page, 1) * 3, 24))
    results = []
    for item in keywords:
        results.append(
            adapter.fetch_page(
                page=1,
                page_size=request_size,
                keyword=item,
                recruitment_type=recruitment_type,
                include_detail=True,
            )
        )
    unique_items = {}
    for result in results:
        for item in result.items:
            if _is_domestic_job(item):
                unique_items.setdefault(item.source_job_id, item)
    scored_items = [
        (item, _score_job(item, track, keyword))
        for item in unique_items.values()
    ]
    if track:
        scored_items = [
            (item, score)
            for item, score in scored_items
            if _infer_track(item)[0] == track and score > 0
        ]
    sorted_items = [
        item for item, _ in sorted(
            scored_items,
            key=lambda entry: (entry[1], entry[0].updated_at or entry[0].crawled_at),
            reverse=True,
        )
    ]
    start = (page - 1) * page_size
    items = sorted_items[start:start + page_size]
    total = len(sorted_items)
    payload = {
        "source": source,
        "company": adapter.company,
        "track": track or None,
        "recruitment_type": recruitment_type,
        "keywords": keywords if track and not keyword else [],
        "items": _dump_jobs(items),
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": start + page_size < len(sorted_items),
        "cached": False,
    }
    _page_cache[cache_key] = (time.time(), payload)
    return payload


def _crawl_jobs_for_refresh(source: str, recruitment_type: str, max_pages: Optional[int]) -> List[dict]:
    adapter = create_adapter(source, sleep_interval=0.05)
    jobs = adapter.fetch_all(
        max_pages=max_pages,
        page_size=adapter.max_page_size,
        recruitment_type=recruitment_type,
        include_detail=True,
    )
    return _dump_jobs([item for item in jobs if _is_domestic_job(item)])


def _refresh_targets(source: str, recruitment_type: str) -> List[Tuple[str, str]]:
    source = source.strip().lower() or "all"
    recruitment_type = recruitment_type.strip().lower() or "all"
    if source != "all" and source not in list_adapters():
        raise BadRequestException(f"不支持的招聘来源：{source}")
    if recruitment_type != "all" and recruitment_type not in RECRUITMENT_TYPES:
        raise BadRequestException(f"不支持的招聘类型：{recruitment_type}")

    sources = list_adapters() if source == "all" else [source]
    targets = []
    for item in sources:
        supported = SOURCE_META.get(item, {}).get("supported_recruitment_types") or list(RECRUITMENT_TYPES)
        types = supported if recruitment_type == "all" else [recruitment_type]
        for job_type in types:
            if job_type in supported:
                targets.append((item, job_type))
    return targets


@router.get("/sources", response_model=ApiResponse[list])
async def get_recruitment_sources():
    sources = [SOURCE_META[source] for source in list_adapters() if source in SOURCE_META]
    return ApiResponse(message="获取成功", data=sources)


@router.get("/tracks", response_model=ApiResponse[list])
async def get_recruitment_tracks():
    return ApiResponse(message="获取成功", data=list(TRACKS.values()))


@router.get("/recruitment-types", response_model=ApiResponse[list])
async def get_recruitment_types():
    return ApiResponse(message="获取成功", data=list(RECRUITMENT_TYPES.values()))


@router.get("/versions", response_model=ApiResponse[list])
async def get_recruitment_versions():
    return ApiResponse(message="获取成功", data=await recruitment_job_repo.latest_versions())


@router.get("/job-interviews", response_model=ApiResponse[list])
async def get_job_interviews(
    source: str = Query(...),
    recruitment_type: str = Query(...),
    source_job_id: str = Query(...),
    limit: int = Query(8, ge=1, le=20),
):
    job = await recruitment_job_repo.get_latest_job(source.strip().lower(), recruitment_type.strip().lower(), source_job_id)
    if not job:
        return ApiResponse(message="获取成功", data=[])
    records = await niuke_repo.search_related_interviews(
        job["company"],
        _interview_keywords(job),
        limit,
        _interview_post_keywords(job),
    )
    return ApiResponse(message="获取成功", data=[
        {key: item[key] for key in ("id", "content_id", "title", "edit_time", "read", "post", "company", "status")}
        for item in records
    ])


@router.get("/track-interviews", response_model=ApiResponse[list])
async def get_track_interviews(
    source: str = Query(...),
    recruitment_type: str = Query("campus"),
    track: str = Query(...),
    limit: int = Query(12, ge=1, le=20),
):
    jobs = await _job_samples(source, recruitment_type, track, 8)
    records = await _related_interviews_for_jobs(jobs, limit)
    return ApiResponse(message="获取成功", data=[
        {key: item[key] for key in ("id", "content_id", "title", "edit_time", "read", "post", "company", "status")}
        for item in records
    ])


@router.post("/resume/parse", response_model=ApiResponse[dict])
async def parse_resume_pdf(file: UploadFile = File(...), user_id: int = Depends(require_user_id)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise BadRequestException("请上传 PDF 简历")
    content = await file.read()
    if len(content) > 8 * 1024 * 1024:
        raise BadRequestException("PDF 文件不能超过 8MB")
    if not content.startswith(b"%PDF-"):
        raise BadRequestException("请上传有效的 PDF 简历")
    try:
        parsed = await run_in_threadpool(parse_resume_content, content)
    except ValueError as exc:
        raise BadRequestException(str(exc)) from exc
    return ApiResponse(message="解析成功", data=parsed)


@router.get("/jobs", response_model=ApiResponse[dict])
async def get_recruitment_jobs(
    source: str = Query("tencent", description="招聘来源"),
    keyword: str = Query("", max_length=80, description="岗位关键词"),
    track: str = Query("", max_length=30, description="岗位方向"),
    recruitment_type: str = Query("campus", max_length=20, description="招聘类型：campus/intern/social"),
    page: int = Query(1, ge=1, le=500),
    page_size: int = Query(12, ge=1, le=24),
    user_id: Optional[int] = Depends(optional_user_id),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
):
    require_public_window((page - 1) * page_size, page_size, user_id, is_valid_admin_token(x_admin_token))
    source = source.strip().lower()
    if source not in list_adapters():
        raise BadRequestException(f"不支持的招聘来源：{source}")
    track = track.strip().lower()
    if track and track not in TRACKS:
        raise BadRequestException(f"不支持的岗位方向：{track}")
    recruitment_type = recruitment_type.strip().lower() or "campus"
    if recruitment_type not in RECRUITMENT_TYPES:
        raise BadRequestException(f"不支持的招聘类型：{recruitment_type}")

    jobs = await recruitment_job_repo.list_latest_jobs(source, recruitment_type)
    result = _filter_saved_jobs(jobs, keyword.strip(), track, page, page_size)
    adapter_company = SOURCE_META.get(source, {}).get("company", source)
    data = {
        "source": source,
        "company": adapter_company,
        "track": track or None,
        "recruitment_type": recruitment_type,
        "keywords": list((TRACKS.get(track) or {}).get("keywords") or []) if track and not keyword else [],
        "items": result["items"],
        "page": page,
        "page_size": page_size,
        "total": result["total"],
        "has_more": result["has_more"],
        "cached": False,
        "from_database": True,
    }
    return ApiResponse(message="获取成功", data=data)


@router.post("/refresh", response_model=ApiResponse[dict])
async def refresh_recruitment_jobs(request: RecruitmentRefreshRequest):
    targets = _refresh_targets(request.source, request.recruitment_type)
    if not targets:
        raise BadRequestException("没有可刷新的招聘来源")

    started_at = datetime.now()
    version = started_at.strftime("jobs-%Y%m%d%H%M%S")
    results = []
    total_jobs = 0

    for source, recruitment_type in targets:
        await recruitment_job_repo.create_refresh_run(version, source, recruitment_type, started_at)
        try:
            jobs = await run_in_threadpool(_crawl_jobs_for_refresh, source, recruitment_type, request.max_pages)
            await recruitment_job_repo.upsert_many(jobs, version, started_at)
            await recruitment_job_repo.mark_latest_version(source, recruitment_type, version)
            await recruitment_job_repo.finish_refresh_run(version, source, recruitment_type, "success", len(jobs))
            total_jobs += len(jobs)
            results.append({"source": source, "recruitment_type": recruitment_type, "status": "success", "job_count": len(jobs)})
        except Exception as exc:
            await recruitment_job_repo.finish_refresh_run(version, source, recruitment_type, "failed", 0, str(exc)[:1000])
            results.append({"source": source, "recruitment_type": recruitment_type, "status": "failed", "job_count": 0, "error": str(exc)})

    _page_cache.clear()
    return ApiResponse(
        message="刷新完成",
        data={
            "refresh_version": version,
            "started_at": started_at.isoformat(),
            "total_jobs": total_jobs,
            "results": results,
        },
    )


@router.post("/ai-report", response_model=ApiResponse[dict])
async def generate_recruitment_ai_report(
    request: RecruitmentAIReportRequest,
    user_id: int = Depends(require_user_id),
):
    request.source = request.source.strip().lower()
    request.recruitment_type = request.recruitment_type.strip().lower() or "campus"
    request.track = request.track.strip().lower()
    job = None
    jobs: List[dict] = []
    single_company_types = {"job", "job_interviews", "resume_job", "full"}
    interview_types = {"job_interviews", "full"}
    resume_types = {"resume_job", "full", "resume_match"}
    if request.report_type in resume_types and not request.resume.strip():
        raise BadRequestException("该报告类型需要提供简历内容")

    if request.source_job_id:
        job = await recruitment_job_repo.get_latest_job(request.source, request.recruitment_type, request.source_job_id)
        if job:
            jobs = [job]
    elif request.report_type in single_company_types:
        jobs = await _job_samples(request.source, request.recruitment_type, request.track, 8)
    if request.report_type in single_company_types and not jobs:
        raise BadRequestException("该公司/招聘类型/岗位方向暂无岗位数据")

    interviews: List[dict] = []
    if request.report_type in interview_types:
        if request.selected_interview_ids:
            interviews = await niuke_repo.get_by_ids(request.selected_interview_ids, 8)
        else:
            interviews = await _related_interviews_for_jobs(jobs, 8)
    if request.report_type in interview_types and not interviews:
        raise BadRequestException("该公司/岗位方向暂无可用于分析的面经")

    job_context = job_brief(job) if job else jobs_brief(jobs)
    prompt = ""
    if request.report_type == "job":
        prompt = f"请基于以下岗位样本，输出结构化 Markdown 报告，包含：结论摘要、岗位画像、核心能力、优先准备项、项目建议、风险点。不要输出 HTML。\n{job_context}"
    elif request.report_type in {"company_compare", "resume_match"}:
        sources = request.compare_sources or list(SOURCE_META)
        chunks = []
        for source in sources[:8]:
            if source not in SOURCE_META:
                raise BadRequestException(f"不支持的招聘来源：{source}")
            types = SOURCE_META.get(source, {}).get("supported_recruitment_types") or ["campus"]
            if request.recruitment_type not in types:
                continue
            jobs = await recruitment_job_repo.list_latest_jobs(source, request.recruitment_type)
            filtered = _filter_saved_jobs(jobs, "", request.track, 1, 5)["items"]
            if filtered:
                chunks.append(f"## {SOURCE_META.get(source, {}).get('company', source)}\n" + "\n".join(job_brief(item) for item in filtered[:3]))
        if not chunks:
            raise BadRequestException("所选公司/招聘类型/岗位方向暂无可对比的岗位数据")
        if request.report_type == "company_compare":
            prompt = "请横向对比不同公司的招聘侧重点，输出结构化 Markdown，包含：结论摘要、共同要求、差异点、各公司偏好、候选人准备策略、风险提醒。不要输出 HTML。\n" + "\n\n".join(chunks)
        else:
            prompt = "请根据候选人简历和以下不同公司的岗位样本，反向判断更匹配的公司与岗位方向。输出结构化 Markdown，包含：推荐排序、匹配依据、各公司机会与风险、简历共性修改建议、投递优先级。不要输出 HTML。\n" + "\n\n".join(chunks) + f"\n\n候选人简历：\n{request.resume[:8000]}"
    elif request.report_type == "job_interviews":
        prompt = f"请结合岗位要求和用户选定的最近相关面经，输出结构化 Markdown 报告，包含：结论摘要、岗位要求对应考点、高频问题、准备顺序、缺口风险。不要输出 HTML。\n{job_context}\n\n相关面经：\n{interviews_brief(interviews)}"
    elif request.report_type == "resume_job":
        prompt = f"请根据目标公司的岗位要求和候选人简历，输出结构化 Markdown 简历匹配报告，包含：结论摘要、匹配度、已有优势、能力缺口、逐项简历修改建议、投递风险。不要输出 HTML。\n{job_context}\n\n候选人简历：\n{request.resume[:8000]}"
    elif request.report_type == "full":
        prompt = f"请根据岗位要求、用户选定的最近相关面经和候选人简历，输出结构化 Markdown 完整求职分析报告，包含：结论摘要、匹配度、优势、短板、面试风险、补强计划、简历修改建议。不要输出 HTML。\n{job_context}\n\n相关面经：\n{interviews_brief(interviews)}\n\n候选人简历：\n{request.resume[:8000] or '未提供'}"
    else:
        raise BadRequestException("不支持的报告类型")

    try:
        report = await run_in_threadpool(call_ai_report, prompt)
    except ValueError as exc:
        raise BadRequestException(str(exc)) from exc
    if request.report_type in {"company_compare", "resume_match"}:
        company = "、".join(SOURCE_META.get(item, {}).get("company", item) for item in request.compare_sources)
    else:
        company = SOURCE_META.get(request.source, {}).get("company", request.company or request.source)
    track_name = (TRACKS.get(request.track) or {}).get("name", request.track)
    saved = await ai_report_repo.save(user_id, {
        "title": f"{company or '多公司'} · {track_name}",
        "report_type": request.report_type,
        "company": company,
        "track": request.track,
        "track_name": track_name,
        "recruitment_type": request.recruitment_type,
        "content": report,
        "model": settings.OPENAI_TEXT_MODEL,
    })
    return ApiResponse(message="生成成功", data={**saved, "report": saved["content"]})


@router.get("/ai-reports", response_model=ApiResponse[list])
async def list_ai_reports(user_id: int = Depends(require_user_id)):
    return ApiResponse(message="获取成功", data=await ai_report_repo.list_by_user(user_id))


@router.get("/ai-reports/{report_code}", response_model=ApiResponse[dict])
async def get_ai_report(report_code: str, user_id: int = Depends(require_user_id)):
    report = await ai_report_repo.get_by_code(user_id, report_code)
    if not report:
        raise NotFoundException("报告不存在")
    return ApiResponse(message="获取成功", data=report)


@router.delete("/ai-reports/{report_code}", response_model=ApiResponse[dict])
async def delete_ai_report(report_code: str, user_id: int = Depends(require_user_id)):
    if not await ai_report_repo.delete_by_code(user_id, report_code):
        raise NotFoundException("报告不存在")
    return ApiResponse(message="删除成功", data={"report_code": report_code})
