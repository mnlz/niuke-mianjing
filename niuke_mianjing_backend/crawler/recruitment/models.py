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
    official_taxonomy: Dict[str, Any] = Field(default_factory=dict)
    role_group: Optional[str] = None
    role_family: Optional[str] = None
    specialties: List[str] = Field(default_factory=list)
    business_domains: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)
    classification_meta: Dict[str, Any] = Field(default_factory=dict)
    inferred_track: Optional[str] = None
    inferred_track_name: Optional[str] = None
    display_category: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    business_unit: Optional[str] = None
    product: Optional[str] = None
    recruitment_type: str = "campus"
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
