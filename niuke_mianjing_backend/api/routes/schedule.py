from fastapi import APIRouter, Depends, BackgroundTasks
from typing import List

from niuke_mianjing_backend.api.deps import get_schedule_service, get_crawl_service
from niuke_mianjing_backend.api.middleware.error_handler import BadRequestException
from niuke_mianjing_backend.services.schedule_service import ScheduleService
from niuke_mianjing_backend.services.crawl_service import CrawlService
from niuke_mianjing_backend.schemas import (
    ApiResponse,
    ScheduleCreateRequest,
    CrawlNowRequest,
    JobItem,
    CrawlTaskData,
)


router = APIRouter(prefix="/api/schedule", tags=["定时任务"])


@router.post(
    "",
    response_model=ApiResponse[JobItem],
    summary="创建定时任务",
    description="创建一个定时爬取任务，支持 Cron 表达式或固定间隔",
)
async def create_schedule(
    request: ScheduleCreateRequest,
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    if not request.cron and not request.interval_hours and not request.interval_minutes:
        raise BadRequestException("必须指定cron表达式或时间间隔（interval_hours/interval_minutes）")

    try:
        if request.cron:
            result = await schedule_service.create_cron_job(request.posts, request.cron, request.max_pages)
        else:
            hours = request.interval_hours or 0
            minutes = request.interval_minutes or 0
            result = await schedule_service.create_interval_job(request.posts, hours, minutes, request.max_pages)

        jobs = await schedule_service.list_jobs()
        return ApiResponse(
            message="定时任务创建成功",
            data=jobs[0] if jobs else None,
        )
    except ValueError as e:
        raise BadRequestException(str(e))


@router.get(
    "/list",
    response_model=ApiResponse[List[JobItem]],
    summary="获取定时任务列表",
    description="获取所有活跃的定时爬取任务",
)
async def list_schedules(
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    jobs = await schedule_service.list_jobs()
    return ApiResponse(message="获取成功", data=jobs)


@router.delete(
    "/{job_id}",
    response_model=ApiResponse[dict],
    summary="删除定时任务",
    description="根据任务ID删除指定的定时爬取任务",
)
async def delete_schedule(
    job_id: str,
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    await schedule_service.delete_job(job_id)
    return ApiResponse(message="定时任务删除成功", data={"job_id": job_id})


@router.post("/{job_id}/pause", response_model=ApiResponse[dict])
async def pause_schedule(
    job_id: str,
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    await schedule_service.pause_job(job_id)
    return ApiResponse(message="定时任务已暂停", data={"job_id": job_id, "status": "paused"})


@router.post("/{job_id}/resume", response_model=ApiResponse[dict])
async def resume_schedule(
    job_id: str,
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    await schedule_service.resume_job(job_id)
    return ApiResponse(message="定时任务已恢复", data={"job_id": job_id, "status": "active"})


@router.post("/{job_id}/run", response_model=ApiResponse[dict])
async def run_schedule_now(
    job_id: str,
    background_tasks: BackgroundTasks,
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    background_tasks.add_task(schedule_service.run_job_now, job_id)
    return ApiResponse(message="定时任务已开始执行", data={"job_id": job_id, "status": "running"})


@router.get("/runs/recent", response_model=ApiResponse[list])
async def list_schedule_runs(
    limit: int = 50,
    schedule_service: ScheduleService = Depends(get_schedule_service),
):
    return ApiResponse(message="获取成功", data=await schedule_service.list_runs(min(max(limit, 1), 100)))


@router.post(
    "/crawl",
    response_model=ApiResponse[CrawlTaskData],
    summary="立即爬取",
    description="立即启动爬取任务，在后台异步执行",
)
async def crawl_now(
    request: CrawlNowRequest,
    background_tasks: BackgroundTasks,
    crawl_service: CrawlService = Depends(get_crawl_service),
):
    background_tasks.add_task(crawl_service.crawl_all, request.posts, request.max_pages)
    return ApiResponse(
        message="爬取任务已启动",
        data=CrawlTaskData(posts=request.posts, max_pages=request.max_pages, status="running"),
    )
