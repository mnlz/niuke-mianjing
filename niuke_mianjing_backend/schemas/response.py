from pydantic import BaseModel, Field
from typing import Optional, Generic, TypeVar, List, Dict, Any
from datetime import datetime


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(0, description="状态码，0=成功")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="业务数据")
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()), description="时间戳")


class JobItem(BaseModel):
    job_id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    posts: List[str] = Field(default_factory=list, description="爬取方向列表")
    schedule_type: str = Field(..., description="调度类型：cron/interval")
    schedule: str = Field(..., description="调度规则")
    max_pages: int = Field(15, description="最大爬取页数")
    next_run_time: Optional[str] = Field(None, description="下次执行时间")


class CrawlLogItem(BaseModel):
    id: int
    post: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_pages: Optional[int] = None
    new_records: int = 0
    updated_records: int = 0
    status: str
    error_message: Optional[str] = None


class StatsData(BaseModel):
    total_records: int = Field(0, description="总记录数")
    active_records: int = Field(0, description="有效记录数")
    post_stats: List[Dict[str, Any]] = Field(default_factory=list, description="各方向统计")


class NiukeDataItem(BaseModel):
    id: int
    content_id: Optional[str] = None
    title: str
    content: str
    edit_time: Optional[str] = None
    read: Optional[int] = None
    post: str
    company: str
    status: int


class NiukeDataResponse(BaseModel):
    data: List[NiukeDataItem] = Field(default_factory=list)
    total: int = Field(0)


class CrawlResultItem(BaseModel):
    post: str = Field(..., description="职位方向")
    new: int = Field(0, description="新增记录数")
    updated: int = Field(0, description="更新记录数")


class CrawlTaskData(BaseModel):
    posts: List[str] = Field(default_factory=list, description="爬取方向列表")
    max_pages: int = Field(15, description="最大爬取页数")
    status: str = Field("running", description="任务状态")
