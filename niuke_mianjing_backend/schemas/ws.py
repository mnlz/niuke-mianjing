from pydantic import BaseModel, Field
from typing import Optional, List, Any
from enum import Enum


class WSMessageType(str, Enum):
    CRAWL_START = "crawl_start"
    CRAWL_PAGE_DONE = "crawl_page_done"
    CRAWL_POST_DONE = "crawl_post_done"
    CRAWL_ALL_DONE = "crawl_all_done"
    CRAWL_ERROR = "crawl_error"
    JOB_STATUS_CHANGE = "job_status_change"


class WSMessage(BaseModel):
    type: WSMessageType = Field(..., description="消息类型")
    data: Optional[Any] = Field(None, description="消息数据")
    message: Optional[str] = Field(None, description="消息文本")


class CrawlStartData(BaseModel):
    post: str = Field(..., description="职位方向")
    max_pages: int = Field(..., description="最大页数")


class CrawlPageDoneData(BaseModel):
    post: str = Field(..., description="职位方向")
    page: int = Field(..., description="当前页码")
    total_pages: int = Field(..., description="总页数")
    new_count: int = Field(0, description="本页新增数")
    updated_count: int = Field(0, description="本页更新数")


class CrawlPostDoneData(BaseModel):
    post: str = Field(..., description="职位方向")
    new_count: int = Field(0, description="新增总数")
    updated_count: int = Field(0, description="更新总数")
    status: str = Field(..., description="状态：success/failed")
    error: Optional[str] = Field(None, description="错误信息")


class CrawlAllDoneData(BaseModel):
    summary: List[dict] = Field(default_factory=list, description="各方向爬取结果")
