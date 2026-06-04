from datetime import datetime
import mysql.connector

from niuke_mianjing_backend.config import get_db_config


class NiukeDataManager:
    def __init__(self, db_config=None):
        self.db_config = db_config or get_db_config()
        self.db = mysql.connector.connect(**self.db_config)

    def get_data(self, post: str = None, company: str = None, 
                 limit: int = 20, offset: int = 0):
        cur = self.db.cursor()
        
        where_conditions = []
        params = []
        
        if post:
            where_conditions.append("post = %s")
            params.append(post)
        
        if company:
            where_conditions.append("company = %s")
            params.append(company)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        count_query = f"""
            SELECT COUNT(*) FROM niuke
            {where_clause}
        """
        cur.execute(count_query, tuple(params))
        total = cur.fetchone()[0]
        
        query = f"""
            SELECT id, content_id, title, content, edit_time, `read`, post, company, status
            FROM niuke
            {where_clause}
            ORDER BY edit_time DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cur.close()
        
        data = []
        for row in rows:
            data.append({
                "id": row[0],
                "content_id": row[1],
                "title": row[2],
                "content": row[3],
                "edit_time": row[4].isoformat() if row[4] else None,
                "read": row[5],
                "post": row[6],
                "company": row[7],
                "status": row[8]
            })
        
        return {
            "data": data,
            "total": total
        }

    def get_stats(self):
        cur = self.db.cursor()
        
        cur.execute("""
            SELECT COUNT(*) FROM niuke
        """)
        total_records = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(*) FROM niuke WHERE status = 1
        """)
        active_records = cur.fetchone()[0]
        
        cur.execute("""
            SELECT post, COUNT(*) as count 
            FROM niuke 
            GROUP BY post
        """)
        post_stats = [{"post": row[0], "count": row[1]} for row in cur.fetchall()]
        
        cur.close()
        
        return {
            "total_records": total_records,
            "active_records": active_records,
            "post_stats": post_stats
        }

    def close(self):
        self.db.close()
