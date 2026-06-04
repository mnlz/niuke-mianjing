from mysql.connector import Error


def clean_duplicate_and_empty_data(connection):
    cursor = connection.cursor()
    try:
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
        
        empty_sql = """
        DELETE FROM `niuke`
        WHERE title IS NULL OR title = ''
           OR content IS NULL OR content = '';
        """
        cursor.execute(empty_sql)
        empty_removed = cursor.rowcount
        
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
