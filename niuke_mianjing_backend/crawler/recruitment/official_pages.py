import base64
import hashlib
import hmac
import json
import re
import time
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from .base import RecruitmentAdapter
from .models import JobPage, JobPosting


RECRUITMENT_TYPE_LABELS = {
    "campus": "校招",
    "intern": "实习",
    "social": "社招",
}

CITY_NAMES = {
    "Beijing": "北京",
    "Shanghai": "上海",
    "Shenzhen": "深圳",
    "Hangzhou": "杭州",
    "Guangzhou": "广州",
    "Chengdu": "成都",
    "Wuhan": "武汉",
    "Nanjing": "南京",
    "Xian": "西安",
    "Xi'an": "西安",
    "Suzhou": "苏州",
    "Gongshu": "杭州",
    "Haidian": "北京",
    "Huangpu": "上海",
    "Nanshan": "深圳",
    "Pudong": "上海",
    "Xiang'an": "厦门",
    "Chahar right front flag": "察哈尔右翼前旗",
}


def _label(recruitment_type: str) -> str:
    return RECRUITMENT_TYPE_LABELS.get(recruitment_type, "校招")


def _first_present(raw: Dict, *keys):
    for key in keys:
        value = raw.get(key)
        if value not in (None, ""):
            return value
    return None


def _parse_datetime(value) -> Optional[datetime]:
    if not value:
        return None
    try:
        number = int(value)
        if number > 10_000_000_000:
            number = number / 1000
        return datetime.fromtimestamp(number)
    except (TypeError, ValueError, OSError):
        pass
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=None)
        except ValueError:
            continue
    return None


def _normalize_city(value) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, list):
        parts = [_normalize_city(item) for item in value]
        return "、".join(part for part in parts if part) or None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("China\\", "中国/").replace("\\", "/")
    for key, name in CITY_NAMES.items():
        text = text.replace(key, name)
    return text


def _safe_tags(value):
    tags = []
    values = value if isinstance(value, list) else ([value] if value not in (None, "") else [])
    for item in values:
        if isinstance(item, dict):
            name = _first_present(item, "name", "tagName", "label", "value")
            code = _first_present(item, "code", "tagCode", "id")
        else:
            name, code = item, None
        if name not in (None, ""):
            tags.append({"code": code, "name": str(name)})
    return tags


class OfficialSearchPageAdapter(RecruitmentAdapter):
    search_urls: Dict[str, str] = {}

    def fetch_page(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        keyword: str = "",
        filters: Optional[Dict] = None,
        recruitment_type: str = "campus",
        include_detail: bool = True,
    ) -> JobPage:
        del keyword, filters, include_detail
        size = self._page_size(page_size)
        if recruitment_type not in self.search_urls:
            return JobPage(items=[], page=page, page_size=size, total=0, has_more=False)
        response = self._request(
            "GET",
            self.search_urls[recruitment_type],
            headers={"User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)"},
            timeout=(8, 20),
        )
        # These official sites are mostly client-rendered and do not expose a
        # stable unauthenticated JSON shape here yet. The request proves source
        # availability while keeping this adapter safe and non-failing.
        if response.status_code >= 400:
            return JobPage(items=[], page=page, page_size=size, total=0, has_more=False)
        return JobPage(items=[], page=page, page_size=size, total=0, has_more=False)


class AlibabaRecruitmentAdapter(OfficialSearchPageAdapter):
    source = "alibaba"
    company = "阿里巴巴"
    SEARCH_URL = "https://campus-talent.alibaba.com/position/search"
    XSRF_TOKEN = "7278d090-03b3-4810-a057-f882eca30cd0"
    INTERNSHIP_BATCH_IDS = (100000540002, 100000560002, 100000560001)
    max_page_size = 50
    search_urls = {
        "intern": "https://campus-talent.alibaba.com/campus/position?batchId=100000560001",
    }

    COOKIES = {
        "cna": "5867IrtNdVYCAXAK+jqhIA5v",
        "xlly_s": "1",
        "XSRF-TOKEN": XSRF_TOKEN,
        "SESSION": "ODY0MzMwNDJBNjQ2MzdBRTg2RjQ4MkI1NEUyREI3QjA=",
        "tfstk": "gFds0U9AOndUxj3tDluUPzv0UuCfM2lPBr_vrEFak1COcstekRPwWi5jl3-UgtHM0j6X0nuGHcfwGHtvcOSV7G-BkHLD7SJN_KaMO3N4_cDMkS1VM0orab8iIsfx46-GaT2GuZl4B5BAs6pwyDJEab8MWP7tzehy3WIwBZSAMOBx9wIhooFvDOFLvMbcklQY62TdxMQYBNCx9eQVuoU9Ds3BJMbAMNKAB2TdxZCADfAbPZM1jFgcLxHgLSmTjGVYMB_1pv81vL9ruNW1AFII2gRd5ujJWMNYMgfQ5W8vDmNVwLxBGTKrGWfwPpCd5pgYpGBWBh7HcbNOXBT96GRtY5S9sepygH3YMi9petpJWDyCRpLwO9R-VS6MphvlhIoEZ1JyzIXJ6fZlYTbXV1pIv5tR4uVPV93uhy6uGwsrR2w0nbzLJHqhhS0PBwb1L2gQXKXO-w_tR2w0nOQh8uuIRlpc.",
        "isg": "BMHBEJ30TyXcSaMQcyEiPwhk0Avb7jXgwaEYvSMXKEhACuLcaj5JstNM7H5MAs0Y",
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
        del include_detail
        size = self._page_size(page_size)
        if recruitment_type != "intern":
            return JobPage(items=[], page=page, page_size=size, total=0, has_more=False)

        items_by_id = {}
        total = 0
        has_more = False
        for batch_id in self.INTERNSHIP_BATCH_IDS:
            payload = {
                "batchId": batch_id,
                "pageIndex": max(page, 1),
                "pageSize": size,
                "channel": "campus_group_official_site",
                "language": "zh",
            }
            if keyword.strip():
                payload["key"] = keyword.strip()
            payload.update(filters or {})
            data = self._request(
                "POST",
                self.SEARCH_URL,
                params={"_csrf": self.XSRF_TOKEN},
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Content-Type": "application/json",
                    "Origin": "https://campus-talent.alibaba.com",
                    "Referer": self.search_urls["intern"],
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                    "bx-v": "2.5.36",
                },
                cookies=self.COOKIES,
                json=payload,
            ).json()
            if not data.get("success"):
                continue
            content = data.get("content") or {}
            batch_items = [self._normalize_job(item, recruitment_type) for item in content.get("datas") or []]
            for item in batch_items:
                items_by_id.setdefault(item.source_job_id, item)
            batch_total = int(content.get("totalCount") or len(batch_items))
            total += batch_total
            has_more = has_more or max(page, 1) * size < batch_total

        return JobPage(
            items=list(items_by_id.values()),
            page=page,
            page_size=size,
            total=total,
            has_more=has_more,
        )

    def _normalize_job(self, raw: Dict, recruitment_type: str) -> JobPosting:
        job_id = str(raw.get("id") or "")
        batch_name = str(raw.get("batchName") or "").strip()
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(raw.get("name") or "").strip(),
            category=raw.get("categoryName"),
            job_family=raw.get("categoryName"),
            official_taxonomy={
                "level1": {"code": None, "name": raw.get("categoryName"), "path": "categoryName"},
                "level2": {"code": raw.get("trackId"), "name": raw.get("trackName"), "path": "trackId"},
                "level3": None,
                "tags": _safe_tags(raw.get("tags")),
            },
            location=_normalize_city(raw.get("workLocations")),
            country="中国",
            business_unit=raw.get("department"),
            product=batch_name or None,
            recruitment_type=recruitment_type,
            employment_type="实习",
            description=str(raw.get("description") or "").strip(),
            requirements=str(raw.get("requirement") or "").strip(),
            highlights=batch_name,
            source_url=f"https://campus-talent.alibaba.com/campus/position-detail?positionId={job_id}",
            updated_at=_parse_datetime(raw.get("modifyTime") or raw.get("publishTime")),
            raw_data=raw,
        )


