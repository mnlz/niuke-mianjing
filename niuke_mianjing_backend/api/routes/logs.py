from typing import List, Optional

from fastapi import APIRouter, Depends, Header, Query

from niuke_mianjing_backend.api.deps import get_log_service
from niuke_mianjing_backend.api.middleware.error_handler import BadRequestException, NotFoundException
from niuke_mianjing_backend.api.routes.user_auth import optional_user_id, require_public_window
from niuke_mianjing_backend.api.security import is_valid_admin_token
from niuke_mianjing_backend.schemas import (
    ApiResponse,
    CrawlLogItem,
    NiukeDataItem,
    NiukeDataResponse,
    StatsData,
)
from niuke_mianjing_backend.services.log_service import LogService
from niuke_mianjing_backend.utils.role_taxonomy import ROLE_FAMILY_LABELS, ROLE_GROUP_LABELS


router = APIRouter(prefix="/api/logs", tags=["日志查询"])


@router.get(
    "/crawl",
    response_model=ApiResponse[List[CrawlLogItem]],
    summary="获取爬取日志",
    description="查询爬取日志，支持按岗位方向、状态、日期范围过滤。",
)
async def get_crawl_logs(
    post: Optional[str] = Query(None, description="岗位方向"),
    status: Optional[str] = Query(None, description="状态：success/failed/running"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    limit: int = Query(10, description="返回条数", ge=1, le=100),
    log_service: LogService = Depends(get_log_service),
):
    logs = await log_service.get_crawl_logs(post, status, start_date, end_date, limit)
    return ApiResponse(message="获取成功", data=logs)


@router.get(
    "/stats",
    response_model=ApiResponse[StatsData],
    summary="获取统计信息",
    description="获取面经总数、有效记录数、各方向统计等汇总信息。",
)
async def get_stats(
    log_service: LogService = Depends(get_log_service),
):
    stats = await log_service.get_stats()
    return ApiResponse(message="获取成功", data=stats)


@router.get(
    "/filters",
    response_model=ApiResponse[dict],
    summary="获取面经筛选项",
    description="返回数据库中已有的岗位方向和公司列表。",
)
async def get_filters(
    company: Optional[str] = Query(None, description="公司名称"),
    log_service: LogService = Depends(get_log_service),
):
    filters = await log_service.get_filters(company)
    return ApiResponse(message="获取成功", data=filters)


@router.get(
    "/data",
    response_model=ApiResponse[NiukeDataResponse],
    summary="查询面经数据",
    description="分页查询面经数据，支持按岗位方向和公司过滤。",
)
async def get_niuke_data(
    post: Optional[str] = Query(None, description="岗位方向"),
    company: Optional[str] = Query(None, description="公司名称"),
    role_group: Optional[str] = Query(None, max_length=40, description="统一职位大类"),
    role_family: Optional[str] = Query(None, max_length=40, description="统一岗位族"),
    limit: int = Query(20, description="每页条数", ge=1, le=100),
    offset: int = Query(0, description="偏移量", ge=0),
    user_id: Optional[int] = Depends(optional_user_id),
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    log_service: LogService = Depends(get_log_service),
):
    require_public_window(offset, limit, user_id, is_valid_admin_token(x_admin_token))
    if role_group and role_group not in ROLE_GROUP_LABELS:
        raise BadRequestException(f"不支持的职位大类：{role_group}")
    if role_family and role_family not in {*ROLE_FAMILY_LABELS, "unknown"}:
        raise BadRequestException(f"不支持的岗位族：{role_family}")
    result = await log_service.get_niuke_data(post, company, role_group, role_family, limit, offset)
    return ApiResponse(message="获取成功", data=result)


@router.get(
    "/data/{record_id}",
    response_model=ApiResponse[NiukeDataItem],
    summary="获取面经详情",
    description="根据记录 ID 获取单条面经详情，用于 Markdown 预览和卡片生成。",
)
async def get_niuke_record(
    record_id: int,
    log_service: LogService = Depends(get_log_service),
):
    record = await log_service.get_niuke_record(record_id)
    if not record:
        raise NotFoundException("面经记录不存在")
    return ApiResponse(message="获取成功", data=record)
