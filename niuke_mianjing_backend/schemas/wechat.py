from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WeChatPreviewData(BaseModel):
    title: str = Field(..., description="文章标题")
    html: str = Field(..., description="微信可用 HTML")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Frontmatter 元信息")


class WeChatDraftData(BaseModel):
    title: str = Field(..., description="文章标题")
    media_id: str = Field(..., description="微信草稿 media_id")
    cover_media_id: str = Field(..., description="封面素材 media_id")
    wechat_response: Optional[Dict[str, Any]] = Field(default=None, description="微信原始响应")


class WeChatNewspicDraftData(BaseModel):
    title: str = Field(..., description="WeChat newspic draft title")
    media_id: str = Field(..., description="WeChat draft media_id")
    image_media_ids: List[str] = Field(default_factory=list, description="Uploaded image media_id list")
    wechat_response: Optional[Dict[str, Any]] = Field(default=None, description="Raw WeChat response")


class WeChatArticleData(BaseModel):
    id: int
    source_record_id: Optional[int] = None
    title: str
    author: Optional[str] = None
    digest: Optional[str] = None
    content_source_url: Optional[str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    cover_base64: Optional[str] = None
    cover_mime: Optional[str] = "image/png"
    prompt: Optional[str] = None
    model_info: Dict[str, Any] = Field(default_factory=dict)
    wechat_media_id: Optional[str] = None
    cover_media_id: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WeChatQuestionAnalysisData(BaseModel):
    title: str = Field(..., description="建议公众号标题")
    digest: str = Field(..., description="建议摘要")
    stats: Dict[str, Any] = Field(default_factory=dict, description="统计结果")
    records: List[Dict[str, Any]] = Field(default_factory=list, description="参与分析的面经摘要")