class MeituanRecruitmentAdapter(OfficialSearchPageAdapter):
    source = "meituan"
    company = "美团"
    SEARCH_URL = "https://zhaopin.meituan.com/api/official/job/getJobList"
    DETAIL_URL = "https://zhaopin.meituan.com/api/official/job/getJobDetail"
    max_page_size = 50
    search_urls = {
        "campus": "https://zhaopin.meituan.com/web/campus",
        "intern": "https://zhaopin.meituan.com/web/campus",
        "social": "https://zhaopin.meituan.com/web/social",
    }

    JOB_TYPE_FILTERS = {
        "campus": [{"code": "1", "subCode": []}],
        "intern": [{"code": "2", "subCode": []}],
        "social": [{"code": "3", "subCode": []}],
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
        job_type = self.JOB_TYPE_FILTERS.get(recruitment_type)
        if not job_type:
            return JobPage(items=[], page=page, page_size=size, total=0, has_more=False)
        payload = {
            "page": {"pageNo": max(page, 1), "pageSize": size},
            "jobShareType": "1",
            "keywords": keyword.strip(),
            "cityList": [],
            "department": [],
            "jfJgList": [],
            "jobType": job_type,
            "typeCode": [],
            "specialCode": [],
        }
        payload.update(filters or {})
        data = self._request(
            "POST",
            self.SEARCH_URL,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": "https://zhaopin.meituan.com",
                "Referer": self.search_urls.get(recruitment_type, self.search_urls["campus"]),
                "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)",
            },
            json=payload,
        ).json()
        result = data.get("data") or {}
        page_info = result.get("page") or {}
        items = []
        for item in result.get("list") or []:
            detail = self.fetch_detail(str(item.get("jobUnionId") or item.get("jobId") or "")) if include_detail else {}
            raw = {**item, **{key: value for key, value in detail.items() if value not in (None, "")}}
            items.append(self._normalize_job(raw, recruitment_type))
            if include_detail and self.sleep_interval > 0:
                time.sleep(min(self.sleep_interval, 1))
        total = int(page_info.get("totalCount") or len(items))
        return JobPage(
            items=items,
            page=page,
            page_size=size,
            total=total,
            has_more=page * size < total and bool(items),
        )

    def fetch_detail(self, job_union_id: str) -> Dict:
        if not job_union_id:
            return {}
        data = self._request(
            "POST",
            self.DETAIL_URL,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": "https://zhaopin.meituan.com",
                "Referer": f"https://zhaopin.meituan.com/web/position/detail?jobUnionId={job_union_id}",
                "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)",
            },
            json={"jobUnionId": job_union_id},
        ).json()
        return data.get("data") or {}

    def _normalize_job(self, raw: Dict, recruitment_type: str = "campus") -> JobPosting:
        job_id = str(raw.get("jobUnionId") or raw.get("jobId") or "")
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(raw.get("name") or "").strip(),
            category=raw.get("jobFamily"),
            job_family=raw.get("jobFamilyGroup") or raw.get("jobFamily"),
            official_taxonomy={
                "level1": {"code": None, "name": raw.get("jobFamily"), "path": "jobFamily"},
                "level2": {"code": None, "name": raw.get("jobFamilyGroup"), "path": "jobFamilyGroup"},
                "level3": {"code": raw.get("jobSpecialCode"), "name": None, "path": "jobSpecialCode"},
                "tags": _safe_tags(raw.get("tag")),
            },
            location=self._join_names(raw.get("cityList")),
            country="中国",
            business_unit=self._join_names(raw.get("department")),
            product=raw.get("projectName"),
            recruitment_type=recruitment_type,
            employment_type=self._employment_type(raw.get("jobType"), recruitment_type),
            experience=raw.get("workYear"),
            description=str(raw.get("jobDuty") or raw.get("desc") or "").strip(),
            requirements=str(raw.get("jobRequirement") or "").strip(),
            highlights=str(raw.get("highLight") or "").strip(),
            source_url=f"https://zhaopin.meituan.com/web/position/detail?jobUnionId={job_id}",
            updated_at=self._parse_timestamp(raw.get("refreshTime") or raw.get("firstPostTime")),
            raw_data=raw,
        )

    @staticmethod
    def _join_names(value) -> Optional[str]:
        if not value:
            return None
        if isinstance(value, list):
            names = [str(item.get("name") or "").strip() for item in value if isinstance(item, dict)]
            return "、".join(name for name in names if name) or None
        if isinstance(value, dict):
            return value.get("name")
        return str(value)

    @staticmethod
    def _employment_type(value, recruitment_type: str) -> str:
        mapping = {"1": "校招", "2": "实习", "3": "社招"}
        return mapping.get(str(value or ""), {"campus": "校招", "intern": "实习", "social": "社招"}.get(recruitment_type, "校招"))

    @staticmethod
    def _parse_timestamp(value) -> Optional[datetime]:
        if not value:
            return None
        try:
            number = int(value)
            if number > 10_000_000_000:
                number = number / 1000
            return datetime.fromtimestamp(number)
        except (TypeError, ValueError, OSError):
            return None


