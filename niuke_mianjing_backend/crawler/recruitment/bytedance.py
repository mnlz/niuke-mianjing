from typing import Dict, Optional

from .base import RecruitmentAdapter
from .models import JobPage, JobPosting


class ByteDanceRecruitmentAdapter(RecruitmentAdapter):
    source = "bytedance"
    company = "字节跳动"
    API_BASE = "https://jobs.bytedance.com/api/v1/public/supplier"
    SEARCH_URL = f"{API_BASE}/search/job/posts"
    FILTERS_URL = f"{API_BASE}/config/job/filters"
    WEBSITE_PATH = "en"

    def __init__(self, sleep_interval: Optional[float] = None, language: str = "zh-CN"):
        super().__init__(sleep_interval)
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://joinbytedance.com",
            "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)",
            "accept-language": language,
            "website-path": self.WEBSITE_PATH,
        }

    def fetch_filters(self) -> Dict:
        data = self._request("POST", self.FILTERS_URL, headers=self.headers, json={}).json()
        self._validate_response(data)
        return data.get("data") or {}

    def fetch_page(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        keyword: str = "",
        filters: Optional[Dict] = None,
        include_detail: bool = True,
    ) -> JobPage:
        del include_detail  # The list API already returns full descriptions and requirements.
        size = self._page_size(page_size)
        payload = {
            "keyword": keyword.strip(),
            "limit": size,
            "offset": max(page - 1, 0) * size,
        }
        payload.update(filters or {})

        data = self._request("POST", self.SEARCH_URL, headers=self.headers, json=payload).json()
        self._validate_response(data)
        result = data.get("data") or {}
        total = int(result.get("count") or 0)
        items = [self._normalize_job(item) for item in result.get("job_post_list") or []]
        return JobPage(
            items=items,
            page=page,
            page_size=size,
            total=total,
            has_more=page * size < total and bool(items),
        )

    def _normalize_job(self, raw: Dict) -> JobPosting:
        category = raw.get("job_category") or {}
        category_parent = category.get("parent") or {}
        city = raw.get("city_info") or {}
        country = self._root_location(city)
        recruit_type = raw.get("recruit_type") or {}
        job_info = raw.get("job_post_info") or {}
        job_id = str(raw.get("id") or raw.get("code") or "")
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(raw.get("title") or "").strip(),
            category=category.get("i18n_name") or category.get("name"),
            job_family=category_parent.get("i18n_name") or category_parent.get("name"),
            location=city.get("i18n_name") or city.get("name"),
            country=country,
            business_unit=self._name(raw.get("department_info")),
            employment_type=recruit_type.get("i18n_name") or recruit_type.get("name"),
            experience=job_info.get("experience"),
            description=str(raw.get("description") or "").strip(),
            requirements=str(raw.get("requirement") or "").strip(),
            highlights=self._join_values(job_info.get("highlight_list")),
            source_url=f"https://jobs.bytedance.com/en/position/{job_id}/detail",
            raw_data=raw,
        )

    @staticmethod
    def _validate_response(data: Dict):
        if data.get("code") != 0:
            raise ValueError(f"字节招聘接口返回异常：{data}")

    @staticmethod
    def _name(value) -> Optional[str]:
        if not isinstance(value, dict):
            return None
        return value.get("i18n_name") or value.get("name") or value.get("en_name")

    @staticmethod
    def _join_values(value) -> str:
        if not value:
            return ""
        if isinstance(value, list):
            return "\n".join(str(item) for item in value if item)
        return str(value)

    @staticmethod
    def _root_location(city: Dict) -> Optional[str]:
        current = city
        root = None
        while isinstance(current, dict) and current:
            root = current.get("i18n_name") or current.get("name") or root
            current = current.get("parent")
        return root
