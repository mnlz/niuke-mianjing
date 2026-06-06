from functools import lru_cache

from niuke_mianjing_backend.config import settings
from niuke_mianjing_backend.services.crawl_service import CrawlService
from niuke_mianjing_backend.services.schedule_service import ScheduleService
from niuke_mianjing_backend.services.log_service import LogService
from niuke_mianjing_backend.services.event_bus import EventBus
from niuke_mianjing_backend.services.wechat_service import WeChatService
from niuke_mianjing_backend.services.review_service import ReviewService


@lru_cache()
def get_event_bus() -> EventBus:
    return EventBus()


@lru_cache()
def get_crawl_service() -> CrawlService:
    return CrawlService(settings.FEISHU_WEBHOOK)


@lru_cache()
def get_schedule_service() -> ScheduleService:
    return ScheduleService(get_crawl_service())


@lru_cache()
def get_log_service() -> LogService:
    return LogService()


@lru_cache()
def get_wechat_service() -> WeChatService:
    return WeChatService()


@lru_cache()
def get_review_service() -> ReviewService:
    return ReviewService()