class BaiduRecruitmentAdapter(OfficialSearchPageAdapter):
    source = "baidu"
    company = "百度"
    SEARCH_URL = "https://talent.baidu.com/httservice/getPostListNew"
    DETAIL_URL = "https://talent.baidu.com/httservice/getPostDetail"
    max_page_size = 20
    search_urls = {
        "campus": "https://talent.baidu.com/jobs/list?recruitType=GRADUATE",
        "intern": "https://talent.baidu.com/jobs/list?recruitType=INTERN",
        "social": "https://talent.baidu.com/jobs/social",
    }
    RECRUIT_TYPES = {
        "campus": "GRADUATE",
        "intern": "INTERN",
        "social": "SOCIAL",
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
        del include_detail
        size = self._page_size(page_size)
        recruit_type = self.RECRUIT_TYPES.get(recruitment_type, self.RECRUIT_TYPES["campus"])
        payload = {
            "recruitType": recruit_type,
            "curPage": max(page, 1),
            "pageSize": size,
            "keyWord": keyword.strip(),
            "projectType": "",
            "workPlace": [],
            "postType": [],
        }
        payload.update(filters or {})
        data = self._request(
            "POST",
            self.SEARCH_URL,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://talent.baidu.com",
                "Referer": self.search_urls.get(recruitment_type, self.search_urls["campus"]),
                "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)",
            },
            data=payload,
        ).json()
        if data.get("status") != "ok":
            return JobPage(items=[], page=page, page_size=size, total=0, has_more=False)
        result = data.get("data") or {}
        items = [self._normalize_job(item, recruitment_type, recruit_type) for item in result.get("list") or []]
        total = int(result.get("total") or len(items))
        return JobPage(items=items, page=page, page_size=size, total=total, has_more=page * size < total and bool(items))

    def _normalize_job(self, raw: Dict, recruitment_type: str, recruit_type: str) -> JobPosting:
        post_id = str(raw.get("postId") or raw.get("jobId") or "")
        return JobPosting(
            source=self.source,
            source_job_id=post_id,
            company=self.company,
            title=str(raw.get("name") or "").strip(),
            category=raw.get("postType"),
            job_family=raw.get("postType"),
            official_taxonomy={
                "level1": {"code": raw.get("postTypeCode"), "name": raw.get("postType"), "path": "postType"},
                "level2": None,
                "level3": None,
                "tags": [],
            },
            location=_normalize_city(raw.get("workPlace")),
            country="中国",
            business_unit=raw.get("orgName") or raw.get("bgShortName"),
            product=raw.get("projectType"),
            recruitment_type=recruitment_type,
            employment_type=_label(recruitment_type),
            experience=raw.get("workYears") or raw.get("education"),
            description=str(raw.get("workContent") or "").strip(),
            requirements=str(raw.get("serviceCondition") or "").strip(),
            highlights=str(raw.get("jobDescription") or "").strip(),
            source_url=f"https://talent.baidu.com/jobs/detail/{recruit_type}/{post_id}",
            updated_at=_parse_datetime(raw.get("updateDate") or raw.get("publishDate")),
            raw_data=raw,
        )


class JDRecruitmentAdapter(OfficialSearchPageAdapter):
    source = "jd"
    company = "京东"
    SEARCH_URL = "https://campus.jd.com/api/wx/position/page"
    max_page_size = 50
    search_urls = {
        "campus": "https://campus.jd.com/#/jobs",
        "intern": "https://campus.jd.com/#/jobs",
    }
    TYPE_PARAMS = {
        "campus": "present",
        "intern": "internship",
    }
    PLAN_IDS = {
        "campus": [52, 53, 54],
        "intern": [45, 51],
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
        del include_detail
        size = self._page_size(page_size)
        if recruitment_type not in self.TYPE_PARAMS:
            return JobPage(items=[], page=page, page_size=size, total=0, has_more=False)
        payload = {
            "pageSize": size,
            "pageIndex": max(page - 1, 0),
            "parameter": {
                "positionName": keyword.strip(),
                "planIdList": self.PLAN_IDS[recruitment_type],
                "jobDirectionCodeList": [],
                "workCityCodeList": [],
                "positionDeptList": [],
            },
        }
        if filters:
            payload["parameter"].update(filters)
        data = self._request(
            "POST",
            self.SEARCH_URL,
            params={"type": self.TYPE_PARAMS.get(recruitment_type, "")},
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": "https://campus.jd.com",
                "Referer": self.search_urls.get(recruitment_type, self.search_urls["campus"]),
                "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)",
            },
            json=payload,
        ).json()
        body = data.get("body") or {}
        items = [self._normalize_job(item, recruitment_type) for item in body.get("items") or []]
        total = int(body.get("totalNumber") or len(items))
        return JobPage(items=items, page=page, page_size=size, total=total, has_more=page * size < total and bool(items))

    def _normalize_job(self, raw: Dict, recruitment_type: str) -> JobPosting:
        publish_id = str(raw.get("publishId") or raw.get("reqId") or "")
        city = raw.get("workCity") or self._join_requirement(raw.get("requirementVoList"), "workCity")
        return JobPosting(
            source=self.source,
            source_job_id=publish_id,
            company=self.company,
            title=str(raw.get("positionName") or "").strip(),
            category=raw.get("jobDirection"),
            job_family=raw.get("jobCategory") or raw.get("jobDirection"),
            official_taxonomy={
                "level1": {"code": raw.get("jobDirectionCode"), "name": raw.get("jobDirection"), "path": "jobDirection"},
                "level2": {"code": raw.get("jobCategoryCode"), "name": raw.get("jobCategory"), "path": "jobCategory"},
                "level3": None,
                "tags": _safe_tags(raw.get("reqTagList")),
            },
            location=_normalize_city(city),
            country="中国",
            business_unit=raw.get("positionDept"),
            recruitment_type=recruitment_type,
            employment_type=_label(recruitment_type),
            description=str(raw.get("workContent") or "").strip(),
            requirements=str(raw.get("qualification") or "").strip(),
            highlights=str(raw.get("positionDept") or "").strip(),
            source_url=f"https://campus.jd.com/#/jobs?publishId={publish_id}",
            updated_at=_parse_datetime(raw.get("publishTime")),
            raw_data=raw,
        )

    @staticmethod
    def _join_requirement(value, key: str) -> Optional[str]:
        if not isinstance(value, list):
            return None
        values = []
        seen = set()
        for item in value:
            if not isinstance(item, dict):
                continue
            text = str(item.get(key) or "").strip()
            if text and text not in seen:
                seen.add(text)
                values.append(text)
        return "、".join(values) or None


