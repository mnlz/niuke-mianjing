import mysql.connector
import re

def strip_html_tags(text):
    """去除HTML标签"""
    return re.sub(r'<[^>]+>', '', text)

def clean_database_content():
    # 数据库连接配置
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '123456',
        'database': 'mianjing'
    }

    try:
        # 连接数据库
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        # 查询所有记录
        select_query = "SELECT id, content FROM niuke"
        cursor.execute(select_query)
        records = cursor.fetchall()

        # 更新计数器
        updated_count = 0

        # 处理每条记录
        for record_id, content in records:
            if content:
                # 清理HTML标签
                cleaned_content = strip_html_tags(content)
                
                # 如果内容有变化，则更新数据库
                if cleaned_content != content:
                    update_query = "UPDATE niuke SET content = %s WHERE id = %s"
                    cursor.execute(update_query, (cleaned_content, record_id))
                    updated_count += 1
                    
                    # 每100条记录提交一次事务
                    if updated_count % 100 == 0:
                        cnx.commit()
                        print(f"已更新 {updated_count} 条记录...")

        # 提交剩余的更改
        cnx.commit()
        print(f"\n清理完成！总共更新了 {updated_count} 条记录。")

    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'cnx' in locals():
            cnx.close()
            print("数据库连接已关闭")

if __name__ == '__main__':
    print("开始清理数据库中的HTML标签...")
    clean_database_content()
