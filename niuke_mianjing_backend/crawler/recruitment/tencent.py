import time
from datetime import datetime
from typing import Dict, Optional

from .base import RecruitmentAdapter
from .models import JobPage, JobPosting


class TencentRecruitmentAdapter(RecruitmentAdapter):
    source = "tencent"
    company = "腾讯"
    API_BASE = "https://careers.tencent.com/tencentcareer/api/post"
    SEARCH_URL = f"{API_BASE}/Query"
    DETAIL_URL = f"{API_BASE}/ByPostId"
    max_page_size = 100

    def __init__(self, sleep_interval: Optional[float] = None, language: str = "zh-cn", area: str = "cn"):
        super().__init__(sleep_interval)
        self.language = language
        self.area = area
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)",
        }

    def fetch_page(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        keyword: str = "",
        filters: Optional[Dict] = None,
        include_detail: bool = True,
    ) -> JobPage:
        size = self._page_size(page_size)
        params = {
            "timestamp": int(time.time() * 1000),
            "pageIndex": max(page, 1),
            "pageSize": size,
            "language": self.language,
            "area": self.area,
        }
        if keyword.strip():
            params["keyword"] = keyword.strip()
        params.update(filters or {})

        data = self._request("GET", self.SEARCH_URL, headers=self.headers, params=params).json()
        self._validate_response(data)
        result = data.get("Data") or {}
        total = int(result.get("Count") or 0)
        items = []
        for raw in result.get("Posts") or []:
            detail = self.fetch_detail(str(raw.get("PostId"))) if include_detail else raw
            items.append(self._normalize_job(detail))
            if include_detail and self.sleep_interval > 0:
                time.sleep(min(self.sleep_interval, 1))

        return JobPage(
            items=items,
            page=page,
            page_size=size,
            total=total,
            has_more=page * size < total and bool(items),
        )

    def fetch_detail(self, post_id: str) -> Dict:
        params = {
            "timestamp": int(time.time() * 1000),
            "postId": post_id,
            "language": self.language,
            "area": self.area,
        }
        data = self._request("GET", self.DETAIL_URL, headers=self.headers, params=params).json()
        self._validate_response(data)
        return data.get("Data") or {}

    def _normalize_job(self, raw: Dict) -> JobPosting:
        post_id = str(raw.get("PostId") or "")
        source_url = raw.get("PostURL") or f"https://careers.tencent.com/jobdesc.html?postId={post_id}"
        return JobPosting(
            source=self.source,
            source_job_id=post_id,
            company=self.company,
            title=str(raw.get("RecruitPostName") or "").strip(),
            category=raw.get("CategoryName"),
            job_family=raw.get("CategoryName"),
            location=raw.get("LocationName"),
            country=raw.get("CountryName") or "中国",
            business_unit=raw.get("BGName") or raw.get("ComName"),
            product=raw.get("ProductName"),
            experience=raw.get("RequireWorkYearsName"),
            description=str(raw.get("Responsibility") or "").strip(),
            requirements=str(raw.get("Requirement") or "").strip(),
            highlights=str(raw.get("PostLightItem") or "").strip(),
            preferred_qualifications=str(raw.get("ImportantItem") or "").strip(),
            source_url=str(source_url).replace("http://", "https://"),
            updated_at=self._parse_date(raw.get("LastUpdateTime")),
            raw_data=raw,
        )

    @staticmethod
    def _validate_response(data: Dict):
        if data.get("Code") != 200:
            raise ValueError(f"腾讯招聘接口返回异常：{data}")

    @staticmethod
    def _parse_date(value) -> Optional[datetime]:
        if not value:
            return None
        for fmt in ("%Y年%m月%d日", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        return None