class KuaishouRecruitmentAdapter(OfficialSearchPageAdapter):
    source = "kuaishou"
    company = "快手"
    SEARCH_URL = "https://zhaopin.kuaishou.cn/recruit/e/api/v1/open/positions/simple"
    LABEL_URL = "https://zhaopin.kuaishou.cn/recruit/e/api/v1/open/positions/label"
    SECRET = "652f962a-0575-4575-98d2-f04e2291bee2"
    max_page_size = 50
    search_urls = {
        "intern": "https://zhaopin.kuaishou.cn/recruit/e/#/official/campus/",
        "social": "https://zhaopin.kuaishou.cn/recruit/e/#/official/social/",
    }
    POSITION_NATURE = {
        "intern": "C002",
        "social": "C001",
    }

    def __init__(self, sleep_interval: Optional[float] = None):
        super().__init__(sleep_interval)
        self._category_labels = {}

    def fetch_page(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        keyword: str = "",
        filters: Optional[Dict] = None,
        recruitment_type: str = "campus",
        include_detail: bool = True,
    ) -> JobPage:
        del include_detail
        size = self._page_size(page_size)
        if recruitment_type not in self.POSITION_NATURE:
            return JobPage(items=[], page=page, page_size=size, total=0, has_more=False)
        params = {
            "pageNum": max(page, 1),
            "pageSize": size,
        }
        if keyword.strip():
            params["name"] = keyword.strip()
        params["positionNatureCode"] = self.POSITION_NATURE[recruitment_type]
        params.update(filters or {})
        timestamp, signature = self._sign(params)
        data = self._request(
            "GET",
            self.SEARCH_URL,
            params=params,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": self.search_urls.get(recruitment_type) or self.search_urls["intern"],
                "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)",
                "sign": signature,
                "signTimestamp": timestamp,
            },
        ).json()
        result = data.get("result") or {}
        labels = self._category_names(recruitment_type)
        items = [self._normalize_job(item, recruitment_type, labels) for item in result.get("list") or []]
        total = int(result.get("total") or len(items))
        return JobPage(items=items, page=page, page_size=size, total=total, has_more=page * size < total and bool(items))

    def _normalize_job(self, raw: Dict, recruitment_type: str, labels: Optional[Dict[str, str]] = None) -> JobPosting:
        job_id = str(raw.get("id") or raw.get("code") or "")
        category_code = raw.get("positionCategoryCode")
        category_name = raw.get("positionCategoryName") or (labels or {}).get(str(category_code or ""))
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(raw.get("name") or "").strip(),
            category=category_name or category_code,
            job_family=raw.get("positionClassName") or category_name or category_code,
            official_taxonomy={
                "level1": {"code": category_code, "name": category_name, "path": "positionCategoryCode"},
                "level2": {"code": raw.get("positionClassCode"), "name": raw.get("positionClassName"), "path": "positionClassCode"},
                "level3": None,
                "tags": [],
            },
            location=_normalize_city(raw.get("workLocationName") or raw.get("workLocationCode")),
            country="中国",
            business_unit=raw.get("departmentName") or raw.get("departmentCode"),
            product=raw.get("recruitProjectName") or raw.get("recruitProjectCode"),
            recruitment_type=recruitment_type,
            employment_type=_label(recruitment_type),
            experience=raw.get("workExperienceName") or raw.get("workExperienceCode"),
            description=str(raw.get("description") or "").strip(),
            requirements=str(raw.get("positionDemand") or "").strip(),
            highlights=str(raw.get("projectDescription") or "").strip(),
            source_url=f"https://zhaopin.kuaishou.cn/recruit/e/#/official/social/job-info/{job_id}",
            updated_at=_parse_datetime(raw.get("releaseTime") or raw.get("updateTime") or raw.get("createTime")),
            raw_data=raw,
        )

    def _category_names(self, recruitment_type: str) -> Dict[str, str]:
        if recruitment_type in self._category_labels:
            return self._category_labels[recruitment_type]
        params = {"channelCode": "official", "positionNatureCode": self.POSITION_NATURE[recruitment_type]}
        timestamp, signature = self._sign(params)
        try:
            data = self._request(
                "GET",
                self.LABEL_URL,
                params=params,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Referer": self.search_urls[recruitment_type],
                    "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)",
                    "sign": signature,
                    "signTimestamp": timestamp,
                },
            ).json()
            labels = {
                str(item.get("code")): str(item.get("name"))
                for item in (data.get("result") or {}).get("category") or []
                if item.get("code") and item.get("name")
            }
        except Exception:
            labels = {}
        self._category_labels[recruitment_type] = labels
        return labels

    def _sign(self, params: Dict):
        timestamp = str(int(time.time() * 1000))
        parts = []
        for key in sorted(params):
            values = params[key] if isinstance(params[key], list) else [params[key]]
            values = sorted(str(value) for value in values if value not in (None, ""))
            if values:
                encoded = ",".join(quote_plus(value) for value in values)
                parts.append(f"{key}={encoded}")
        message = timestamp + "&".join(parts) + self.SECRET
        signature = hmac.new(self.SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
        return timestamp, signature


class HuaweiRecruitmentAdapter(OfficialSearchPageAdapter):
    source = "huawei"
    company = "华为"
    SEARCH_URL = "https://career.huawei.com/reccampportal/services/portal/portalpub/getJob/newHr/page"
    DETAIL_URL = "https://career.huawei.com/reccampportal/services/portal/portalpub/getJobDetail/newHr"
    max_page_size = 50
    search_urls = {
        "campus": "https://career.huawei.com/reccampportal/portal5/campus-recruitment.html",
        "intern": "https://career.huawei.com/reccampportal/portal5/campus-recruitment.html",
        "social": "https://career.huawei.com/reccampportal/portal5/social-recruitment.html",
    }
    JOB_TYPES = {
        "campus": "0",
        "intern": "2",
        "social": "1",
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
        params = {
            "keyword": keyword.strip(),
            "jobTypes": self.JOB_TYPES.get(recruitment_type, "0"),
            "jobType": self.JOB_TYPES.get(recruitment_type, "0"),
            "language": "zh_CN",
        }
        params.update(filters or {})
        data = self._request(
            "GET",
            f"{self.SEARCH_URL}/{size}/{max(page, 1)}",
            params=params,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": self.search_urls.get(recruitment_type, self.search_urls["campus"]),
                "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)",
            },
        ).json()
        page_info = data.get("pageVO") or {}
        items = []
        for item in data.get("result") or []:
            detail = self.fetch_detail(item) if include_detail else {}
            raw = {**item, **{key: value for key, value in detail.items() if value not in (None, "")}}
            items.append(self._normalize_job(raw, recruitment_type))
            if include_detail and self.sleep_interval > 0:
                time.sleep(min(self.sleep_interval, 1))
        total = int(page_info.get("totalRows") or len(items))
        return JobPage(items=items, page=page, page_size=size, total=total, has_more=page * size < total and bool(items))

    def fetch_detail(self, raw: Dict) -> Dict:
        job_id = str(_first_present(raw, "jobId", "jobRequirementId", "advertisementCode", "positionReqCode") or "")
        if not job_id:
            return {}
        data = self._request(
            "GET",
            self.DETAIL_URL,
            params={
                "jobId": job_id,
                "dataSource": raw.get("dataSource"),
            },
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://career.huawei.com/reccampportal/portal5/campus-recruitment-detail.html",
                "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)",
            },
        ).json()
        return data if isinstance(data, dict) else {}

    def _normalize_job(self, raw: Dict, recruitment_type: str) -> JobPosting:
        job_id = str(_first_present(raw, "jobId", "jobRequirementId", "advertisementCode", "positionReqCode") or "")
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(_first_present(raw, "jobname", "nameCn", "jobName") or "").strip(),
            category=raw.get("jobFamilyName") or raw.get("jobFamClsCode"),
            job_family=raw.get("jobSubcategoryName") or raw.get("jobClassName") or raw.get("jobFamilyName") or raw.get("jobSubcategory"),
            official_taxonomy={
                "level1": {"code": raw.get("jobFamClsCode"), "name": raw.get("jobFamilyName"), "path": "jobFamilyName"},
                "level2": {"code": raw.get("jobClass"), "name": raw.get("jobClassName"), "path": "jobClass"},
                "level3": {"code": raw.get("jobSubcategory"), "name": raw.get("jobSubcategoryName"), "path": "jobSubcategory"},
                "tags": [],
            },
            location=_normalize_city(raw.get("jobArea") or raw.get("jobAddress")),
            country="中国",
            business_unit=raw.get("deptName") or raw.get("deptFullName"),
            recruitment_type=recruitment_type,
            employment_type=_label(recruitment_type),
            experience=str(_first_present(raw, "workYear", "degree") or ""),
            description=str(raw.get("mainBusiness") or raw.get("mostlyDuty") or "").strip(),
            requirements=str(raw.get("jobRequire") or raw.get("demand") or "").strip(),
            highlights=str(raw.get("bonusPoints") or raw.get("bonus") or "").strip(),
            source_url=f"https://career.huawei.com/reccampportal/portal5/campus-recruitment-detail.html?jobId={job_id}",
            updated_at=_parse_datetime(raw.get("lastUpdateDate") or raw.get("releaseDate") or raw.get("creationDate")),
            raw_data=raw,
        )


