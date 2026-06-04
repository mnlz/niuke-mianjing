from datetime import datetime
import mysql.connector

from niuke_mianjing_backend.config import get_db_config


class CrawlLogManager:
    def __init__(self, db_config=None):
        self.db_config = db_config or get_db_config()
        self.db = mysql.connector.connect(**self.db_config)

    def get_logs(self, post: str = None, status: str = None, 
                 start_date: str = None, end_date: str = None, limit: int = 10):
        cur = self.db.cursor()
        
        where_conditions = []
        params = []
        
        if post:
            where_conditions.append("post = %s")
            params.append(post)
        
        if status:
            where_conditions.append("status = %s")
            params.append(status)
        
        if start_date:
            where_conditions.append("DATE(start_time) >= %s")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("DATE(start_time) <= %s")
            params.append(end_date)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        query = f"""
            SELECT id, post, start_time, end_time, total_pages, 
                   new_records, updated_records, status, error_message
            FROM crawl_log 
            {where_clause}
            ORDER BY start_time DESC
            LIMIT %s
        """
        params.append(limit)
        
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        cur.close()
        
        logs = []
        for row in rows:
            logs.append({
                "id": row[0],
                "post": row[1],
                "start_time": row[2].isoformat() if row[2] else None,
                "end_time": row[3].isoformat() if row[3] else None,
                "total_pages": row[4],
                "new_records": row[5],
                "updated_records": row[6],
                "status": row[7],
                "error_message": row[8]
            })
        
        return logs

    def add_log(self, post: str, start_time: datetime, end_time: datetime, 
               total_pages: int, new_records: int, updated_records: int, 
               status: str, error_message: str = None):
        cur = self.db.cursor()
        cur.execute("""
            INSERT INTO crawl_log (post, start_time, end_time, total_pages, 
                               new_records, updated_records, status, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (post, start_time, end_time, total_pages, 
               new_records, updated_records, status, error_message))
        self.db.commit()
        cur.close()

    def close(self):
        self.db.close()
