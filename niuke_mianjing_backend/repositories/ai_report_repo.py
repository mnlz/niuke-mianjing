import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from niuke_mianjing_backend.repositories.base import BaseRepository


class AIReportRepository(BaseRepository):
    async def init_table(self):
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS `ai_analysis_reports` (
                `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
                `user_id` BIGINT NOT NULL,
                `report_code` VARCHAR(64) NOT NULL,
                `title` VARCHAR(255) NOT NULL,
                `report_type` VARCHAR(32) NOT NULL,
                `company` VARCHAR(255) NULL,
                `track` VARCHAR(64) NULL,
                `track_name` VARCHAR(128) NULL,
                `recruitment_type` VARCHAR(32) NULL,
                `content` MEDIUMTEXT NOT NULL,
                `model` VARCHAR(128) NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY `uk_ai_report_code` (`report_code`),
                KEY `idx_ai_report_user_created` (`user_id`, `created_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )

    @staticmethod
    def _row(row) -> Dict[str, Any]:
        return {
            "report_code": row[0], "title": row[1], "report_type": row[2], "company": row[3],
            "track": row[4], "track_name": row[5], "recruitment_type": row[6], "content": row[7],
            "model": row[8], "created_at": row[9].isoformat() if row[9] else None,
            "updated_at": row[10].isoformat() if row[10] else None,
        }

    async def save(self, user_id: int, report: Dict[str, Any]) -> Dict[str, Any]:
        code = report.get("report_code") or f"RPT-{datetime.now():%Y%m%d}-{secrets.token_hex(3).upper()}"
        await self._execute(
            """
            INSERT INTO ai_analysis_reports
                (user_id, report_code, title, report_type, company, track, track_name, recruitment_type, content, model)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, code, report["title"], report["report_type"], report.get("company"), report.get("track"),
             report.get("track_name"), report.get("recruitment_type"), report["content"], report.get("model")),
        )
        saved = await self.get_by_code(user_id, code)
        if not saved:
            raise RuntimeError("报告保存失败")
        return saved

    async def list_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        rows = await self._fetch_all(
            "SELECT report_code, title, report_type, company, track, track_name, recruitment_type, content, model, created_at, updated_at FROM ai_analysis_reports WHERE user_id = %s ORDER BY created_at DESC LIMIT 100",
            (user_id,),
        )
        return [self._row(row) for row in rows]

    async def get_by_code(self, user_id: int, report_code: str) -> Optional[Dict[str, Any]]:
        row = await self._fetch_one(
            "SELECT report_code, title, report_type, company, track, track_name, recruitment_type, content, model, created_at, updated_at FROM ai_analysis_reports WHERE user_id = %s AND report_code = %s",
            (user_id, report_code),
        )
        return self._row(row) if row else None

    async def delete_by_code(self, user_id: int, report_code: str) -> bool:
        return bool(await self._execute(
            "DELETE FROM ai_analysis_reports WHERE user_id = %s AND report_code = %s",
            (user_id, report_code),
        ))