class PDDRecruitmentAdapter(OfficialSearchPageAdapter):
    source = "pdd"
    company = "拼多多"
    SEARCH_URL = "https://careers.pddglobalhr.com/api/careers/api/recruit/position/list"
    DETAIL_URL = "https://careers.pddglobalhr.com/api/careers/api/recruit/position/detail"
    default_page_size = 10
    max_page_size = 10
    search_urls = {"campus": "https://careers.pddglobalhr.com/campus/grad"}

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
        if recruitment_type != "campus":
            return JobPage(items=[], page=page, page_size=size, total=0, has_more=False)
        payload = {"page": max(page, 1), "pageSize": size}
        if keyword.strip():
            payload["keyword"] = keyword.strip()
        payload.update(filters or {})
        data = self._request(
            "POST",
            self.SEARCH_URL,
            json=payload,
            headers={"Referer": self.search_urls["campus"], "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)"},
        ).json()
        result = data.get("result") or {}
        items = []
        for item in result.get("list") or []:
            detail = self.fetch_detail(item) if include_detail else {}
            raw = {**item, **{key: value for key, value in detail.items() if value not in (None, "")}}
            items.append(self._normalize_job(raw, recruitment_type))
        total = int(result.get("total") or len(items))
        return JobPage(items=items, page=page, page_size=size, total=total, has_more=page * size < total and bool(items))

    def fetch_detail(self, raw: Dict) -> Dict:
        job_id = str(raw.get("id") or "")
        if not job_id:
            return {}
        data = self._request(
            "POST",
            self.DETAIL_URL,
            json={"id": job_id},
            headers={"Referer": self.search_urls["campus"], "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)"},
        ).json()
        return data.get("result") or {}

    def _normalize_job(self, raw: Dict, recruitment_type: str) -> JobPosting:
        job_id = str(raw.get("id") or "")
        category = raw.get("jobName")
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(raw.get("name") or "").strip(),
            category=category,
            job_family=category,
            official_taxonomy={
                "level1": {"code": raw.get("job"), "name": category, "path": "job"},
                "level2": None,
                "level3": None,
                "tags": _safe_tags(raw.get("labelList")),
            },
            location=_normalize_city(raw.get("workLocationName") or raw.get("workLocation")),
            country="中国",
            recruitment_type=recruitment_type,
            employment_type=str(raw.get("recruitTypeName") or _label(recruitment_type)),
            experience=str(raw.get("graduationYear") or ""),
            description=str(raw.get("jobDuty") or "").strip(),
            requirements=str(raw.get("serveRequirement") or "").strip(),
            highlights=str(raw.get("recruitTypeName") or "").strip(),
            preferred_qualifications=str(raw.get("bonus") or "").strip(),
            source_url=str(raw.get("shareUrl") or f"https://careers.pddglobalhr.com/campus/grad/detail?positionId={job_id}"),
            updated_at=_parse_datetime(raw.get("releaseTime")),
            raw_data=raw,
        )


