import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from niuke_mianjing_backend.repositories.base import BaseRepository


class ReviewRepository(BaseRepository):
    async def init_tables(self):
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS `app_users` (
                `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
                `visitor_key` VARCHAR(128) NOT NULL,
                `email` VARCHAR(255) NULL,
                `password_hash` VARCHAR(255) NULL,
                `display_name` VARCHAR(64) NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY `uk_app_users_visitor_key` (`visitor_key`),
                UNIQUE KEY `uk_app_users_email` (`email`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        await self._upgrade_account_columns()
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS `review_progress` (
                `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
                `record_id` BIGINT NOT NULL,
                `favorite` TINYINT NOT NULL DEFAULT 0,
                `mastery` VARCHAR(32) NOT NULL DEFAULT 'new',
                `note` TEXT NULL,
                `last_reviewed_at` DATETIME NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY `uk_review_progress_record` (`record_id`),
                KEY `idx_review_progress_favorite` (`favorite`),
                KEY `idx_review_progress_mastery` (`mastery`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        await self._execute(
            """
            CREATE TABLE IF NOT EXISTS `review_ai_reviews` (
                `id` BIGINT PRIMARY KEY AUTO_INCREMENT,
                `record_id` BIGINT NOT NULL,
                `review_json` JSON NOT NULL,
                `prompt` TEXT NULL,
                `model` VARCHAR(128) NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY `uk_review_ai_record` (`record_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        await self._upgrade_progress_user_scope()

    async def _upgrade_account_columns(self):
        for name, definition in (
            ("email", "VARCHAR(255) NULL"),
            ("password_hash", "VARCHAR(255) NULL"),
            ("display_name", "VARCHAR(64) NULL"),
        ):
            row = await self._fetch_one(
                "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'app_users' AND column_name = %s",
                (name,),
            )
            if not row or row[0] == 0:
                await self._execute(f"ALTER TABLE app_users ADD COLUMN {name} {definition}")
        index = await self._fetch_one(
            "SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'app_users' AND index_name = 'uk_app_users_email'"
        )
        if not index or index[0] == 0:
            await self._execute("ALTER TABLE app_users ADD UNIQUE KEY uk_app_users_email (email)")

    async def _upgrade_progress_user_scope(self):
        column = await self._fetch_one(
            """
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = 'review_progress'
              AND column_name = 'user_id'
            """
        )
        if not column or column[0] == 0:
            await self._execute("ALTER TABLE review_progress ADD COLUMN user_id BIGINT NULL AFTER id")

        legacy_user_id = await self.get_or_create_user("legacy-shared-user")
        await self._execute("UPDATE review_progress SET user_id = %s WHERE user_id IS NULL", (legacy_user_id,))

        old_index = await self._fetch_one(
            """
            SELECT COUNT(*) FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = 'review_progress'
              AND index_name = 'uk_review_progress_record'
            """
        )
        if old_index and old_index[0] > 0:
            await self._execute("ALTER TABLE review_progress DROP INDEX uk_review_progress_record")

        scoped_index = await self._fetch_one(
            """
            SELECT COUNT(*) FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = 'review_progress'
              AND index_name = 'uk_review_progress_user_record'
            """
        )
        if not scoped_index or scoped_index[0] == 0:
            await self._execute(
                "ALTER TABLE review_progress ADD UNIQUE KEY uk_review_progress_user_record (user_id, record_id)"
            )

    async def get_or_create_user(self, visitor_key: str) -> int:
        safe_key = (visitor_key or "anonymous").strip()[:128] or "anonymous"
        await self._execute(
            """
            INSERT INTO app_users (visitor_key)
            VALUES (%s)
            ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP
            """,
            (safe_key,),
        )
        row = await self._fetch_one("SELECT id FROM app_users WHERE visitor_key = %s", (safe_key,))
        return int(row[0])

    async def create_account(self, email: str, password_hash: str, display_name: str) -> Dict[str, Any]:
        visitor_key = f"account:{hashlib.sha256(email.encode('utf-8')).hexdigest()}"
        await self._execute(
            "INSERT INTO app_users (visitor_key, email, password_hash, display_name) VALUES (%s, %s, %s, %s)",
            (visitor_key, email, password_hash, display_name),
        )
        account = await self.get_account_by_email(email)
        if not account:
            raise RuntimeError("账户创建失败")
        return account

    async def get_account_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        row = await self._fetch_one(
            "SELECT id, email, password_hash, display_name FROM app_users WHERE email = %s",
            (email,),
        )
        return {"id": int(row[0]), "email": row[1], "password_hash": row[2], "display_name": row[3]} if row else None

    async def get_account_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        row = await self._fetch_one(
            "SELECT id, email, password_hash, display_name FROM app_users WHERE id = %s AND email IS NOT NULL",
            (user_id,),
        )
        return {"id": int(row[0]), "email": row[1], "password_hash": row[2], "display_name": row[3]} if row else None

    async def set_account_display_name(self, user_id: int, display_name: str) -> Dict[str, Any]:
        await self._execute("UPDATE app_users SET display_name = %s WHERE id = %s", (display_name, user_id))
        account = await self.get_account_by_id(user_id)
        if not account:
            raise RuntimeError("账户不存在")
        return account

    async def get_progress_map(self, user_id: int, record_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        if not record_ids:
            return {}
        placeholders = ",".join(["%s"] * len(record_ids))
        rows = await self._fetch_all(
            f"""
            SELECT record_id, favorite, mastery, note, last_reviewed_at, updated_at
            FROM review_progress
            WHERE user_id = %s AND record_id IN ({placeholders})
            """,
            tuple([user_id, *record_ids]),
        )
        return {
            int(row[0]): {
                "record_id": int(row[0]),
                "favorite": bool(row[1]),
                "mastery": row[2],
                "note": row[3],
                "last_reviewed_at": row[4].isoformat() if row[4] else None,
                "updated_at": row[5].isoformat() if row[5] else None,
            }
            for row in rows
        }

    async def upsert_progress(
        self,
        user_id: int,
        record_id: int,
        favorite: Optional[bool] = None,
        mastery: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        current = (await self.get_progress_map(user_id, [record_id])).get(record_id, {})
        next_favorite = int(favorite if favorite is not None else current.get("favorite", False))
        next_mastery = mastery or current.get("mastery") or "new"
        next_note = note if note is not None else current.get("note")
        last_reviewed_at = datetime.now() if mastery and mastery != "new" else None

        await self._execute(
            """
            INSERT INTO review_progress (user_id, record_id, favorite, mastery, note, last_reviewed_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                favorite = VALUES(favorite),
                mastery = VALUES(mastery),
                note = VALUES(note),
                last_reviewed_at = COALESCE(VALUES(last_reviewed_at), last_reviewed_at),
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, record_id, next_favorite, next_mastery, next_note, last_reviewed_at),
        )
        return (await self.get_progress_map(user_id, [record_id])).get(record_id, self.default_progress(record_id))

    async def get_ai_review(self, record_id: int) -> Optional[Dict[str, Any]]:
        row = await self._fetch_one(
            """
            SELECT record_id, review_json, model, updated_at
            FROM review_ai_reviews
            WHERE record_id = %s
            """,
            (record_id,),
        )
        if not row:
            return None
        review = json.loads(row[1]) if isinstance(row[1], str) else row[1]
        return {
            "record_id": int(row[0]),
            "review": review,
            "model": row[2],
            "updated_at": row[3].isoformat() if row[3] else None,
        }

    async def save_ai_review(self, record_id: int, review: Dict[str, Any], prompt: str, model: str) -> Dict[str, Any]:
        await self._execute(
            """
            INSERT INTO review_ai_reviews (record_id, review_json, prompt, model)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                review_json = VALUES(review_json),
                prompt = VALUES(prompt),
                model = VALUES(model),
                updated_at = CURRENT_TIMESTAMP
            """,
            (record_id, json.dumps(review, ensure_ascii=False), prompt, model),
        )
        saved = await self.get_ai_review(record_id)
        return saved or {"record_id": record_id, "review": review, "model": model, "updated_at": None}

    @staticmethod
    def default_progress(record_id: int) -> Dict[str, Any]:
        return {
            "record_id": record_id,
            "favorite": False,
            "mastery": "new",
            "note": None,
            "last_reviewed_at": None,
            "updated_at": None,
        }
