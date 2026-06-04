import json
from typing import List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool

from niuke_mianjing_backend.api.deps import get_wechat_service
from niuke_mianjing_backend.api.middleware.error_handler import BadRequestException, NotFoundException
from niuke_mianjing_backend.schemas import (
    ApiResponse,
    WeChatAIGenerateRequest,
    WeChatAISaveRequest,
    WeChatArticleData,
    WeChatDraftData,
    WeChatDraftRequest,
    WeChatPreviewData,
    WeChatPreviewRequest,
    WeChatQuestionAnalysisRequest,
    WeChatQuickChecklistRequest,
)
from niuke_mianjing_backend.services.wechat_service import WeChatService


router = APIRouter(prefix="/api/wechat", tags=["微信公众号"])


def sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post(
    "/preview",
    response_model=ApiResponse[WeChatPreviewData],
    summary="预览微信公众号 HTML",
    description="将 Markdown 转换为适配微信公众号的内联样式 HTML。",
)
async def preview_wechat_html(
    request: WeChatPreviewRequest,
    wechat_service: WeChatService = Depends(get_wechat_service),
):
    if not request.markdown.strip():
        raise BadRequestException("Markdown 内容不能为空")
    rendered = await run_in_threadpool(wechat_service.render_html, request.markdown, request.title or "未命名文章")
    return ApiResponse(message="转换成功", data=rendered)