class XiaomiRecruitmentAdapter(OfficialSearchPageAdapter):
    source = "xiaomi"
    company = "小米"
    SEARCH_URL = "https://hr.xiaomi.com/website/api/agent/searchJobPage"
    max_page_size = 100
    search_urls = {
        "campus": "https://hr.xiaomi.com/campus/",
        "intern": "https://hr.xiaomi.com/campus/",
        "social": "https://hr.xiaomi.com/job",
    }
    JOB_TYPES = {"social": 1, "campus": 2, "intern": 3}

    def fetch_page(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        keyword: str = "",
        filters: Optional[Dict] = None,
        recruitment_type: str = "campus",
        include_detail: bool = True,
    ) -> JobPage:
        del include_detail
        size = self._page_size(page_size)
        job_type = self.JOB_TYPES.get(recruitment_type)
        if not job_type:
            return JobPage(items=[], page=page, page_size=size, total=0, has_more=False)
        params = {"pageNum": max(page, 1), "pageSize": size, "type": job_type}
        if keyword.strip():
            params["keyword"] = keyword.strip()
        params.update(filters or {})
        data = self._request(
            "GET",
            self.SEARCH_URL,
            params=params,
            headers={"Referer": self.search_urls[recruitment_type], "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)"},
        ).json()
        result = data.get("data") or {}
        items = [self._normalize_job(item, recruitment_type) for item in result.get("list") or []]
        total = int(result.get("total") or len(items))
        actual_size = int(result.get("pageSize") or size)
        return JobPage(items=items, page=page, page_size=actual_size, total=total, has_more=page * actual_size < total and bool(items))

    def _normalize_job(self, raw: Dict, recruitment_type: str) -> JobPosting:
        job_id = str(_first_present(raw, "jobPostId", "jobId", "id") or "")
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(raw.get("title") or "").strip(),
            official_taxonomy={
                "level1": None,
                "level2": None,
                "level3": None,
                "tags": [{"code": raw.get("type"), "name": _label(recruitment_type)}],
            },
            location=_normalize_city(raw.get("cityZhNames")),
            country="中国",
            business_unit=raw.get("levelOneDeptName"),
            recruitment_type=recruitment_type,
            employment_type=_label(recruitment_type),
            experience=str(raw.get("expectedJobLevel") or ""),
            description=str(raw.get("description") or "").strip(),
            requirements=str(raw.get("requirement") or "").strip(),
            source_url=str(raw.get("url") or f"https://hr.xiaomi.com/website/opportunities.html?jobId={job_id}"),
            updated_at=_parse_datetime(raw.get("publishTime")),
            raw_data=raw,
        )


class XiaohongshuRecruitmentAdapter(OfficialSearchPageAdapter):
    source = "xiaohongshu"
    company = "小红书"
    SEARCH_URL = "https://job.xiaohongshu.com/websiterecruit/position/pageQueryPosition"
    default_page_size = 10
    max_page_size = 10
    search_urls = {
        "campus": "https://job.xiaohongshu.com/campus",
        "intern": "https://job.xiaohongshu.com/intern",
        "social": "https://job.xiaohongshu.com/social",
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
        del include_detail
        size = self._page_size(page_size)
        if recruitment_type not in self.search_urls:
            return JobPage(items=[], page=page, page_size=size, total=0, has_more=False)
        payload = {"recruitType": recruitment_type, "pageNum": max(page, 1), "pageSize": size}
        if keyword.strip():
            payload["keyword"] = keyword.strip()
        payload.update(filters or {})
        data = self._request(
            "POST",
            self.SEARCH_URL,
            json=payload,
            headers={"Referer": self.search_urls[recruitment_type], "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)"},
        ).json()
        result = data.get("data") or {}
        items = [self._normalize_job(item, recruitment_type) for item in result.get("list") or []]
        total = int(result.get("total") or len(items))
        actual_size = int(result.get("pageSize") or size)
        total_pages = int(result.get("totalPage") or 0)
        return JobPage(items=items, page=page, page_size=actual_size, total=total, has_more=page < total_pages and bool(items))

    def _normalize_job(self, raw: Dict, recruitment_type: str) -> JobPosting:
        job_id = str(raw.get("positionId") or "")
        category = raw.get("jobType") or raw.get("positionType")
        tags = _safe_tags(raw.get("labels"))
        if raw.get("jobProjectName"):
            tags.append({"code": raw.get("jobProject"), "name": str(raw["jobProjectName"])})
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(raw.get("positionName") or "").strip(),
            category=category,
            job_family=category,
            official_taxonomy={
                "level1": {"code": None, "name": category, "path": "jobType"},
                "level2": None,
                "level3": None,
                "tags": tags,
            },
            location=_normalize_city(raw.get("workplace")),
            country="中国",
            recruitment_type=recruitment_type,
            employment_type=_label(recruitment_type),
            experience=" / ".join(str(value) for value in (raw.get("workExperience"), raw.get("education")) if value),
            description=str(raw.get("duty") or "").strip(),
            requirements=str(raw.get("qualification") or "").strip(),
            highlights=str(raw.get("jobProjectName") or "").strip(),
            source_url=f"https://job.xiaohongshu.com/{recruitment_type}/position/{job_id}",
            updated_at=_parse_datetime(raw.get("publishTime")),
            raw_data=raw,
        )


def _decrypt_moka_payload(payload: Dict, aes_iv: str) -> Dict:
    decryptor = Cipher(
        algorithms.AES(str(payload["necromancer"]).encode()),
        modes.CBC(aes_iv.encode()),
    ).decryptor()
    padded = decryptor.update(base64.b64decode(payload["data"])) + decryptor.finalize()
    unpadder = PKCS7(128).unpadder()
    return json.loads(unpadder.update(padded) + unpadder.finalize())


def _split_moka_description(value: str):
    text = BeautifulSoup(value or "", "html.parser").get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    marker = re.search(
        r"(?m)^(?:【)?(?:任职要求|任职资格|职位要求|职位资格|岗位要求|核心要求|我们期待|我们希望|你需要)",
        text,
    )
    if not marker:
        return text, text
    description, requirements = text[:marker.start()].strip(), text[marker.start():].strip()
    return description or text, requirements or text


def _moka_locations(raw: Dict):
    locations = raw.get("locations") or []
    names = []
    countries = []
    country_names = {"China": "中国", "USA": "美国", "Singapore": "新加坡"}
    for item in locations:
        country = country_names.get(item.get("country"), item.get("country"))
        city = _normalize_city(item.get("cityName"))
        name = city or country
        if name and name not in names:
            names.append(name)
        if country and country not in countries:
            countries.append(country)
    return "、".join(names) or None, "、".join(countries) or "中国"


def _moka_is_intern(raw: Dict) -> bool:
    return str(raw.get("commitment") or "") == "实习" or "实习" in str(raw.get("title") or "")


