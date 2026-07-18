from typing import Dict, Optional

from .base import RecruitmentAdapter
from .models import JobPage, JobPosting


class ByteDanceRecruitmentAdapter(RecruitmentAdapter):
    source = "bytedance"
    company = "字节跳动"
    API_BASE = "https://jobs.bytedance.com/api/v1"
    SEARCH_URL = f"{API_BASE}/search/job/posts"
    FILTERS_URL = f"{API_BASE}/config/job/filters"
    max_page_size = 50
    CAMPUS_SUBJECT_IDS = [
        "7624064258157889845",  # 2027届前沿技术领域人才校招
        "7621018151002507573",  # 2027届Seed大模型人才校招
        "7525009396952582407",  # 2026届校园招聘
    ]
    INTERN_SUBJECT_IDS = [
        "7624086888207862069",  # 前沿技术领域人才实习招聘
        "7621018569480046853",  # Seed大模型人才实习招聘
        "7194661644654577981",  # 日常实习
        "7194661126919358757",  # ByteIntern
    ]
    SEARCH_URLS = {
        "campus": "https://jobs.bytedance.com/campus/position",
        "intern": "https://jobs.bytedance.com/campus/position",
        "social": "https://jobs.bytedance.com/experienced/position",
    }

    def __init__(self, sleep_interval: Optional[float] = None, language: str = "zh-CN"):
        super().__init__(sleep_interval)
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://jobs.bytedance.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            "accept-language": language,
            "portal-platform": "pc",
        }

    def fetch_filters(self, recruitment_type: str = "campus") -> Dict:
        portal_type = self._portal_type(recruitment_type)
        headers = self._headers(recruitment_type)
        data = self._request("GET", f"{self.FILTERS_URL}/{portal_type}", headers=headers).json()
        self._validate_response(data)
        return data.get("data") or {}

    def fetch_page(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        keyword: str = "",
        filters: Optional[Dict] = None,
        recruitment_type: str = "campus",
        include_detail: bool = True,
    ) -> JobPage:
        del include_detail  # The list API already returns full descriptions and requirements.
        size = self._page_size(page_size)
        portal_type = self._portal_type(recruitment_type)
        payload = {
            "keyword": keyword.strip(),
            "limit": size,
            "offset": max(page - 1, 0) * size,
            "job_category_id_list": [],
            "tag_id_list": [],
            "location_code_list": [],
            "subject_id_list": self._subject_ids(recruitment_type),
            "recruitment_id_list": [],
            "portal_type": portal_type,
            "job_function_id_list": [],
            "storefront_id_list": [],
            "portal_entrance": 1,
        }
        payload.update(filters or {})

        data = self._request("POST", self.SEARCH_URL, headers=self._headers(recruitment_type), json=payload).json()
        self._validate_response(data)
        result = data.get("data") or {}
        total = int(result.get("count") or 0)
        items = [self._normalize_job(item, recruitment_type) for item in result.get("job_post_list") or []]
        return JobPage(
            items=items,
            page=page,
            page_size=size,
            total=total,
            has_more=page * size < total and bool(items),
        )

    def _normalize_job(self, raw: Dict, recruitment_type: str = "campus") -> JobPosting:
        category = raw.get("job_category") or {}
        category_parent = category.get("parent") or {}
        city = raw.get("city_info") or {}
        country = self._root_location(city)
        recruit_type = raw.get("recruit_type") or {}
        job_info = raw.get("job_post_info") or {}
        job_id = str(raw.get("id") or raw.get("code") or "")
        address = self._address(job_info)
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(raw.get("title") or "").strip(),
            category=category.get("i18n_name") or category.get("name"),
            job_family=category_parent.get("i18n_name") or category_parent.get("name"),
            official_taxonomy={
                "level1": {
                    "code": category_parent.get("id") or category_parent.get("code"),
                    "name": category_parent.get("i18n_name") or category_parent.get("name"),
                    "path": "job_category.parent",
                },
                "level2": {
                    "code": category.get("id") or category.get("code"),
                    "name": category.get("i18n_name") or category.get("name"),
                    "path": "job_category",
                },
                "level3": None,
                "tags": [],
            },
            location=city.get("i18n_name") or city.get("name"),
            country=address.get("country") or country,
            business_unit=self._name(raw.get("department_info")),
            recruitment_type=recruitment_type,
            employment_type=recruit_type.get("i18n_name") or recruit_type.get("name"),
            experience=job_info.get("experience"),
            description=str(raw.get("description") or "").strip(),
            requirements=str(raw.get("requirement") or "").strip(),
            highlights=self._join_values(job_info.get("highlight_list")),
            source_url=f"{self.SEARCH_URLS.get(recruitment_type, self.SEARCH_URLS['campus'])}/{job_id}/detail",
            raw_data=raw,
        )

    def _headers(self, recruitment_type: str) -> Dict:
        website_path = "society" if recruitment_type == "social" else "campus"
        portal_channel = "office" if recruitment_type == "social" else "campus"
        return {
            **self.headers,
            "Referer": self.SEARCH_URLS.get(recruitment_type, self.SEARCH_URLS["campus"]),
            "website-path": website_path,
            "portal-channel": portal_channel,
        }

    @staticmethod
    def _portal_type(recruitment_type: str) -> int:
        return 2 if recruitment_type == "social" else 3

    def _subject_ids(self, recruitment_type: str):
        if recruitment_type == "campus":
            return list(self.CAMPUS_SUBJECT_IDS)
        if recruitment_type == "intern":
            return list(self.INTERN_SUBJECT_IDS)
        return []

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
        if not city.get("parent"):
            return None
        current = city
        root = None
        while isinstance(current, dict) and current:
            root = current.get("i18n_name") or current.get("name") or root
            current = current.get("parent")
        return root

    @staticmethod
    def _address(job_info: Dict) -> Dict[str, Optional[str]]:
        for item in job_info.get("address_list") or []:
            if not isinstance(item, dict):
                continue
            country = item.get("country") or {}
            if isinstance(country, dict):
                return {"country": country.get("i18n_name") or country.get("name")}
        return {"country": None}
