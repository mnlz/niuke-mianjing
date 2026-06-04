from pydantic import BaseModel, Field
from typing import List, Optional, Union


class ScheduleRequest(BaseModel):
    posts: List[str] = Field(..., description="要爬取的方向列表")
    cron: Optional[str] = Field(None, description="Cron表达式（分 时 日 月 周）")
    interval_hours: Optional[int] = Field(None, description="间隔小时数")
    interval_minutes: Optional[int] = Field(None, description="间隔分钟数")
    max_pages: int = Field(15, description="最大爬取页数")
    feishu_webhook: Optional[str] = Field(None, description="飞书机器人webhook地址")


class CrawlRequest(BaseModel):
    posts: List[str] = Field(..., description="要爬取的方向列表")
    max_pages: int = Field(15, description="最大爬取页数")
    feishu_webhook: Optional[str] = Field(None, description="飞书机器人webhook地址")


class CrawlLog(BaseModel):
    id: int
    post: str
    start_time: Optional[str]
    end_time: Optional[str]
    total_pages: Optional[int]
    new_records: int
    updated_records: int
    status: str
    error_message: Optional[str]


class Stats(BaseModel):
    total_records: int
    post_stats: List[dict]


class JobInfo(BaseModel):
    job_id: str
    name: str
    next_run_time: Optional[str]


class ScheduleResponse(BaseModel):
    code: int = 0
    message: str
    data: Optional[Union[dict, List[dict]]] = None


class CrawlResponse(BaseModel):
    code: int = 0
    message: str
    data: Optional[dict] = None
