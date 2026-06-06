from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    source: str = Field(..., description="招聘官网适配器标识")
    source_job_id: str
    company: str
    title: str
    category: Optional[str] = None
    job_family: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    business_unit: Optional[str] = None
    product: Optional[str] = None
    employment_type: Optional[str] = None
    experience: Optional[str] = None
    description: str = ""
    requirements: str = ""
    highlights: str = ""
    preferred_qualifications: str = ""
    source_url: str
    updated_at: Optional[datetime] = None
    crawled_at: datetime = Field(default_factory=datetime.now)
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class JobPage(BaseModel):
    items: List[JobPosting]
    page: int
    page_size: int
    total: int
    has_more: bool
