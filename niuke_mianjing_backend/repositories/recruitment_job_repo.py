import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from niuke_mianjing_backend.repositories.base import BaseRepository


class RecruitmentJobRepository(BaseRepository):
    async def init_table(self):
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS `official_recruitment_jobs` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `source` VARCHAR(40) NOT NULL,
                `source_job_id` VARCHAR(120) NOT NULL,
                `company` VARCHAR(80) NOT NULL,
                `title` VARCHAR(300) NOT NULL,
                `category` VARCHAR(120) NULL,
                `job_family` VARCHAR(120) NULL,
                `official_taxonomy` JSON NULL,
                `role_group` VARCHAR(40) NULL,
                `role_family` VARCHAR(40) NULL,
                `specialties` JSON NULL,
                `business_domains` JSON NULL,
                `tech_stack` JSON NULL,
                `classification_meta` JSON NULL,
                `inferred_track` VARCHAR(40) NULL,
                `inferred_track_name` VARCHAR(80) NULL,
                `display_category` VARCHAR(80) NULL,
                `location` VARCHAR(500) NULL,
                `country` VARCHAR(80) NULL,
                `business_unit` VARCHAR(500) NULL,
                `product` VARCHAR(200) NULL,
                `recruitment_type` VARCHAR(30) NOT NULL DEFAULT 'campus',
                `employment_type` VARCHAR(80) NULL,
                `experience` VARCHAR(120) NULL,
                `description` MEDIUMTEXT NULL,
                `requirements` MEDIUMTEXT NULL,
                `highlights` MEDIUMTEXT NULL,
                `preferred_qualifications` MEDIUMTEXT NULL,
                `source_url` VARCHAR(1000) NOT NULL,
                `detail_status` VARCHAR(30) NOT NULL DEFAULT 'unknown',
                `raw_json` JSON NULL,
                `refresh_version` VARCHAR(80) NULL,
                `refresh_started_at` DATETIME NULL,
                `is_latest` TINYINT NOT NULL DEFAULT 1,
                `updated_at` DATETIME NULL,
                `crawled_at` DATETIME NULL,
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                `synced_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY `uk_official_job` (`source`, `source_job_id`, `recruitment_type`),
                KEY `idx_source_type` (`source`, `recruitment_type`),
                KEY `idx_role_family` (`role_family`),
                KEY `idx_track` (`inferred_track`),
                KEY `idx_refresh_version` (`refresh_version`),
                KEY `idx_latest_source_type` (`is_latest`, `source`, `recruitment_type`),
                KEY `idx_company` (`company`),
                FULLTEXT KEY `ft_title_desc_req` (`title`, `description`, `requirements`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='官方招聘岗位表'
            """
        )
        await self._ensure_column("official_recruitment_jobs", "refresh_version", "`refresh_version` VARCHAR(80) NULL")
        await self._ensure_column("official_recruitment_jobs", "refresh_started_at", "`refresh_started_at` DATETIME NULL")
        await self._ensure_column("official_recruitment_jobs", "is_latest", "`is_latest` TINYINT NOT NULL DEFAULT 1")
        await self._ensure_column("official_recruitment_jobs", "official_taxonomy", "`official_taxonomy` JSON NULL")
        await self._ensure_column("official_recruitment_jobs", "role_group", "`role_group` VARCHAR(40) NULL")
        await self._ensure_column("official_recruitment_jobs", "role_family", "`role_family` VARCHAR(40) NULL")
        await self._ensure_column("official_recruitment_jobs", "specialties", "`specialties` JSON NULL")
        await self._ensure_column("official_recruitment_jobs", "business_domains", "`business_domains` JSON NULL")
        await self._ensure_column("official_recruitment_jobs", "tech_stack", "`tech_stack` JSON NULL")
        await self._ensure_column("official_recruitment_jobs", "classification_meta", "`classification_meta` JSON NULL")
        await self._ensure_index("official_recruitment_jobs", "idx_role_family", "KEY `idx_role_family` (`role_family`)")
        await self._ensure_index("official_recruitment_jobs", "idx_refresh_version", "KEY `idx_refresh_version` (`refresh_version`)")
        await self._ensure_index("official_recruitment_jobs", "idx_latest_source_type", "KEY `idx_latest_source_type` (`is_latest`, `source`, `recruitment_type`)")
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS `official_recruitment_refresh_runs` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `refresh_version` VARCHAR(80) NOT NULL,
                `source` VARCHAR(40) NOT NULL,
                `recruitment_type` VARCHAR(30) NOT NULL,
                `status` VARCHAR(30) NOT NULL,
                `job_count` INT NOT NULL DEFAULT 0,
                `error_message` TEXT NULL,
                `quality_json` JSON NULL,
                `started_at` DATETIME NOT NULL,
                `finished_at` DATETIME NULL,
                UNIQUE KEY `uk_refresh_run` (`refresh_version`, `source`, `recruitment_type`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='官方招聘岗位刷新记录'
            """
        )
        await self._ensure_column("official_recruitment_refresh_runs", "quality_json", "`quality_json` JSON NULL")

    async def upsert_many(
        self,
        jobs: List[Dict[str, Any]],
        refresh_version: Optional[str] = None,
        refresh_started_at: Optional[datetime] = None,
    ) -> int:
        if not jobs:
            return 0
        params = [self._to_row(job, refresh_version, refresh_started_at) for job in jobs]
        return await self._execute_many(
            """
            INSERT INTO official_recruitment_jobs (
                source, source_job_id, company, title, category, job_family,
                official_taxonomy, role_group, role_family, specialties,
                business_domains, tech_stack, classification_meta,
                inferred_track, inferred_track_name, display_category,
                location, country, business_unit, product, recruitment_type,
                employment_type, experience, description, requirements,
                highlights, preferred_qualifications, source_url, detail_status,
                raw_json, refresh_version, refresh_started_at, is_latest,
                updated_at, crawled_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
            ON DUPLICATE KEY UPDATE
                company = VALUES(company),
                title = VALUES(title),
                category = VALUES(category),
                job_family = VALUES(job_family),
                official_taxonomy = VALUES(official_taxonomy),
                role_group = VALUES(role_group),
                role_family = VALUES(role_family),
                specialties = VALUES(specialties),
                business_domains = VALUES(business_domains),
                tech_stack = VALUES(tech_stack),
                classification_meta = VALUES(classification_meta),
                inferred_track = VALUES(inferred_track),
                inferred_track_name = VALUES(inferred_track_name),
                display_category = VALUES(display_category),
                location = VALUES(location),
                country = VALUES(country),
                business_unit = VALUES(business_unit),
                product = VALUES(product),
                employment_type = VALUES(employment_type),
                experience = VALUES(experience),
                description = VALUES(description),
                requirements = VALUES(requirements),
                highlights = VALUES(highlights),
                preferred_qualifications = VALUES(preferred_qualifications),
                source_url = VALUES(source_url),
                detail_status = VALUES(detail_status),
                raw_json = VALUES(raw_json),
                refresh_version = VALUES(refresh_version),
                refresh_started_at = VALUES(refresh_started_at),
                is_latest = VALUES(is_latest),
                updated_at = VALUES(updated_at),
                crawled_at = VALUES(crawled_at),
                synced_at = CURRENT_TIMESTAMP
            """,
            params,
        )

    async def mark_latest_version(self, source: str, recruitment_type: str, refresh_version: str) -> int:
        return await self._execute(
            """
            UPDATE official_recruitment_jobs
            SET is_latest = IF(refresh_version = %s, 1, 0)
            WHERE source = %s AND recruitment_type = %s
            """,
            (refresh_version, source, recruitment_type),
        )

    async def latest_job_count(self, source: str, recruitment_type: str) -> int:
        row = await self._fetch_one(
            "SELECT COUNT(*) FROM official_recruitment_jobs WHERE source = %s AND recruitment_type = %s AND is_latest = 1",
            (source, recruitment_type),
        )
        return int(row[0] or 0) if row else 0

    async def latest_refresh_quality(self, source: str, recruitment_type: str) -> Dict[str, Any]:
        row = await self._fetch_one(
            """
            SELECT quality_json
            FROM official_recruitment_refresh_runs
            WHERE source = %s AND recruitment_type = %s AND status = 'success'
            ORDER BY finished_at DESC, id DESC
            LIMIT 1
            """,
            (source, recruitment_type),
        )
        return self._json_value(row[0], {}) if row else {}

    async def list_latest_jobs(self, source: str, recruitment_type: str) -> List[Dict[str, Any]]:
        rows = await self._fetch_all(
            """
            SELECT
                source, source_job_id, company, title, category, job_family,
                official_taxonomy, role_group, role_family, specialties,
                business_domains, tech_stack, classification_meta,
                inferred_track, inferred_track_name, display_category,
                location, country, business_unit, product, recruitment_type,
                employment_type, experience, description, requirements,
                highlights, preferred_qualifications, source_url, detail_status,
                refresh_version, refresh_started_at, updated_at, crawled_at, synced_at
            FROM official_recruitment_jobs
            WHERE source = %s AND recruitment_type = %s AND is_latest = 1
            ORDER BY COALESCE(updated_at, crawled_at, synced_at) DESC, id DESC
            """,
            (source, recruitment_type),
        )
        return [self._row_to_job(row) for row in rows]

    async def get_latest_job(self, source: str, recruitment_type: str, source_job_id: str) -> Optional[Dict[str, Any]]:
        row = await self._fetch_one(
            """
            SELECT
                source, source_job_id, company, title, category, job_family,
                official_taxonomy, role_group, role_family, specialties,
                business_domains, tech_stack, classification_meta,
                inferred_track, inferred_track_name, display_category,
                location, country, business_unit, product, recruitment_type,
                employment_type, experience, description, requirements,
                highlights, preferred_qualifications, source_url, detail_status,
                refresh_version, refresh_started_at, updated_at, crawled_at, synced_at
            FROM official_recruitment_jobs
            WHERE source = %s AND recruitment_type = %s AND source_job_id = %s AND is_latest = 1
            LIMIT 1
            """,
            (source, recruitment_type, source_job_id),
        )
        return self._row_to_job(row) if row else None

    async def latest_versions(self) -> List[Dict[str, Any]]:
        rows = await self._fetch_all(
            """
            SELECT
                source,
                recruitment_type,
                refresh_version,
                COUNT(*) AS job_count,
                MAX(refresh_started_at) AS refresh_started_at,
                MAX(synced_at) AS synced_at
            FROM official_recruitment_jobs
            WHERE is_latest = 1
            GROUP BY source, recruitment_type, refresh_version
            ORDER BY MAX(synced_at) DESC
            """
        )
        return [
            {
                "source": row[0],
                "recruitment_type": row[1],
                "refresh_version": row[2],
                "job_count": row[3],
                "refresh_started_at": self._format_datetime(row[4]),
                "synced_at": self._format_datetime(row[5]),
            }
            for row in rows
        ]

    async def create_refresh_run(self, version: str, source: str, recruitment_type: str, started_at: datetime):
        await self._execute(
            """
            INSERT INTO official_recruitment_refresh_runs (
                refresh_version, source, recruitment_type, status, started_at
            ) VALUES (%s, %s, %s, 'running', %s)
            ON DUPLICATE KEY UPDATE
                status = 'running',
                job_count = 0,
                error_message = NULL,
                quality_json = NULL,
                started_at = VALUES(started_at),
                finished_at = NULL
            """,
            (version, source, recruitment_type, started_at),
        )

    async def finish_refresh_run(
        self,
        version: str,
        source: str,
        recruitment_type: str,
        status: str,
        job_count: int,
        error_message: Optional[str] = None,
        quality: Optional[Dict[str, Any]] = None,
    ):
        await self._execute(
            """
            UPDATE official_recruitment_refresh_runs
            SET status = %s, job_count = %s, error_message = %s, quality_json = %s, finished_at = CURRENT_TIMESTAMP
            WHERE refresh_version = %s AND source = %s AND recruitment_type = %s
            """,
            (status, job_count, error_message, json.dumps(quality or {}, ensure_ascii=False), version, source, recruitment_type),
        )

    def _to_row(
        self,
        job: Dict[str, Any],
        refresh_version: Optional[str] = None,
        refresh_started_at: Optional[datetime] = None,
    ) -> tuple:
        description = job.get("description") or ""
        requirements = job.get("requirements") or ""
        detail_status = "complete" if description.strip() and requirements.strip() else "missing_detail"
        return (
            self._str(job.get("source"), 40),
            self._str(job.get("source_job_id"), 120),
            self._str(job.get("company"), 80),
            self._str(job.get("title"), 300),
            self._str(job.get("category"), 120),
            self._str(job.get("job_family"), 120),
            json.dumps(job.get("official_taxonomy") or {}, ensure_ascii=False),
            self._str(job.get("role_group"), 40),
            self._str(job.get("role_family"), 40),
            json.dumps(job.get("specialties") or [], ensure_ascii=False),
            json.dumps(job.get("business_domains") or [], ensure_ascii=False),
            json.dumps(job.get("tech_stack") or [], ensure_ascii=False),
            json.dumps(job.get("classification_meta") or {}, ensure_ascii=False),
            self._str(job.get("inferred_track"), 40),
            self._str(job.get("inferred_track_name"), 80),
            self._str(job.get("display_category"), 80),
            self._str(job.get("location"), 500),
            self._str(job.get("country"), 80),
            self._str(job.get("business_unit"), 500),
            self._str(job.get("product"), 200),
            self._str(job.get("recruitment_type") or "campus", 30),
            self._str(job.get("employment_type"), 80),
            self._str(job.get("experience"), 120),
            description,
            requirements,
            job.get("highlights") or "",
            job.get("preferred_qualifications") or "",
            self._str(job.get("source_url"), 1000),
            detail_status,
            json.dumps(job, ensure_ascii=False),
            self._str(refresh_version or job.get("refresh_version"), 80),
            refresh_started_at or self._parse_datetime(job.get("refresh_started_at")),
            1,
            self._parse_datetime(job.get("updated_at")),
            self._parse_datetime(job.get("crawled_at")),
        )

    def _row_to_job(self, row) -> Dict[str, Any]:
        return {
            "source": row[0],
            "source_job_id": row[1],
            "company": row[2],
            "title": row[3],
            "category": row[4],
            "job_family": row[5],
            "official_taxonomy": self._json_value(row[6], {}),
            "role_group": row[7],
            "role_family": row[8],
            "specialties": self._json_value(row[9], []),
            "business_domains": self._json_value(row[10], []),
            "tech_stack": self._json_value(row[11], []),
            "classification_meta": self._json_value(row[12], {}),
            "inferred_track": row[13],
            "inferred_track_name": row[14],
            "display_category": row[15],
            "location": row[16],
            "country": row[17],
            "business_unit": row[18],
            "product": row[19],
            "recruitment_type": row[20],
            "employment_type": row[21],
            "experience": row[22],
            "description": row[23] or "",
            "requirements": row[24] or "",
            "highlights": row[25] or "",
            "preferred_qualifications": row[26] or "",
            "source_url": row[27],
            "detail_status": row[28],
            "refresh_version": row[29],
            "refresh_started_at": self._format_datetime(row[30]),
            "updated_at": self._format_datetime(row[31]),
            "crawled_at": self._format_datetime(row[32]),
            "synced_at": self._format_datetime(row[33]),
        }

    async def _ensure_column(self, table: str, column: str, definition: str):
        exists = await self._fetch_one(
            """
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s
            """,
            (table, column),
        )
        if not exists or exists[0] == 0:
            await self._execute(f"ALTER TABLE `{table}` ADD COLUMN {definition}")

    async def _ensure_index(self, table: str, index_name: str, definition: str):
        exists = await self._fetch_one(
            """
            SELECT COUNT(*) FROM information_schema.statistics
            WHERE table_schema = DATABASE() AND table_name = %s AND index_name = %s
            """,
            (table, index_name),
        )
        if not exists or exists[0] == 0:
            await self._execute(f"ALTER TABLE `{table}` ADD {definition}")

    @staticmethod
    def _str(value: Any, max_length: int) -> Optional[str]:
        if value in (None, ""):
            return None
        return str(value)[:max_length]

    @staticmethod
    def _json_value(value: Any, default: Any):
        if value in (None, ""):
            return default
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(text).replace(tzinfo=None)
        except ValueError:
            return None

    @staticmethod
    def _format_datetime(value: Any) -> Optional[str]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
