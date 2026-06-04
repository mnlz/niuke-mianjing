from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse

from niuke_mianjing_backend.api.deps import get_crawl_service, get_log_service
from niuke_mianjing_backend.services.crawl_service import CrawlService
from niuke_mianjing_backend.services.log_service import LogService
from niuke_mianjing_backend.schemas import (
    ApiResponse,
    CrawlTaskData,
    ExportMdRequest,
    QuickCrawlRequest,
)
from niuke_mianjing_backend.utils.job_map import get_all_posts, get_job_tree


router = APIRouter(prefix="/api/crawl", tags=["快速爬取"])


@router.get(
    "/posts",
    response_model=ApiResponse,
    summary="获取可选方向列表",
    description="返回所有可爬取的岗位方向及其 jobId。",
)
async def get_posts():
    posts = get_all_posts()
    tree = get_job_tree()
    return ApiResponse(message="获取成功", data={"posts": posts, "tree": tree})


@router.post(
    "/quick",
    response_model=ApiResponse[CrawlTaskData],
    summary="快速爬取",
    description="按岗位方向和页数启动后台爬取任务。",
)
async def quick_crawl(
    request: QuickCrawlRequest,
    background_tasks: BackgroundTasks,
    crawl_service: CrawlService = Depends(get_crawl_service),
):
    background_tasks.add_task(crawl_service.crawl_all, request.posts, request.max_pages)
    return ApiResponse(
        message="快速爬取任务已启动",
        data=CrawlTaskData(posts=request.posts, max_pages=request.max_pages, status="running"),
    )


@router.post(
    "/export-md",
    summary="导出面经为 Markdown",
    description="按条件导出面经数据为 Markdown 文件，支持按公司或岗位方向分组。",
    response_class=PlainTextResponse,
)
async def export_md(
    request: ExportMdRequest,
    log_service: LogService = Depends(get_log_service),
):
    result = await log_service.get_niuke_data(
        post=request.post,
        company=request.company,
        limit=request.limit,
        offset=0,
    )

    items = result.get("data", [])
    if not items:
        return PlainTextResponse(
            "# 暂无数据\n\n没有找到符合条件的面经数据。",
            media_type="text/markdown; charset=utf-8",
        )

    group_by = request.group_by if request.group_by in {"company", "post"} else None
    lines = ["# 牛客面经数据\n"]
    if request.post:
        lines.append(f"**方向**: {request.post}\n")
    if request.company:
        lines.append(f"**公司**: {request.company}\n")
    lines.append(f"**共 {len(items)} 条**\n")
    lines.append("---\n")

    grouped_items = []
    if group_by:
        groups = {}
        for item in items:
            fallback = "未知公司" if group_by == "company" else "未知方向"
            key = item.get(group_by) or fallback
            groups.setdefault(key, []).append(item)
        for key in sorted(groups.keys()):
            grouped_items.append((key, groups[key]))
    else:
        grouped_items.append((None, items))

    group_titles = {"company": "公司", "post": "岗位方向"}

    for group_name, group_items in grouped_items:
        if group_name:
            lines.append(f"# 按{group_titles[group_by]}：{group_name}\n")

        for item in group_items:
            title = item.get("title", "无标题")
            company = item.get("company", "未知公司")
            post = item.get("post", "")
            content = item.get("content", "暂无内容")
            edit_time = item.get("edit_time", "")
            content_id = item.get("content_id", "")

            lines.append(f"## {title}\n")
            lines.append("| 方向 | 公司 | 时间 |")
            lines.append("|------|------|------|")
            lines.append(f"| {post} | {company} | {edit_time} |\n")

            if content_id:
                lines.append(f"[查看原文](https://www.nowcoder.com/discuss/{content_id})\n")

            lines.append(f"{content}\n")
            lines.append("---\n")

    return PlainTextResponse("\n".join(lines), media_type="text/markdown; charset=utf-8")
