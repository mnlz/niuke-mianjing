import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from niuke_mianjing_backend.repositories.base import BaseRepository


class WeChatArticleRepository(BaseRepository):
    async def init_table(self):
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS `wechat_articles` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `source_record_id` INT NULL,
                `title` VARCHAR(255) NOT NULL,
                `author` VARCHAR(64) NULL,
                `digest` VARCHAR(255) NULL,
                `content_source_url` VARCHAR(500) NULL,
                `markdown` MEDIUMTEXT NOT NULL,
                `html` MEDIUMTEXT NOT NULL,
                `cover_base64` LONGTEXT NULL,
                `cover_mime` VARCHAR(50) DEFAULT 'image/png',
                `prompt` MEDIUMTEXT NULL,
                `model_info` JSON NULL,
                `wechat_media_id` VARCHAR(128) NULL,
                `cover_media_id` VARCHAR(128) NULL,
                `status` VARCHAR(32) DEFAULT 'generated',
                `error_message` TEXT NULL,
                `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
                `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                KEY `idx_source_record_id` (`source_record_id`),
                KEY `idx_status` (`status`),
                KEY `idx_created_at` (`created_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='微信公众号 AI 生成稿'
            """
        )

    async def create_article(
        self,
        source_record_id: Optional[int],
        title: str,
        author: Optional[str],
        digest: Optional[str],
        content_source_url: Optional[str],
        markdown: str,
        html: str,
        cover_base64: Optional[str],
        cover_mime: str,
        prompt: Optional[str],
        model_info: Dict[str, Any],
        status: str = "generated",
    ) -> int:
        return await self._execute_lastrowid(
            """
            INSERT INTO wechat_articles (
                source_record_id, title, author, digest, content_source_url,
                markdown, html, cover_base64, cover_mime, prompt, model_info, status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                source_record_id,
                title,
                author,
                digest,
                content_source_url,
                markdown,
                html,
                cover_base64,
                cover_mime,
                prompt,
                json.dumps(model_info, ensure_ascii=False),
                status,
            ),
        )

    async def get_article(self, article_id: int, include_content: bool = True) -> Optional[Dict[str, Any]]:
        columns = """
            id, source_record_id, title, author, digest, content_source_url,
            markdown, html, cover_base64, cover_mime, prompt, model_info,
            wechat_media_id, cover_media_id, status, error_message, created_at, updated_at
        """
        if not include_content:
            columns = """
                id, source_record_id, title, author, digest, content_source_url,
                NULL, NULL, NULL, cover_mime, NULL, model_info,
                wechat_media_id, cover_media_id, status, error_message, created_at, updated_at
            """

        row = await self._fetch_one(
            f"SELECT {columns} FROM wechat_articles WHERE id = %s",
            (article_id,),
        )
        return self._row_to_dict(row) if row else None

    async def list_articles(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        rows = await self._fetch_all(
            """
            SELECT
                id, source_record_id, title, author, digest, content_source_url,
                NULL, NULL, NULL, cover_mime, NULL, model_info,
                wechat_media_id, cover_media_id, status, error_message, created_at, updated_at
            FROM wechat_articles
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        return [self._row_to_dict(row) for row in rows]

    async def update_publish_result(
        self,
        article_id: int,
        status: str,
        wechat_media_id: Optional[str] = None,
        cover_media_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        await self._execute(
            """
            UPDATE wechat_articles
            SET status = %s,
                wechat_media_id = COALESCE(%s, wechat_media_id),
                cover_media_id = COALESCE(%s, cover_media_id),
                error_message = %s,
                updated_at = %s
            WHERE id = %s
            """,
            (status, wechat_media_id, cover_media_id, error_message, datetime.now(), article_id),
        )

    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        model_info = {}
        if row[11]:
            try:
                model_info = json.loads(row[11])
            except json.JSONDecodeError:
                model_info = {}

        return {
            "id": row[0],
            "source_record_id": row[1],
            "title": row[2],
            "author": row[3],
            "digest": row[4],
            "content_source_url": row[5],
            "markdown": row[6],
            "html": row[7],
            "cover_base64": row[8],
            "cover_mime": row[9],
            "prompt": row[10],
            "model_info": model_info,
            "wechat_media_id": row[12],
            "cover_media_id": row[13],
            "status": row[14],
            "error_message": row[15],
            "created_at": row[16].isoformat() if row[16] else None,
            "updated_at": row[17].isoformat() if row[17] else None,
        }
