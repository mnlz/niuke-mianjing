import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from niuke_mianjing_backend.repositories.base import BaseRepository


class JobRepository(BaseRepository):
    async def init_table(self):
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS `scheduled_jobs` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
                `job_id` VARCHAR(100) NOT NULL COMMENT 'APScheduler任务ID',
                `name` VARCHAR(200) COMMENT '任务名称',
                `posts` JSON COMMENT '要爬取的方向列表',
                `schedule_type` VARCHAR(20) COMMENT '调度类型：cron/interval',
                `schedule` VARCHAR(100) COMMENT '调度规则',
                `max_pages` INT DEFAULT 15 COMMENT '最大爬取页数',
                `next_run_time` DATETIME COMMENT '下次执行时间',
                `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态：active/inactive',
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY `uk_job_id` (`job_id`),
                KEY `idx_status` (`status`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定时任务表'
            """
        )
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS `scheduled_job_runs` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `job_id` VARCHAR(100) NOT NULL,
                `started_at` DATETIME NOT NULL,
                `finished_at` DATETIME NULL,
                `duration_seconds` INT NULL,
                `status` VARCHAR(20) NOT NULL DEFAULT 'running',
                `result_json` JSON NULL,
                `error_message` TEXT NULL,
                KEY `idx_job_runs_job_started` (`job_id`, `started_at`),
                KEY `idx_job_runs_status` (`status`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )

    async def add_job(
        self,
        job_id: str,
        name: str,
        posts: list,
        schedule_type: str,
        schedule: str,
        max_pages: int = 15,
        next_run_time: datetime = None,
    ):
        posts_json = json.dumps(posts, ensure_ascii=False)
        await self._execute(
            """
            INSERT INTO scheduled_jobs (job_id, name, posts, schedule_type, schedule, max_pages, next_run_time, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')
            """,
            (job_id, name, posts_json, schedule_type, schedule, max_pages, next_run_time),
        )

    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        rows = await self._fetch_all(
            """
            SELECT job_id, name, posts, schedule_type, schedule, max_pages, next_run_time, status
            FROM scheduled_jobs ORDER BY created_at DESC
            """
        )
        jobs = []
        for row in rows:
            jobs.append(
                {
                    "job_id": row[0],
                    "name": row[1],
                    "posts": json.loads(row[2]) if row[2] else [],
                    "schedule_type": row[3],
                    "schedule": row[4],
                    "max_pages": row[5],
                    "next_run_time": row[6].isoformat() if row[6] else None,
                    "status": row[7],
                }
            )
        return jobs

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        row = await self._fetch_one(
            """
            SELECT job_id, name, posts, schedule_type, schedule, max_pages, next_run_time, status
            FROM scheduled_jobs WHERE job_id = %s
            """,
            (job_id,),
        )
        if row:
            return {
                "job_id": row[0],
                "name": row[1],
                "posts": json.loads(row[2]) if row[2] else [],
                "schedule_type": row[3],
                "schedule": row[4],
                "max_pages": row[5],
                "next_run_time": row[6].isoformat() if row[6] else None,
                "status": row[7],
            }
        return None

    async def update_job_next_run(self, job_id: str, next_run_time: datetime):
        await self._execute(
            """
            UPDATE scheduled_jobs SET next_run_time = %s, updated_at = %s WHERE job_id = %s
            """,
            (next_run_time, datetime.now(), job_id),
        )

    async def delete_job(self, job_id: str):
        await self._execute("DELETE FROM scheduled_jobs WHERE job_id = %s", (job_id,))

    async def update_job_status(self, job_id: str, status: str, next_run_time: datetime = None):
        await self._execute(
            """
            UPDATE scheduled_jobs
            SET status = %s, next_run_time = %s, updated_at = %s
            WHERE job_id = %s
            """,
            (status, next_run_time, datetime.now(), job_id),
        )

    async def create_run(self, job_id: str, started_at: datetime) -> int:
        return await self._execute_lastrowid(
            """
            INSERT INTO scheduled_job_runs (job_id, started_at, status)
            VALUES (%s, %s, 'running')
            """,
            (job_id, started_at),
        )

    async def finish_run(
        self,
        run_id: int,
        finished_at: datetime,
        duration_seconds: int,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ):
        await self._execute(
            """
            UPDATE scheduled_job_runs
            SET finished_at = %s,
                duration_seconds = %s,
                status = %s,
                result_json = %s,
                error_message = %s
            WHERE id = %s
            """,
            (
                finished_at,
                duration_seconds,
                status,
                json.dumps(result, ensure_ascii=False) if result is not None else None,
                error_message,
                run_id,
            ),
        )

    async def get_recent_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = await self._fetch_all(
            """
            SELECT id, job_id, started_at, finished_at, duration_seconds, status, result_json, error_message
            FROM scheduled_job_runs
            ORDER BY started_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [
            {
                "id": row[0],
                "job_id": row[1],
                "started_at": row[2].isoformat() if row[2] else None,
                "finished_at": row[3].isoformat() if row[3] else None,
                "duration_seconds": row[4],
                "status": row[5],
                "result": json.loads(row[6]) if isinstance(row[6], str) else row[6],
                "error_message": row[7],
            }
            for row in rows
        ]
