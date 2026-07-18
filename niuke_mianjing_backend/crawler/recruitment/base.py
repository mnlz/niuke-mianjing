import time
from abc import ABC, abstractmethod
from typing import Dict, Iterator, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from niuke_mianjing_backend.config import get_proxy_config, settings

from .models import JobPage, JobPosting


class RecruitmentAdapter(ABC):
    source: str
    company: str
    default_page_size = 20
    max_page_size = 100

    def __init__(self, sleep_interval: Optional[float] = None):
        self.sleep_interval = float(settings.SLEEP_INTERVAL if sleep_interval is None else sleep_interval)
        self.proxies = get_proxy_config()
        self.session = requests.Session()
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST"}),
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    @abstractmethod
    def fetch_page(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        keyword: str = "",
        filters: Optional[Dict] = None,
        recruitment_type: str = "campus",
        include_detail: bool = True,
    ) -> JobPage:
        raise NotImplementedError

    def iter_jobs(
        self,
        keyword: str = "",
        filters: Optional[Dict] = None,
        max_pages: Optional[int] = None,
        page_size: Optional[int] = None,
        recruitment_type: str = "campus",
        include_detail: bool = True,
    ) -> Iterator[JobPosting]:
        current_page = 1
        while max_pages is None or current_page <= max_pages:
            result = self.fetch_page(
                page=current_page,
                page_size=page_size,
                keyword=keyword,
                filters=filters,
                recruitment_type=recruitment_type,
                include_detail=include_detail,
            )
            yield from result.items
            if not result.has_more:
                return
            current_page += 1
            if self.sleep_interval > 0:
                time.sleep(self.sleep_interval)

    def fetch_all(
        self,
        keyword: str = "",
        filters: Optional[Dict] = None,
        max_pages: Optional[int] = None,
        page_size: Optional[int] = None,
        recruitment_type: str = "campus",
        include_detail: bool = True,
    ):
        return list(self.iter_jobs(keyword, filters, max_pages, page_size, recruitment_type, include_detail))

    def _page_size(self, page_size: Optional[int]) -> int:
        return min(max(int(page_size or self.default_page_size), 1), self.max_page_size)

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", (10, 40))
        kwargs.setdefault("proxies", self.proxies)
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response
