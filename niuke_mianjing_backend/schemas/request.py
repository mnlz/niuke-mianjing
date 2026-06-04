from typing import List, Optional

from pydantic import BaseModel, Field


class ScheduleCreateRequest(BaseModel):
    posts: List[str] = Field(..., description="要爬取的方向列表", examples=[["后端", "前端"]])
    cron: Optional[str] = Field(None, description="Cron 表达式（分 时 日 月 周）", examples=["0 8 * * *"])
    interval_hours: Optional[int] = Field(None, description="间隔小时数", examples=[2])
    interval_minutes: Optional[int] = Field(None, description="间隔分钟数", examples=[30])
    max_pages: int = Field(15, description="最大爬取页数")


class CrawlNowRequest(BaseModel):
    posts: List[str] = Field(..., description="要爬取的方向列表", examples=[["后端"]])
    max_pages: int = Field(15, description="最大爬取页数")
    feishu_webhook: Optional[str] = Field(None, description="飞书机器人 webhook 地址")


class QuickCrawlRequest(BaseModel):
    posts: List[str] = Field(..., description="要爬取的方向列表", examples=[["后端", "前端"]])
    max_pages: int = Field(5, description="最大爬取页数", ge=1, le=100)


class ExportMdRequest(BaseModel):
    post: Optional[str] = Field(None, description="岗位方向过滤")
    company: Optional[str] = Field(None, description="公司过滤")
    limit: int = Field(100, description="最大导出条数", ge=1, le=1000)
    group_by: Optional[str] = Field(None, description="分组方式：company/post")


class WeChatPreviewRequest(BaseModel):
    markdown: str = Field(..., description="Markdown 内容")
    title: Optional[str] = Field(None, description="文章标题，优先级高于正文 H1")
    wechat_theme: Optional[str] = Field(None, description="公众号排版主题 ID，默认按内容类型自动选择")


class WeChatDraftRequest(BaseModel):
    markdown: str = Field(..., description="Markdown 内容")
    title: Optional[str] = Field(None, description="文章标题，优先级高于正文 H1")
    author: Optional[str] = Field(None, description="作者")
    digest: Optional[str] = Field(None, description="摘要")
    content_source_url: Optional[str] = Field(None, description="原文链接")
    cover_theme: str = Field("auto", description="封面主题：auto/programming/ai/tech")
    wechat_theme: Optional[str] = Field(None, description="公众号排版主题 ID")


class WeChatAIGenerateRequest(BaseModel):
    markdown: str = Field(..., description="原始 Markdown 内容")
    title: Optional[str] = Field(None, description="标题")
    author: Optional[str] = Field(None, description="作者")
    digest: Optional[str] = Field(None, description="摘要，不传则由 AI 生成")
    content_source_url: Optional[str] = Field(None, description="原文链接")
    source_record_id: Optional[int] = Field(None, description="来源面经记录 ID")
    style: str = Field("single_interpretation", description="内容类型：single_interpretation/knowledge_deep_dive/trend_analysis/manual_rewrite/quick_checklist/interviewer_chain")
    wechat_theme: Optional[str] = Field(None, description="公众号排版主题 ID，支持 Raphael Publish 主题")


class WeChatAISaveRequest(BaseModel):
    markdown: str = Field(..., description="原始 Markdown 内容")
    html: str = Field(..., description="已编辑确认的公众号 HTML")
    title: str = Field(..., description="公众号标题")
    author: Optional[str] = Field(None, description="作者")
    digest: Optional[str] = Field(None, description="摘要")
    content_source_url: Optional[str] = Field(None, description="原文链接")
    source_record_id: Optional[int] = Field(None, description="来源面经记录 ID")
    style: str = Field("single_interpretation", description="内容类型")
    cover_prompt: Optional[str] = Field(None, description="封面生成提示词")
    cover_base64: Optional[str] = Field(None, description="自定义封面 base64，不含 data URL 前缀")
    cover_mime: Optional[str] = Field(None, description="自定义封面 MIME 类型")


class WeChatQuestionAnalysisRequest(BaseModel):
    company: str = Field(..., description="公司名称")
    post: str = Field(..., description="岗位方向")
    days: int = Field(30, description="统计最近多少天", ge=1, le=180)
    limit: int = Field(200, description="最多分析多少条面经", ge=1, le=500)
    wechat_theme: Optional[str] = Field(None, description="公众号排版主题 ID")


class WeChatQuickChecklistRequest(BaseModel):
    company: str = Field(..., description="公司名称")
    post: str = Field(..., description="岗位方向")
    limit: int = Field(10, description="抽取面经条数", ge=1, le=50)
    order_by_time: bool = Field(False, description="是否按时间倒序抽取")
    days: Optional[int] = Field(None, description="按时间抽取时统计最近多少天", ge=1, le=180)
    wechat_theme: Optional[str] = Field(None, description="公众号排版主题 ID")
