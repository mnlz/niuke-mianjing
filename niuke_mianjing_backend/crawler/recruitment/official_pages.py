import hashlib
import hmac
import time
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import quote_plus

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
            job_family=raw.get("categoryType"),
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
            raw = self.fetch_detail(str(item.get("jobUnionId") or item.get("jobId") or "")) if include_detail else item
            items.append(self._normalize_job(raw or item, recruitment_type))
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
            job_family=raw.get("projectType") or raw.get("postType"),
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
            job_family=raw.get("jobDirection"),
            location=_normalize_city(city),
            country="中国",
            business_unit=raw.get("positionDept") or raw.get("reportLeaderName"),
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
        items = [self._normalize_job(item, recruitment_type) for item in result.get("list") or []]
        total = int(result.get("total") or len(items))
        return JobPage(items=items, page=page, page_size=size, total=total, has_more=page * size < total and bool(items))

    def _normalize_job(self, raw: Dict, recruitment_type: str) -> JobPosting:
        job_id = str(raw.get("id") or raw.get("code") or "")
        return JobPosting(
            source=self.source,
            source_job_id=job_id,
            company=self.company,
            title=str(raw.get("name") or "").strip(),
            category=raw.get("positionCategoryName") or raw.get("positionCategoryCode"),
            job_family=raw.get("positionClassName") or raw.get("positionCategoryName"),
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
            raw = self.fetch_detail(item) if include_detail else item
            items.append(self._normalize_job(raw or item, recruitment_type))
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
            category=raw.get("jobFamilyName") or raw.get("jobSubcategory"),
            job_family=raw.get("jobFamilyName") or raw.get("jobFamClsCode"),
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
