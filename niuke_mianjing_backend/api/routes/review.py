from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel, Field

from niuke_mianjing_backend.api.deps import get_review_service
from niuke_mianjing_backend.api.middleware.error_handler import BadRequestException
from niuke_mianjing_backend.schemas import ApiResponse
from niuke_mianjing_backend.services.review_service import ReviewService


router = APIRouter(prefix="/api/review", tags=["面经复习"])


class ReviewProgressRequest(BaseModel):
    favorite: Optional[bool] = None
    mastery: Optional[str] = Field(None, description="new/learning/fuzzy/mastered")
    note: Optional[str] = None


@router.get("/progress", response_model=ApiResponse[list])
async def get_progress(
    record_ids: str = Query("", description="逗号分隔的面经记录 ID"),
    visitor_id: str = Header("anonymous", alias="X-Visitor-ID"),
    review_service: ReviewService = Depends(get_review_service),
):
    ids = [int(item) for item in record_ids.split(",") if item.strip().isdigit()]
    return ApiResponse(message="获取成功", data=await review_service.get_progress(visitor_id, ids))


@router.put("/progress/{record_id}", response_model=ApiResponse[dict])
async def update_progress(
    record_id: int,
    request: ReviewProgressRequest,
    visitor_id: str = Header("anonymous", alias="X-Visitor-ID"),
    review_service: ReviewService = Depends(get_review_service),
):
    try:
        data = await review_service.update_progress(visitor_id, record_id, request.favorite, request.mastery, request.note)
    except ValueError as exc:
        raise BadRequestException(str(exc))
    return ApiResponse(message="保存成功", data=data)


@router.get("/overview", response_model=ApiResponse[dict])
async def get_overview(
    company: str = Query(..., description="公司"),
    post: str = Query(..., description="岗位方向"),
    days: int = Query(30, ge=1, le=180),
    limit: int = Query(80, ge=1, le=300),
    review_service: ReviewService = Depends(get_review_service),
):
    data = await review_service.build_overview(company, post, days, limit)
    return ApiResponse(message="获取成功", data=data)


@router.post("/records/{record_id}/ai-review", response_model=ApiResponse[dict])
async def generate_ai_review(
    record_id: int,
    refresh: bool = Query(False, description="是否强制重新生成"),
    review_service: ReviewService = Depends(get_review_service),
):
    try:
        data = await review_service.get_ai_review(record_id, refresh)
    except ValueError as exc:
        raise BadRequestException(str(exc))
    return ApiResponse(message="生成成功", data=data)
