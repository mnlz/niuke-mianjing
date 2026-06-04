import json
from datetime import datetime
import mysql.connector

from niuke_mianjing_backend.config import get_db_config


class ScheduledJobManager:
    def __init__(self, db_config=None):
        self.db_config = db_config or get_db_config()
        self.db = mysql.connector.connect(**self.db_config)
        self._init_table()

    def _init_table(self):
        cur = self.db.cursor()
        cur.execute("""
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
        """)
        self.db.commit()
        cur.close()

    def add_job(self, job_id: str, name: str, posts: list, 
               schedule_type: str, schedule: str, max_pages: int = 15):
        cur = self.db.cursor()
        posts_json = json.dumps(posts, ensure_ascii=False)
        
        cur.execute("""
            INSERT INTO scheduled_jobs (job_id, name, posts, schedule_type, schedule, max_pages, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'active')
        """, (job_id, name, posts_json, schedule_type, schedule, max_pages))
        
        self.db.commit()
        cur.close()

    def get_all_jobs(self):
        cur = self.db.cursor()
        cur.execute("""
            SELECT job_id, name, posts, schedule_type, schedule, max_pages, next_run_time, status
            FROM scheduled_jobs
            WHERE status = 'active'
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        cur.close()
        
        jobs = []
        for row in rows:
            jobs.append({
                "job_id": row[0],
                "name": row[1],
                "posts": json.loads(row[2]) if row[2] else [],
                "schedule_type": row[3],
                "schedule": row[4],
                "max_pages": row[5],
                "next_run_time": row[6].isoformat() if row[6] else None
            })
        
        return jobs

    def get_job(self, job_id: str):
        cur = self.db.cursor()
        cur.execute("""
            SELECT job_id, name, posts, schedule_type, schedule, max_pages, next_run_time, status
            FROM scheduled_jobs
            WHERE job_id = %s
        """, (job_id,))
        row = cur.fetchone()
        cur.close()
        
        if row:
            return {
                "job_id": row[0],
                "name": row[1],
                "posts": json.loads(row[2]) if row[2] else [],
                "schedule_type": row[3],
                "schedule": row[4],
                "max_pages": row[5],
                "next_run_time": row[6].isoformat() if row[6] else None
            }
        return None

    def update_job_next_run(self, job_id: str, next_run_time: datetime):
        cur = self.db.cursor()
        cur.execute("""
            UPDATE scheduled_jobs 
            SET next_run_time = %s, updated_at = %s
            WHERE job_id = %s
        """, (next_run_time, datetime.now(), job_id))
        self.db.commit()
        cur.close()

    def delete_job(self, job_id: str):
        cur = self.db.cursor()
        cur.execute("DELETE FROM scheduled_jobs WHERE job_id = %s", (job_id,))
        self.db.commit()
        cur.close()

    def close(self):
        self.db.close()
