import math
import time
from typing import Dict, List, Tuple

from fastapi import APIRouter, Query
from starlette.concurrency import run_in_threadpool

from niuke_mianjing_backend.api.middleware.error_handler import BadRequestException
from niuke_mianjing_backend.crawler.recruitment import create_adapter, list_adapters
from niuke_mianjing_backend.schemas import ApiResponse


router = APIRouter(prefix="/api/recruitment", tags=["公开招聘岗位"])

SOURCE_META = {
    "bytedance": {
        "source": "bytedance",
        "company": "字节跳动",
        "description": "字节跳动招聘官网公开岗位",
    },
    "tencent": {
        "source": "tencent",
        "company": "腾讯",
        "description": "腾讯招聘官网公开岗位",
    },
}

TRACKS = {
    "backend": {
        "id": "backend",
        "name": "后端开发",
        "description": "服务端、分布式系统与基础架构",
        "keywords": ["后端", "服务端", "Java", "Golang"],
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
_page_cache: Dict[Tuple[str, str, str, int, int], Tuple[float, dict]] = {}


def _fetch_jobs(source: str, keyword: str, track: str, page: int, page_size: int) -> dict:
    cache_key = (source, keyword, track, page, page_size)
    cached = _page_cache.get(cache_key)
    if cached and time.time() - cached[0] < CACHE_TTL_SECONDS:
        return {**cached[1], "cached": True}

    adapter = create_adapter(source, sleep_interval=0.05)
    keywords: List[str] = [keyword] if keyword else list((TRACKS.get(track) or {}).get("keywords") or [""])
    request_size = page_size if len(keywords) == 1 else max(2, math.ceil(page_size / len(keywords)))
    results = [
        adapter.fetch_page(page=page, page_size=request_size, keyword=item, include_detail=True)
        for item in keywords
    ]
    unique_items = {}
    for result in results:
        for item in result.items:
            unique_items.setdefault(item.source_job_id, item)
    items = list(unique_items.values())[:page_size]
    total = sum(result.total for result in results)
    payload = {
        "source": source,
        "company": adapter.company,
        "track": track or None,
        "keywords": keywords if track and not keyword else [],
        "items": [item.model_dump(mode="json", exclude={"raw_data"}) for item in items],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": any(result.has_more for result in results),
        "cached": False,
    }
    _page_cache[cache_key] = (time.time(), payload)
    return payload


@router.get("/sources", response_model=ApiResponse[list])
async def get_recruitment_sources():
    sources = [SOURCE_META[source] for source in list_adapters() if source in SOURCE_META]
    return ApiResponse(message="获取成功", data=sources)


@router.get("/tracks", response_model=ApiResponse[list])
async def get_recruitment_tracks():
    return ApiResponse(message="获取成功", data=list(TRACKS.values()))


@router.get("/jobs", response_model=ApiResponse[dict])
async def get_recruitment_jobs(
    source: str = Query("tencent", description="招聘来源"),
    keyword: str = Query("", max_length=80, description="岗位关键词"),
    track: str = Query("", max_length=30, description="岗位方向"),
    page: int = Query(1, ge=1, le=500),
    page_size: int = Query(12, ge=1, le=24),
):
    source = source.strip().lower()
    if source not in list_adapters():
        raise BadRequestException(f"不支持的招聘来源：{source}")
    track = track.strip().lower()
    if track and track not in TRACKS:
        raise BadRequestException(f"不支持的岗位方向：{track}")

    data = await run_in_threadpool(_fetch_jobs, source, keyword.strip(), track, page, page_size)
    return ApiResponse(message="获取成功", data=data)
