import re
from datetime import datetime
from typing import Dict, List
from uuid import uuid4

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

    def _add_scheduler_job(
        self,
        job_id: str,
        posts: List[str],
        schedule_type: str,
        schedule: str,
        max_pages: int,
        paused: bool = False,
    ):
        kwargs = {
            "func": self._execute_job,
            "args": [job_id, posts, max_pages],
            "id": job_id,
            "name": f"定时爬取: {','.join(posts)}",
            "replace_existing": True,
            "coalesce": True,
            "max_instances": 1,
        }
        if schedule_type == "cron":
            parts = schedule.split()
            if len(parts) != 5:
                raise ValueError("Cron 表达式应为：分钟 小时 日期 月份 星期")
            minute, hour, day, month, day_of_week = parts
            job = self.scheduler.add_job(
                trigger=CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week),
                **kwargs,
            )
        else:
            hours = int(re.search(r"(\d+)\s*h", schedule).group(1)) if re.search(r"(\d+)\s*h", schedule) else 0
            minutes = int(re.search(r"(\d+)\s*m", schedule).group(1)) if re.search(r"(\d+)\s*m", schedule) else 0
            if hours == 0 and minutes == 0:
                raise ValueError("固定间隔不能为 0")
            job = self.scheduler.add_job(trigger="interval", hours=hours, minutes=minutes, **kwargs)
        if paused:
            job.pause()
        return job

    async def restore_jobs(self):
        for item in await self.job_repo.get_all_jobs():
            if item.get("status") not in {"active", "paused"}:
                continue
            try:
                self._add_scheduler_job(
                    job_id=item["job_id"],
                    posts=item["posts"],
                    schedule_type=item["schedule_type"],
                    schedule=item["schedule"],
                    max_pages=item["max_pages"],
                    paused=item.get("status") == "paused",
                )
            except ValueError:
                await self.job_repo.update_job_status(item["job_id"], "invalid")

    async def _execute_job(self, job_id: str, posts: List[str], max_pages: int):
        started_at = datetime.now()
        run_id = await self.job_repo.create_run(job_id, started_at)
        try:
            result = await self.crawl_service.crawl_all(posts, max_pages)
            finished_at = datetime.now()
            await self.job_repo.finish_run(
                run_id,
                finished_at,
                int((finished_at - started_at).total_seconds()),
                "success",
                {"summary": result},
            )
        except Exception as exc:
            finished_at = datetime.now()
            await self.job_repo.finish_run(
                run_id,
                finished_at,
                int((finished_at - started_at).total_seconds()),
                "failed",
                error_message=str(exc),
            )
            raise
        finally:
            job = self.scheduler.get_job(job_id)
            await self.job_repo.update_job_next_run(
                job_id,
                job.next_run_time.replace(tzinfo=None) if job and job.next_run_time else None,
            )

    async def create_cron_job(self, posts: List[str], cron_expr: str, max_pages: int = 15) -> Dict:
        job_id = f"cron_{uuid4().hex}"
        job = self._add_scheduler_job(job_id, posts, "cron", cron_expr, max_pages)
        await self.job_repo.add_job(
            job.id,
            job.name,
            posts,
            "cron",
            cron_expr,
            max_pages,
            job.next_run_time.replace(tzinfo=None) if job.next_run_time else None,
        )
        await self.event_bus.publish(
            WSMessageType.JOB_STATUS_CHANGE,
            {"job_id": job_id, "action": "created", "schedule_type": "cron"},
            f"定时任务创建成功：{cron_expr}",
        )
        return {"job_id": job_id, "name": job.name, "next_run_time": str(job.next_run_time)}

    async def create_interval_job(self, posts: List[str], hours: int = 0, minutes: int = 0, max_pages: int = 15) -> Dict:
        schedule = f"{hours}h {minutes}m"
        job_id = f"interval_{uuid4().hex}"
        job = self._add_scheduler_job(job_id, posts, "interval", schedule, max_pages)
        await self.job_repo.add_job(
            job.id,
            job.name,
            posts,
            "interval",
            schedule,
            max_pages,
            job.next_run_time.replace(tzinfo=None) if job.next_run_time else None,
        )
        await self.event_bus.publish(
            WSMessageType.JOB_STATUS_CHANGE,
            {"job_id": job_id, "action": "created", "schedule_type": "interval"},
            f"间隔任务创建成功：每 {hours} 小时 {minutes} 分钟",
        )
        return {"job_id": job_id, "name": job.name, "next_run_time": str(job.next_run_time)}

    async def list_jobs(self) -> List[Dict]:
        jobs = await self.job_repo.get_all_jobs()
        for item in jobs:
            scheduled = self.scheduler.get_job(item["job_id"])
            item["next_run_time"] = (
                scheduled.next_run_time.replace(tzinfo=None).isoformat()
                if scheduled and scheduled.next_run_time
                else None
            )
        return jobs

    async def list_runs(self, limit: int = 50) -> List[Dict]:
        return await self.job_repo.get_recent_runs(limit)

    async def pause_job(self, job_id: str):
        self.scheduler.pause_job(job_id)
        await self.job_repo.update_job_status(job_id, "paused")

    async def resume_job(self, job_id: str):
        self.scheduler.resume_job(job_id)
        job = self.scheduler.get_job(job_id)
        await self.job_repo.update_job_status(
            job_id,
            "active",
            job.next_run_time.replace(tzinfo=None) if job and job.next_run_time else None,
        )

    async def run_job_now(self, job_id: str):
        item = await self.job_repo.get_job(job_id)
        if not item:
            raise ValueError("定时任务不存在")
        await self._execute_job(job_id, item["posts"], item["max_pages"])

    async def delete_job(self, job_id: str):
        job = self.scheduler.get_job(job_id)
        if job:
            self.scheduler.remove_job(job_id)
        await self.job_repo.delete_job(job_id)

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