@router.post(
    "/ai-stream",
    summary="流式生成微信公众号 HTML",
    description="调用 Chat Completions 流式生成可编辑的公众号 HTML，不生成封面、不入库。",
)
async def stream_wechat_article(
    request: WeChatAIGenerateRequest,
    wechat_service: WeChatService = Depends(get_wechat_service),
):
    if not request.markdown.strip():
        raise BadRequestException("Markdown 内容不能为空")

    def event_generator():
        try:
            for event in wechat_service.stream_wechat_html(request.markdown, request.title, request.style):
                yield sse_event(event)
        except Exception as exc:
            yield sse_event({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/question-analysis-stream",
    summary="AI 直接分析面经并流式生成微信公众号 HTML",
    description="查询指定公司、岗位、时间范围内的面经，将统计结果和样本摘录交给 AI 直接生成公众号 HTML。",
)
async def stream_question_analysis_article(
    request: WeChatQuestionAnalysisRequest,
    wechat_service: WeChatService = Depends(get_wechat_service),
):
    if not request.company.strip() or not request.post.strip():
        raise BadRequestException("公司和岗位方向不能为空")
    try:
        analysis = await wechat_service.build_question_analysis(
            company=request.company.strip(),
            post=request.post.strip(),
            days=request.days,
            limit=request.limit,
        )
    except ValueError as exc:
        raise BadRequestException(str(exc))

    prompt = wechat_service.build_question_analysis_direct_prompt(analysis)

    def event_generator():
        try:
            yield sse_event(
                {
                    "type": "analysis",
                    "title": analysis["title"],
                    "digest": analysis["digest"],
                    "stats": analysis["stats"],
                    "records": analysis["records"],
                }
            )
            for event in wechat_service.stream_prompt_html(prompt, analysis["title"]):
                yield sse_event(event)
        except Exception as exc:
            yield sse_event({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/quick-checklist-stream",
    summary="AI 抽样分析面经并流式生成高频题速查清单",
    description="按公司、岗位、条数和可选时间范围抽取真实面经样本，交给 AI 生成适合收藏的高频题速查清单。",
)
async def stream_quick_checklist_article(
    request: WeChatQuickChecklistRequest,
    wechat_service: WeChatService = Depends(get_wechat_service),
):
    if not request.company.strip() or not request.post.strip():
        raise BadRequestException("公司和岗位方向不能为空")
    try:
        analysis = await wechat_service.build_quick_checklist_analysis(
            company=request.company.strip(),
            post=request.post.strip(),
            limit=request.limit,
            order_by_time=request.order_by_time,
            days=request.days,
        )
    except ValueError as exc:
        raise BadRequestException(str(exc))

    prompt = wechat_service.build_quick_checklist_prompt(analysis)

    def event_generator():
        try:
            yield sse_event(
                {
                    "type": "analysis",
                    "title": analysis["title"],
                    "digest": analysis["digest"],
                    "stats": analysis["stats"],
                    "records": analysis["records"],
                }
            )
            for event in wechat_service.stream_prompt_html(prompt, analysis["title"]):
                yield sse_event(event)
        except Exception as exc:
            yield sse_event({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/ai-save",
    response_model=ApiResponse[WeChatArticleData],
    summary="保存已编辑的 AI 公众号稿件",
    description="使用已编辑 HTML 生成封面图，并保存到 wechat_articles 表。",
)
async def save_wechat_article(
    request: WeChatAISaveRequest,
    wechat_service: WeChatService = Depends(get_wechat_service),
):
    if not request.markdown.strip() or not request.html.strip():
        raise BadRequestException("Markdown 和 HTML 内容不能为空")
    try:
        result = await wechat_service.save_ai_article(
            markdown_content=request.markdown,
            html=request.html,
            title=request.title,
            author=request.author,
            digest=request.digest,
            content_source_url=request.content_source_url,
            source_record_id=request.source_record_id,
            style=request.style,
            cover_prompt=request.cover_prompt,
            cover_base64=request.cover_base64,
            cover_mime=request.cover_mime,
        )
        return ApiResponse(message="公众号稿件已保存", data=result)
    except ValueError as exc:
        raise BadRequestException(str(exc))


@router.post(
    "/ai-generate",
    response_model=ApiResponse[WeChatArticleData],
    summary="AI 生成微信公众号稿件",
    description="调用 OpenAI 生成公众号 HTML 和封面图，并保存到 wechat_articles 表。",
)
async def ai_generate_wechat_article(
    request: WeChatAIGenerateRequest,
    wechat_service: WeChatService = Depends(get_wechat_service),
):
    if not request.markdown.strip():
        raise BadRequestException("Markdown 内容不能为空")
    try:
        result = await wechat_service.generate_ai_article(
            markdown_content=request.markdown,
            title=request.title,
            author=request.author,
            digest=request.digest,
            content_source_url=request.content_source_url,
            source_record_id=request.source_record_id,
            style=request.style,
        )
        return ApiResponse(message="AI 公众号稿件生成成功", data=result)
    except ValueError as exc:
        raise BadRequestException(str(exc))


@router.get(
    "/articles",
    response_model=ApiResponse[List[WeChatArticleData]],
    summary="获取 AI 公众号稿件列表",
)
async def list_wechat_articles(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    wechat_service: WeChatService = Depends(get_wechat_service),
):
    rows = await wechat_service.list_articles(limit, offset)
    return ApiResponse(message="获取成功", data=rows)


@router.get(
    "/articles/{article_id}",
    response_model=ApiResponse[WeChatArticleData],
    summary="获取 AI 公众号稿件详情",
)
async def get_wechat_article(
    article_id: int,
    wechat_service: WeChatService = Depends(get_wechat_service),
):
    article = await wechat_service.get_article(article_id)
    if not article:
        raise NotFoundException("公众号稿件不存在")
    return ApiResponse(message="获取成功", data=article)


@router.post(
    "/articles/{article_id}/draft",
    response_model=ApiResponse[WeChatDraftData],
    summary="将已保存稿件推送到公众号草稿箱",
    description="使用数据库中保存的 HTML 和 base64 封面创建公众号草稿；不会自动群发。",
)
async def publish_saved_article(
    article_id: int,
    wechat_service: WeChatService = Depends(get_wechat_service),
):
    try:
        result = await wechat_service.publish_saved_article(article_id)
        return ApiResponse(message="草稿创建成功，请登录公众号后台预览后再群发", data=result)
    except ValueError as exc:
        raise BadRequestException(str(exc))


@router.post(
    "/draft",
    response_model=ApiResponse[WeChatDraftData],
    summary="推送微信公众号草稿",
    description="使用普通 Markdown 转 HTML 流程创建草稿；不会自动群发。",
)
async def create_wechat_draft(
    request: WeChatDraftRequest,
    wechat_service: WeChatService = Depends(get_wechat_service),
):
    if not request.markdown.strip():
        raise BadRequestException("Markdown 内容不能为空")

    try:
        result = await run_in_threadpool(
            wechat_service.create_draft,
            markdown_content=request.markdown,
            title=request.title,
            author=request.author,
            digest=request.digest,
            content_source_url=request.content_source_url,
            cover_theme=request.cover_theme,
        )
        return ApiResponse(message="草稿创建成功，请登录公众号后台检查后再群发", data=result)
    except ValueError as exc:
        raise BadRequestException(str(exc))
