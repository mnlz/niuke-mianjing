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
    CAMPUS_SEARCH_URL = "https://join.qq.com/api/v1/position/searchPosition"
    CAMPUS_DETAIL_URL = "https://join.qq.com/api/v1/jobDetails/getJobDetailsByPostId"
    CAMPUS_PROJECT_MAPPING_IDS = {
        "campus": [1],
        "intern": [2],
    }
    POSITION_FAMILY_NAMES = {
        "1": "设计",
        "2": "技术",
        "3": "产品",
        "4": "市场",
        "5": "职能",
    }
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
        recruitment_type: str = "campus",
        include_detail: bool = True,
    ) -> JobPage:
        size = self._page_size(page_size)
        if recruitment_type in self.CAMPUS_PROJECT_MAPPING_IDS:
            return self._fetch_campus_page(page, size, keyword, filters, recruitment_type, include_detail)

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
            detail = self.fetch_detail(str(raw.get("PostId"))) if include_detail else {}
            merged = {**raw, **{key: value for key, value in detail.items() if value not in (None, "")}}
            items.append(self._normalize_job(merged, recruitment_type))
            if include_detail and self.sleep_interval > 0:
                time.sleep(min(self.sleep_interval, 1))

        return JobPage(
            items=items,
            page=page,
            page_size=size,
            total=total,
            has_more=page * size < total and bool(items),
        )

    def _fetch_campus_page(
        self,
        page: int,
        size: int,
        keyword: str,
        filters: Optional[Dict],
        recruitment_type: str,
        include_detail: bool = True,
    ) -> JobPage:
        payload = {
            "projectIdList": [],
            "projectMappingIdList": self.CAMPUS_PROJECT_MAPPING_IDS[recruitment_type],
            "keyword": keyword.strip(),
            "bgList": [],
            "workCountryType": 0,
            "workCityList": [],
            "recruitCityList": [],
            "positionFidList": [],
            "pageIndex": max(page, 1),
            "pageSize": size,
        }
        payload.update(filters or {})
        data = self._request(
            "POST",
            self.CAMPUS_SEARCH_URL,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": "https://join.qq.com",
                "Referer": f"https://join.qq.com/post.html?query={'p_1' if recruitment_type == 'campus' else 'p_2'}",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            },
            params={"timestamp": int(time.time() * 1000)},
            json=payload,
        ).json()
        self._validate_campus_response(data)
        result = data.get("data") or {}
        total = int(result.get("count") or 0)
        items = []
        for item in result.get("positionList") or []:
            raw = {**item}
            if include_detail:
                try:
                    raw["detail"] = self.fetch_campus_detail(str(item.get("postId") or ""))
                except ValueError:
                    raw["detail"] = {}
            items.append(self._normalize_campus_job(raw, recruitment_type))
            if include_detail and self.sleep_interval > 0:
                time.sleep(min(self.sleep_interval, 1))
        return JobPage(
            items=items,
            page=page,
            page_size=size,
            total=total,
            has_more=page * size < total and bool(items),
        )

    def fetch_campus_detail(self, post_id: str) -> Dict:
        if not post_id:
            return {}
        data = self._request(
            "GET",
            self.CAMPUS_DETAIL_URL,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": f"https://join.qq.com/post_detail.html?postid={post_id}",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            },
            params={"postId": post_id, "timestamp": int(time.time() * 1000)},
        ).json()
        self._validate_campus_response(data)
        return data.get("data") or {}

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

    def _normalize_job(self, raw: Dict, recruitment_type: str = "campus") -> JobPosting:
        post_id = str(raw.get("PostId") or "")
        source_url = raw.get("PostURL") or f"https://careers.tencent.com/jobdesc.html?postId={post_id}"
        return JobPosting(
            source=self.source,
            source_job_id=post_id,
            company=self.company,
            title=str(raw.get("RecruitPostName") or "").strip(),
            category=raw.get("CategoryName"),
            job_family=raw.get("CategoryName"),
            official_taxonomy={
                "level1": {"code": raw.get("CategoryId"), "name": raw.get("CategoryName"), "path": "CategoryName"},
                "level2": None,
                "level3": None,
                "tags": [],
            },
            location=raw.get("LocationName"),
            country=raw.get("CountryName") or "中国",
            business_unit=raw.get("BGName") or raw.get("ComName"),
            product=raw.get("ProductName"),
            recruitment_type=recruitment_type,
            experience=raw.get("RequireWorkYearsName"),
            description=str(raw.get("Responsibility") or "").strip(),
            requirements=str(raw.get("Requirement") or "").strip(),
            highlights=str(raw.get("PostLightItem") or "").strip(),
            preferred_qualifications=str(raw.get("ImportantItem") or "").strip(),
            source_url=str(source_url).replace("http://", "https://"),
            updated_at=self._parse_date(raw.get("LastUpdateTime")),
            raw_data=raw,
        )

    def _normalize_campus_job(self, raw: Dict, recruitment_type: str) -> JobPosting:
        post_id = str(raw.get("postId") or raw.get("id") or "")
        detail = raw.get("detail") or {}
        family_code = str(raw.get("positionFamily") or "")
        category = detail.get("tidName") or self.POSITION_FAMILY_NAMES.get(family_code, family_code or None)
        project_name = raw.get("projectName") or raw.get("recruitLabelName") or _type_label(recruitment_type)
        return JobPosting(
            source=self.source,
            source_job_id=post_id,
            company=self.company,
            title=str(detail.get("title") or raw.get("positionTitle") or "").strip(),
            category=category,
            job_family=category,
            official_taxonomy={
                "level1": {"code": detail.get("tid") or family_code, "name": category, "path": "detail.tidName"},
                "level2": {
                    "code": detail.get("subDirectionId"),
                    "name": detail.get("techTagName"),
                    "path": "detail.subDirectionId",
                },
                "level3": None,
                "tags": ([{"code": None, "name": str(detail.get("techTagName"))}] if detail.get("techTagName") else []),
            },
            location="、".join(detail.get("workCityList") or []) or str(raw.get("workCities") or "").strip() or None,
            country="中国",
            business_unit=str(raw.get("bgs") or "").strip() or None,
            product=project_name,
            recruitment_type=recruitment_type,
            employment_type=project_name,
            description=str(detail.get("desc") or "").strip(),
            requirements=str(detail.get("request") or "").strip(),
            source_url=f"https://join.qq.com/post_detail.html?postid={post_id}",
            raw_data=raw,
        )

    @staticmethod
    def _validate_response(data: Dict):
        if data.get("Code") != 200:
            raise ValueError(f"腾讯招聘接口返回异常：{data}")

    @staticmethod
    def _validate_campus_response(data: Dict):
        if data.get("status") != 0:
            raise ValueError(f"腾讯校招接口返回异常：{data}")

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


def _type_label(recruitment_type: str) -> str:
    return {"campus": "校招", "intern": "实习", "social": "社招"}.get(recruitment_type, "校招")
