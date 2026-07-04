from typing import Optional, Dict, List
from niuke_mianjing_backend.repositories.niuke_repo import NiukeRepository
from niuke_mianjing_backend.repositories.crawl_log_repo import CrawlLogRepository


class LogService:
    def __init__(self):
        self.niuke_repo = NiukeRepository()
        self.log_repo = CrawlLogRepository()

    async def init_table(self):
        await self.log_repo.init_table()

    async def get_crawl_logs(
        self,
        post: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        return await self.log_repo.get_logs(post, status, start_date, end_date, limit)

    async def get_stats(self) -> Dict:
        stats_data = await self.niuke_repo.get_stats()
        return {
            "total_records": stats_data["total_records"],
            "active_records": stats_data["active_records"],
            "post_stats": stats_data["post_stats"],
        }

    async def get_niuke_data(
        self,
        post: Optional[str] = None,
        company: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict:
        return await self.niuke_repo.get_data(post, company, limit, offset)

    async def get_niuke_record(self, record_id: int) -> Optional[Dict]:
        return await self.niuke_repo.get_by_id(record_id)

    async def get_filters(self) -> Dict:
        return await self.niuke_repo.get_filters()
