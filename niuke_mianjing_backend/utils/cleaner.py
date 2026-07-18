from mysql.connector import Error

from niuke_mianjing_backend.utils.logger import get_logger

logger = get_logger(__name__)


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

        logger.info("数据清理完成: 删除重复 %d 条, 删除空数据 %d 条", duplicates_removed, empty_removed)

        return duplicates_removed, empty_removed

    except Error as e:
        logger.exception("清理数据失败")
        connection.rollback()
        return 0, 0
    finally:
        cursor.close()
