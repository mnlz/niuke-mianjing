import time
from typing import Dict, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from niuke_mianjing_backend.repositories.job_repo import JobRepository
from niuke_mianjing_backend.schemas.ws import WSMessageType
from niuke_mianjing_backend.services.crawl_service import CrawlService
from niuke_mianjing_backend.services.event_bus import EventBus


class ScheduleService:
    def __init__(self, crawl_service: CrawlService):
        self.crawl_service = crawl_service
        self.job_repo = JobRepository()
        self.event_bus = EventBus()
        self.scheduler = AsyncIOScheduler()

    async def init_table(self):
        await self.job_repo.init_table()

    async def create_cron_job(self, posts: List[str], cron_expr: str, max_pages: int = 15) -> Dict:
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError("Cron 表达式格式错误，应为：分钟 小时 日 月 周")

        minute, hour, day, month, day_of_week = parts
        job_id = f"cron_{int(time.time())}"

        job = self.scheduler.add_job(
            self.crawl_service.crawl_all,
            trigger=CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week),
            args=[posts, max_pages],
            id=job_id,
            name=f"爬取任务: {','.join(posts)}",
        )

        await self.job_repo.add_job(
            job_id=job.id,
            name=job.name,
            posts=posts,
            schedule_type="cron",
            schedule=cron_expr,
            max_pages=max_pages,
            next_run_time=job.next_run_time.replace(tzinfo=None) if job.next_run_time else None,
        )

        await self.event_bus.publish(
            WSMessageType.JOB_STATUS_CHANGE,
            {"job_id": job_id, "action": "created", "schedule_type": "cron"},
            f"定时任务创建成功：{cron_expr}",
        )

        return {"job_id": job_id, "name": job.name, "next_run_time": str(job.next_run_time)}

    async def create_interval_job(self, posts: List[str], hours: int = 0, minutes: int = 0, max_pages: int = 15) -> Dict:
        if hours == 0 and minutes == 0:
            raise ValueError("必须指定至少一个时间间隔")

        job_id = f"interval_{int(time.time())}"

        job = self.scheduler.add_job(
            self.crawl_service.crawl_all,
            trigger="interval",
            hours=hours,
            minutes=minutes,
            args=[posts, max_pages],
            id=job_id,
            name=f"定时爬取: {','.join(posts)}",
        )

        await self.job_repo.add_job(
            job_id=job.id,
            name=job.name,
            posts=posts,
            schedule_type="interval",
            schedule=f"{hours}h {minutes}m",
            max_pages=max_pages,
            next_run_time=job.next_run_time.replace(tzinfo=None) if job.next_run_time else None,
        )

        await self.event_bus.publish(
            WSMessageType.JOB_STATUS_CHANGE,
            {"job_id": job_id, "action": "created", "schedule_type": "interval"},
            f"间隔任务创建成功：每 {hours} 小时 {minutes} 分钟",
        )

        return {"job_id": job_id, "name": job.name, "next_run_time": str(job.next_run_time)}

    async def list_jobs(self) -> List[Dict]:
        return await self.job_repo.get_all_jobs()

    async def delete_job(self, job_id: str):
        self.scheduler.remove_job(job_id)
        await self.job_repo.delete_job(job_id)

        await self.event_bus.publish(
            WSMessageType.JOB_STATUS_CHANGE,
            {"job_id": job_id, "action": "deleted"},
            f"定时任务已删除：{job_id}",
        )

    def start(self):
        self.scheduler.start()
        print("定时任务调度器已启动")

    def stop(self):
        self.scheduler.shutdown()
        print("定时任务调度器已停止")
