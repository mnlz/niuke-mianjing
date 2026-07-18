import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from niuke_mianjing_backend.repositories.base import BaseRepository


class NiukeRepository(BaseRepository):
    async def get_data(
        self,
        post: Optional[str] = None,
        company: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        conditions = []
        params: list = []

        if post:
            conditions.append("post = %s")
            params.append(post)
        if company:
            conditions.append("company = %s")
            params.append(company)

        where = ""
        if conditions:
            where = "WHERE " + " AND ".join(conditions)

        total = await self._fetch_one(
            f"SELECT COUNT(*) FROM niuke {where}", tuple(params) if params else None
        )

        query_params = params + [limit, offset]
        rows = await self._fetch_all(
            f"""
            SELECT id, content_id, title, content, edit_time, `read`, post, company, status
            FROM niuke {where}
            ORDER BY edit_time DESC
            LIMIT %s OFFSET %s
            """,
            tuple(query_params),
        )

        data = []
        for row in rows:
            data.append(
                {
                    "id": row[0],
                    "content_id": row[1],
                    "title": row[2],
                    "content": row[3],
                    "edit_time": row[4].isoformat() if row[4] else None,
                    "read": row[5],
                    "post": row[6],
                    "company": row[7],
                    "status": row[8],
                }
            )

        return {"data": data, "total": total[0] if total else 0}

    async def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        row = await self._fetch_one(
            """
            SELECT id, content_id, title, content, edit_time, `read`, post, company, status
            FROM niuke
            WHERE id = %s
            """,
            (record_id,),
        )
        if not row:
            return None
        return {
            "id": row[0],
            "content_id": row[1],
            "title": row[2],
            "content": row[3],
            "edit_time": row[4].isoformat() if row[4] else None,
            "read": row[5],
            "post": row[6],
            "company": row[7],
            "status": row[8],
        }

    async def get_by_ids(self, record_ids: List[int], limit: int = 8) -> List[Dict[str, Any]]:
        ids = [int(item) for item in record_ids[:limit] if item]
        if not ids:
            return []
        placeholders = ",".join(["%s"] * len(ids))
        rows = await self._fetch_all(
            f"""
            SELECT id, content_id, title, content, edit_time, `read`, post, company, status
            FROM niuke
            WHERE id IN ({placeholders})
              AND content IS NOT NULL
              AND content <> ''
            ORDER BY FIELD(id, {placeholders})
            """,
            tuple(ids + ids),
        )
        return [
            {
                "id": row[0],
                "content_id": row[1],
                "title": row[2],
                "content": row[3],
                "edit_time": row[4].isoformat() if row[4] else None,
                "read": row[5],
                "post": row[6],
                "company": row[7],
                "status": row[8],
            }
            for row in rows
        ]

    async def search_related_interviews(
        self,
        company: str,
        keywords: List[str],
        limit: int = 8,
        post_keywords: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        conditions = ["company = %s", "content IS NOT NULL", "content <> ''"]
        params: list = [company]
        post_conditions = []
        for keyword in [item.strip() for item in (post_keywords or []) if item and item.strip()][:6]:
            post_conditions.append("post LIKE %s")
            params.append(f"%{keyword}%")
        if post_conditions:
            conditions.append("(" + " OR ".join(post_conditions) + ")")
        keyword_conditions = []
        for keyword in [item.strip() for item in keywords if item and item.strip()][:8]:
            keyword_conditions.append("(post LIKE %s OR title LIKE %s OR content LIKE %s)")
            like = f"%{keyword}%"
            params.extend([like, like, like])
        if keyword_conditions:
            conditions.append("(" + " OR ".join(keyword_conditions) + ")")
        rows = await self._fetch_all(
            f"""
            SELECT id, content_id, title, content, edit_time, `read`, post, company, status
            FROM niuke
            WHERE {" AND ".join(conditions)}
            ORDER BY edit_time DESC
            LIMIT %s
            """,
            tuple(params + [limit]),
        )
        return [
            {
                "id": row[0],
                "content_id": row[1],
                "title": row[2],
                "content": row[3],
                "edit_time": row[4].isoformat() if row[4] else None,
                "read": row[5],
                "post": row[6],
                "company": row[7],
                "status": row[8],
            }
            for row in rows
        ]

    async def get_recent_records(
        self,
        company: str,
        post: str,
        start_time: datetime,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        rows = await self._fetch_all(
            """
            SELECT id, content_id, title, content, edit_time, `read`, post, company, status
            FROM niuke
            WHERE company = %s
              AND post = %s
              AND edit_time >= %s
              AND content IS NOT NULL
              AND content <> ''
            ORDER BY edit_time DESC
            LIMIT %s
            """,
            (company, post, start_time, limit),
        )
        return [
            {
                "id": row[0],
                "content_id": row[1],
                "title": row[2],
                "content": row[3],
                "edit_time": row[4].isoformat() if row[4] else None,
                "read": row[5],
                "post": row[6],
                "company": row[7],
                "status": row[8],
            }
            for row in rows
        ]

    async def get_records_for_analysis(
        self,
        company: str,
        post: str,
        limit: int = 10,
        start_time: Optional[datetime] = None,
        order_by_time: bool = False,
    ) -> List[Dict[str, Any]]:
        conditions = [
            "company = %s",
            "post = %s",
            "content IS NOT NULL",
            "content <> ''",
        ]
        params: list = [company, post]
        if start_time:
            conditions.append("edit_time >= %s")
            params.append(start_time)

        order_clause = "ORDER BY edit_time DESC" if order_by_time else "ORDER BY RAND()"
        rows = await self._fetch_all(
            f"""
            SELECT id, content_id, title, content, edit_time, `read`, post, company, status
            FROM niuke
            WHERE {" AND ".join(conditions)}
            {order_clause}
            LIMIT %s
            """,
            tuple(params + [limit]),
        )
        return [
            {
                "id": row[0],
                "content_id": row[1],
                "title": row[2],
                "content": row[3],
                "edit_time": row[4].isoformat() if row[4] else None,
                "read": row[5],
                "post": row[6],
                "company": row[7],
                "status": row[8],
            }
            for row in rows
        ]

    async def get_stats(self) -> Dict[str, Any]:
        total_row = await self._fetch_one("SELECT COUNT(*) FROM niuke")
        active_row = await self._fetch_one("SELECT COUNT(*) FROM niuke WHERE status = 1")
        post_rows = await self._fetch_all(
            "SELECT post, COUNT(*) as count FROM niuke GROUP BY post"
        )

        return {
            "total_records": total_row[0] if total_row else 0,
            "active_records": active_row[0] if active_row else 0,
            "post_stats": [{"post": r[0], "count": r[1]} for r in post_rows],
        }

    async def get_filters(self) -> Dict[str, List[str]]:
        post_rows = await self._fetch_all(
            "SELECT DISTINCT post FROM niuke WHERE post IS NOT NULL AND post <> '' ORDER BY post"
        )
        company_rows = await self._fetch_all(
            "SELECT DISTINCT company FROM niuke WHERE company IS NOT NULL AND company <> '' ORDER BY company"
        )
        return {
            "posts": [row[0] for row in post_rows],
            "companies": [row[0] for row in company_rows],
        }

    async def get_classification_rows(
        self,
        post: Optional[str] = None,
        company: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        conditions = []
        params = []
        if post:
            conditions.append("post = %s")
            params.append(post)
        if company:
            conditions.append("company = %s")
            params.append(company)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = await self._fetch_all(
            f"""
            SELECT id, title, LEFT(content, 1500), post
            FROM niuke {where}
            ORDER BY edit_time DESC
            """,
            tuple(params) if params else None,
        )
        return [
            {"id": row[0], "title": row[1], "content": row[2], "post": row[3]}
            for row in rows
        ]

    async def upsert_content(self, items: List[Dict]) -> Dict[str, int]:
        pool = await self._get_pool()
        new_count = 0
        updated_count = 0

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                for item in items:
                    status = 1 if item["company"] != "未知公司" else 0
                    await cur.execute(
                        "SELECT id, content FROM niuke WHERE title=%s AND post=%s ORDER BY id DESC LIMIT 1",
                        (item["title"], item["post"]),
                    )
                    row = await cur.fetchone()
                    if row:
                        if row[1] != item["content"]:
                            await cur.execute(
                                "UPDATE niuke SET content=%s, edit_time=%s, company=%s, status=%s, content_id=%s WHERE id=%s",
                                (item["content"], item["endTime"], item["company"], status, item["contentId"], row[0]),
                            )
                            updated_count += 1
                    else:
                        await cur.execute(
                            "INSERT INTO niuke (title, content, edit_time, post, company, status, content_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (item["title"], item["content"], item["endTime"], item["post"], item["company"], status, item["contentId"]),
                        )
                        new_count += 1
                await conn.commit()

        return {"new": new_count, "updated": updated_count}

    async def save_page_data(self, page_data: Dict, post: str):
        await self._execute(
            "INSERT INTO `update` (`time`, totalPage, total, post) VALUES (%s, %s, %s, %s)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), page_data["totalPage"], page_data["total"], post),
        )

    async def get_total_pages(self, post: str) -> Optional[Dict]:
        row = await self._fetch_one(
            "SELECT totalPage, total FROM `update` WHERE post=%s ORDER BY `time` DESC LIMIT 1",
            (post,),
        )
        if row:
            return {"total": row[1], "totalPage": row[0]}
        return None

    async def clean_duplicates_and_empty(self) -> Dict[str, int]:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    DELETE FROM `niuke`
                    WHERE id NOT IN (
                        SELECT * FROM (
                            SELECT MIN(id) FROM `niuke` GROUP BY title, content
                        ) AS temp
                    )
                    """
                )
                duplicates_removed = cur.rowcount

                await cur.execute(
                    """
                    DELETE FROM `niuke`
                    WHERE title IS NULL OR title = ''
                       OR content IS NULL OR content = ''
                    """
                )
                empty_removed = cur.rowcount

                await conn.commit()

        return {"duplicates_removed": duplicates_removed, "empty_removed": empty_removed}

    async def _get_pool(self):
        from niuke_mianjing_backend.repositories.database import DatabasePool
        return await DatabasePool.get_pool()
