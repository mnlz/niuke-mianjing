import mysql.connector
from mysql.connector import Error

def clean_duplicate_and_empty_data(connection):
    """
    清理数据库中的重复数据和空数据
    :param connection: MySQL数据库连接
    :return: tuple (删除的重复数据数量, 删除的空数据数量)
    """
    cursor = connection.cursor()
    try:
        # 1. 删除重复数据（保留最小ID）
        duplicate_sql = """
        DELETE FROM `niuke`
        WHERE id NOT IN (
            SELECT * FROM (
                SELECT MIN(id)
                FROM `niuke`
                GROUP BY title, content
            ) AS temp
        );
        """
        cursor.execute(duplicate_sql)
        duplicates_removed = cursor.rowcount
        
        # 2. 删除空数据
        empty_sql = """
        DELETE FROM `niuke`
        WHERE title IS NULL OR title = ''
           OR content IS NULL OR content = '';
        """
        cursor.execute(empty_sql)
        empty_removed = cursor.rowcount
        
        # 提交更改
        connection.commit()
        
        print(f"数据清理完成:")
        print(f"- 删除了 {duplicates_removed} 条重复数据")
        print(f"- 删除了 {empty_removed} 条空数据")
        
        return duplicates_removed, empty_removed
        
    except Error as e:
        print(f"清理数据时发生错误: {e}")
        connection.rollback()
        return 0, 0
    finally:
        cursor.close()

if __name__ == "__main__":
    # 测试代码
    try:
        # 测试本地连接
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="123456",
            database="mianjing",
            charset="utf8mb4"
        )
        clean_duplicate_and_empty_data(conn)
        conn.close()
        
    except Error as e:
        print(f"连接数据库时发生错误: {e}")