class MokaRecruitmentAdapter(OfficialSearchPageAdapter):
    JOBS_URL = "https://app.mokahr.com/api/outer/ats-apply/website/jobs/v2"
    max_page_size = 100
    portals: Dict[str, list] = {}

    def __init__(self, sleep_interval: Optional[float] = None):
        super().__init__(sleep_interval)
        self._jobs_cache = {}

    def fetch_page(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        keyword: str = "",
        filters: Optional[Dict] = None,
        recruitment_type: str = "social",
        include_detail: bool = True,
    ) -> JobPage:
        del filters, include_detail
        size = self._page_size(page_size)
        jobs = self._load_jobs(recruitment_type)
        if keyword.strip():
            lowered = keyword.strip().lower()
            jobs = [job for job in jobs if lowered in f"{job.title} {job.category or ''} {job.description} {job.requirements}".lower()]
        start = (max(page, 1) - 1) * size
        return JobPage(
            items=jobs[start:start + size],
            page=page,
            page_size=size,
            total=len(jobs),
            has_more=start + size < len(jobs),
        )

    def _load_jobs(self, recruitment_type: str):
        if recruitment_type in self._jobs_cache:
            return self._jobs_cache[recruitment_type]
        unique = {}
        for portal in self.portals.get(recruitment_type, []):
            for raw in self._fetch_portal(portal):
                wanted = portal.get("commitment")
                is_intern = _moka_is_intern(raw)
                if wanted == "intern" and not is_intern:
                    continue
                if wanted == "non_intern" and is_intern:
                    continue
                normalized = self._normalize_job(raw, recruitment_type)
                unique[normalized.source_job_id] = normalized
        self._jobs_cache[recruitment_type] = list(unique.values())
        return self._jobs_cache[recruitment_type]

    def _fetch_portal(self, portal: Dict):
        response = self._request(
            "GET",
            portal["url"],
            headers={"User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)"},
        )
        node = BeautifulSoup(response.text, "html.parser").select_one("#init-data")
        if not node or not node.get("value"):
            raise ValueError(f"{self.company} Moka 门户缺少初始化数据")
        init_data = json.loads(node["value"])
        jobs = []
        offset = 0
        limit = 30
        while True:
            encrypted = self._request(
                "POST",
                self.JOBS_URL,
                json={
                    "orgId": portal["org_id"],
                    "siteId": portal["site_id"],
                    "limit": limit,
                    "offset": offset,
                    "needStat": False,
                    "site": portal["site"],
                    "locale": "zh_cn",
                },
                headers={"Referer": portal["url"], "User-Agent": "Mozilla/5.0 (compatible; OfferLensRecruitmentCrawler/1.0)"},
            ).json()
            decoded = _decrypt_moka_payload(encrypted, init_data["aesIv"])
            if not decoded.get("success"):
                raise ValueError(f"{self.company} Moka 岗位接口失败：{decoded.get('msg') or decoded.get('code')}")
            batch = ((decoded.get("data") or {}).get("jobs") or [])
            jobs.extend({**item, "_moka_portal_url": portal["url"]} for item in batch)
            if len(batch) < limit:
                return jobs
            offset += limit

    def _normalize_job(self, raw: Dict, recruitment_type: str) -> JobPosting:
        category_data = raw.get("zhineng") or {}
        category = category_data.get("name") if isinstance(category_data, dict) else str(category_data or "")
        department = raw.get("department") or {}
        business_unit = department.get("name") if isinstance(department, dict) else str(department or "")
        description, requirements = _split_moka_description(str(raw.get("jobDescription") or ""))
        location, country = _moka_locations(raw)
        job_id = str(raw.get("id") or "")
        portal_url = str(raw.get("_moka_portal_url") or self.search_urls.get(recruitment_type) or "")
        portal_base = portal_url.split("#", 1)[0]
        employment_type = (
            _label(recruitment_type)
            if recruitment_type in {"campus", "intern"}
            else str(raw.get("commitment") or ("实习/全职" if re.search(r"实习\s*/\s*全职|全职\s*/\s*实习", description) else _label(recruitment_type)))
        )
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(raw.get("title") or "").strip(),
            category=category or None,
            job_family=category or None,
            official_taxonomy={
                "level1": {"code": category_data.get("id"), "name": category or None, "path": "zhineng"} if isinstance(category_data, dict) else None,
                "level2": None,
                "level3": None,
                "tags": _safe_tags(raw.get("commitment")),
            },
            location=location,
            country=country,
            business_unit=business_unit or None,
            recruitment_type=recruitment_type,
            employment_type=employment_type,
            description=description,
            requirements=requirements,
            source_url=f"{portal_base}#/job/{job_id}",
            updated_at=_parse_datetime(raw.get("updatedAt") or raw.get("publishedAt") or raw.get("openedAt")),
            raw_data=raw,
        )


class DeepSeekRecruitmentAdapter(MokaRecruitmentAdapter):
    source = "deepseek"
    company = "DeepSeek"
    PORTAL = "https://app.mokahr.com/social-recruitment/high-flyer/140576#/"
    search_urls = {"social": PORTAL}
    portals = {
        "social": [{"url": PORTAL, "org_id": "high-flyer", "site_id": 140576, "site": "social"}],
    }


class KimiRecruitmentAdapter(MokaRecruitmentAdapter):
    source = "kimi"
    company = "月之暗面"
    SOCIAL_PORTAL = "https://app.mokahr.com/apply/moonshot/148506#/jobs"
    CAMPUS_PORTAL = "https://app.mokahr.com/campus-recruitment/moonshot/148507#/"
    search_urls = {"social": SOCIAL_PORTAL, "campus": CAMPUS_PORTAL, "intern": CAMPUS_PORTAL}
    portals = {
        "social": [{"url": SOCIAL_PORTAL, "org_id": "moonshot", "site_id": 148506, "site": "social"}],
        "campus": [{"url": CAMPUS_PORTAL, "org_id": "moonshot", "site_id": 148507, "site": "campus", "commitment": "non_intern"}],
        "intern": [{"url": CAMPUS_PORTAL, "org_id": "moonshot", "site_id": 148507, "site": "campus", "commitment": "intern"}],
    }


class ZhipuRecruitmentAdapter(MokaRecruitmentAdapter):
    source = "zhipu"
    company = "智谱 AI"
    SOCIAL_PORTAL = "https://app.mokahr.com/social-recruitment/zphz/148983#/"
    CAMPUS_PORTAL = "https://app.mokahr.com/campus-recruitment/zphz/148984#/home"
    SOCIAL = {"url": SOCIAL_PORTAL, "org_id": "zphz", "site_id": 148983, "site": "social"}
    CAMPUS = {"url": CAMPUS_PORTAL, "org_id": "zphz", "site_id": 148984, "site": "campus"}
    search_urls = {"social": SOCIAL_PORTAL, "campus": CAMPUS_PORTAL, "intern": CAMPUS_PORTAL}
    portals = {
        "social": [{**SOCIAL, "commitment": "non_intern"}],
        "campus": [{**CAMPUS, "commitment": "non_intern"}],
        "intern": [{**SOCIAL, "commitment": "intern"}, {**CAMPUS, "commitment": "intern"}],
    }


