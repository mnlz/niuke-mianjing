from datetime import datetime
from typing import Optional, List, Dict, Any

from niuke_mianjing_backend.repositories.base import BaseRepository


class CrawlLogRepository(BaseRepository):
    async def init_table(self):
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS `crawl_log` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
                `post` VARCHAR(50) NOT NULL COMMENT '职位方向',
                `start_time` DATETIME COMMENT '开始时间',
                `end_time` DATETIME COMMENT '结束时间',
                `total_pages` INT COMMENT '总页数',
                `new_records` INT DEFAULT 0 COMMENT '新增记录数',
                `updated_records` INT DEFAULT 0 COMMENT '更新记录数',
                `status` VARCHAR(20) COMMENT '状态：success/failed',
                `error_message` TEXT COMMENT '错误信息',
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='爬取日志表'
            """
        )

    async def get_logs(
        self,
        post: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        conditions = []
        params: list = []

        if post:
            conditions.append("post = %s")
            params.append(post)
        if status:
            conditions.append("status = %s")
            params.append(status)
        if start_date:
            conditions.append("DATE(start_time) >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("DATE(start_time) <= %s")
            params.append(end_date)

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        params.append(limit)
        rows = await self._fetch_all(
            f"""
            SELECT id, post, start_time, end_time, total_pages,
                   new_records, updated_records, status, error_message
            FROM crawl_log {where}
            ORDER BY start_time DESC LIMIT %s
            """,
            tuple(params),
        )

        return [
            {
                "id": row[0],
                "post": row[1],
                "start_time": row[2].isoformat() if row[2] else None,
                "end_time": row[3].isoformat() if row[3] else None,
                "total_pages": row[4],
                "new_records": row[5],
                "updated_records": row[6],
                "status": row[7],
                "error_message": row[8],
            }
            for row in rows
        ]

    async def add_log(
        self,
        post: str,
        start_time: datetime,
        end_time: datetime,
        total_pages: int,
        new_records: int,
        updated_records: int,
        status: str,
        error_message: str = None,
    ):
        await self._execute(
            """
            INSERT INTO crawl_log (post, start_time, end_time, total_pages,
                               new_records, updated_records, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (post, start_time, end_time, total_pages, new_records, updated_records, status, error_message),
        )
