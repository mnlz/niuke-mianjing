from typing import Any, Dict, List

from niuke_mianjing_backend.repositories.base import BaseRepository


class AIModelRepository(BaseRepository):
    async def init_table(self):
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS `ai_model_configs` (
                `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
                `model` VARCHAR(191) NOT NULL,
                `channel_name` VARCHAR(100) NOT NULL DEFAULT '默认线路',
                `endpoint` VARCHAR(1000) NOT NULL,
                `api_key_encrypted` TEXT NULL,
                `description` VARCHAR(500) NULL,
                `enabled` TINYINT NOT NULL DEFAULT 1,
                `is_default` TINYINT NOT NULL DEFAULT 0,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        column = await self._fetch_one(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'ai_model_configs' AND column_name = 'channel_name'"
        )
        if not column or not column[0]:
            await self._execute("ALTER TABLE ai_model_configs ADD COLUMN channel_name VARCHAR(100) NOT NULL DEFAULT '默认线路' AFTER model")
        index = await self._fetch_one(
            "SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'ai_model_configs' AND index_name = 'uk_ai_model_name'"
        )
        if index and index[0]:
            await self._execute("ALTER TABLE ai_model_configs DROP INDEX uk_ai_model_name")

    async def list_all(self) -> List[Dict[str, Any]]:
        rows = await self._fetch_all(
            "SELECT id, model, channel_name, endpoint, api_key_encrypted, description, enabled, is_default FROM ai_model_configs ORDER BY id"
        )
        return [{
            "id": row[0], "model": row[1], "channel_name": row[2], "endpoint": row[3],
            "api_key_encrypted": row[4] or "", "description": row[5] or "",
            "enabled": bool(row[6]), "is_default": bool(row[7]),
        } for row in rows]

    async def save(self, item: Dict[str, Any], model_id: int | None = None) -> bool:
        if item.get("is_default"):
            await self._execute("UPDATE ai_model_configs SET is_default = 0 WHERE is_default = 1")
        values = (
            item["model"], item["channel_name"], item["endpoint"], item.get("api_key_encrypted", ""),
            item.get("description", ""), int(item.get("enabled", True)), int(item.get("is_default", False)),
        )
        if model_id is None:
            return bool(await self._execute(
                "INSERT INTO ai_model_configs (model, channel_name, endpoint, api_key_encrypted, description, enabled, is_default) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                values,
            ))
        return bool(await self._execute(
            """
            UPDATE ai_model_configs SET model = %s, channel_name = %s, endpoint = %s,
                api_key_encrypted = IF(%s = '', api_key_encrypted, %s), description = %s,
                enabled = %s, is_default = %s WHERE id = %s
            """,
            (values[0], values[1], values[2], values[3], values[3], *values[4:], model_id),
        ))

    async def delete(self, model_id: int) -> bool:
        return bool(await self._execute("DELETE FROM ai_model_configs WHERE id = %s", (model_id,)))