def _minimax_is_intern(raw: Dict) -> bool:
    recruit_type = raw.get("recruit_type") or (raw.get("job_post_info") or {}).get("recruitment_type") or {}
    names = [recruit_type.get("name"), (recruit_type.get("parent") or {}).get("name")]
    return any("实习" in str(name or "") for name in names)


class MiniMaxRecruitmentAdapter(OfficialSearchPageAdapter):
    source = "minimax"
    company = "MiniMax"
    BASE_URL = "https://vrfi1sk8a0.jobs.feishu.cn"
    JOBS_URL = f"{BASE_URL}/api/v1/search/job/posts"
    TOKEN_URL = f"{BASE_URL}/api/v1/csrf/token/"
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36"
    PORTALS = {
        "social": [("index", "non_intern")],
        "campus": [("379481", "non_intern")],
        "intern": [("index", "intern"), ("379481", "intern")],
    }
    search_urls = {
        "social": f"{BASE_URL}/index/",
        "campus": f"{BASE_URL}/379481/",
        "intern": f"{BASE_URL}/379481/",
    }
    max_page_size = 100

    def __init__(self, sleep_interval: Optional[float] = None):
        super().__init__(sleep_interval)
        self._jobs_cache = {}

    def fetch_page(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        keyword: str = "",
        filters: Optional[Dict] = None,
        recruitment_type: str = "social",
        include_detail: bool = True,
    ) -> JobPage:
        del filters, include_detail
        size = self._page_size(page_size)
        jobs = self._load_jobs(recruitment_type)
        if keyword.strip():
            lowered = keyword.strip().lower()
            jobs = [job for job in jobs if lowered in f"{job.title} {job.category or ''} {job.description} {job.requirements}".lower()]
        start = (max(page, 1) - 1) * size
        return JobPage(
            items=jobs[start:start + size],
            page=page,
            page_size=size,
            total=len(jobs),
            has_more=start + size < len(jobs),
        )

    def _load_jobs(self, recruitment_type: str):
        if recruitment_type in self._jobs_cache:
            return self._jobs_cache[recruitment_type]
        unique = {}
        for portal, commitment in self.PORTALS.get(recruitment_type, []):
            for raw in self._fetch_portal(portal):
                is_intern = _minimax_is_intern(raw)
                if commitment == "intern" and not is_intern:
                    continue
                if commitment == "non_intern" and is_intern:
                    continue
                normalized = self._normalize_job({**raw, "_minimax_portal": portal}, recruitment_type)
                unique[normalized.source_job_id] = normalized
        self._jobs_cache[recruitment_type] = list(unique.values())
        return self._jobs_cache[recruitment_type]

    def _headers(self, portal: str, csrf_token: str = ""):
        headers = {
            "User-Agent": self.USER_AGENT,
            "Referer": f"{self.BASE_URL}/{portal}/",
            "website-path": portal,
            "Portal-Channel": "saas-career",
            "Portal-Platform": "pc",
            "Content-Type": "application/json",
        }
        if csrf_token:
            headers["x-csrf-token"] = csrf_token
        return headers

    def _fetch_portal(self, portal: str):
        self._request("GET", f"{self.BASE_URL}/{portal}/", headers=self._headers(portal))
        token_data = self._request("POST", self.TOKEN_URL, headers=self._headers(portal)).json()
        csrf_token = ((token_data.get("data") or {}).get("token") or "").strip()
        if token_data.get("code") != 0 or not csrf_token:
            raise ValueError(f"MiniMax CSRF token 获取失败：{token_data.get('message') or token_data.get('code')}")

        jobs = []
        limit = 50
        offset = 0
        while True:
            payload = {
                "keyword": "",
                "limit": limit,
                "offset": offset,
                "job_category_id_list": [],
                "tag_id_list": [],
                "location_code_list": [],
                "subject_id_list": [],
                "recruitment_id_list": [],
                "portal_type": 6,
                "job_function_id_list": [],
                "storefront_id_list": [],
                "portal_entrance": 1,
            }
            data = self._request("POST", self.JOBS_URL, json=payload, headers=self._headers(portal, csrf_token)).json()
            if data.get("code") != 0:
                raise ValueError(f"MiniMax 岗位接口失败：{data.get('message') or data.get('code')}")
            result = data.get("data") or {}
            batch = result.get("job_post_list") or []
            jobs.extend(batch)
            offset += len(batch)
            if not batch or offset >= int(result.get("count") or len(jobs)):
                return jobs

    def _normalize_job(self, raw: Dict, recruitment_type: str) -> JobPosting:
        category = raw.get("job_category") or {}
        chain = []
        node = category
        while isinstance(node, dict) and node and len(chain) < 3:
            chain.append(node)
            node = node.get("parent")
        chain.reverse()
        levels = [None, None, None]
        for index, item in enumerate(chain):
            levels[index] = {
                "code": item.get("id"),
                "name": item.get("name") or item.get("i18n_name"),
                "path": "job_category" + ".parent" * (len(chain) - index - 1),
            }
        cities = list(dict.fromkeys(
            str(item.get("name") or item.get("i18n_name"))
            for item in raw.get("city_list") or []
            if item.get("name") or item.get("i18n_name")
        ))
        recruit_type = raw.get("recruit_type") or {}
        job_id = str(raw.get("id") or "")
        portal = str(raw.get("_minimax_portal") or "index")
        job_function = raw.get("job_function") or {}
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(raw.get("title") or "").strip(),
            category=category.get("name") or category.get("i18n_name"),
            job_family=category.get("name") or category.get("i18n_name"),
            official_taxonomy={
                "level1": levels[0],
                "level2": levels[1],
                "level3": levels[2],
                "tags": _safe_tags([recruit_type, raw.get("job_subject")]),
            },
            location="、".join(cities) or None,
            country="中国",
            business_unit=job_function.get("name") or None,
            recruitment_type=recruitment_type,
            employment_type=_label(recruitment_type),
            description=str(raw.get("description") or "").strip(),
            requirements=str(raw.get("requirement") or "").strip(),
            source_url=f"{self.BASE_URL}/{portal}/position/{job_id}/detail",
            updated_at=_parse_datetime(raw.get("publish_time")),
            raw_data=raw,
        )
