import mysql.connector
from split_content import split_interview_content
from datetime import datetime

def get_db_connection():
    """创建数据库连接"""
    return mysql.connector.connect(
        host="116.198.250.133",
        port=13306,
        user="root",
        password="123456",
        database="mianjing",
        charset="utf8mb4"
    )

def process_interview_content():
    """
    处理面经内容：
    1. 获取status=1的记录
    2. 分割content
    3. 保存分割后的问题
    4. 更新原记录状态
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取status=1的记录
        select_query = """
        SELECT id, content, company, edit_time 
        FROM niuke 
        WHERE status = 1 
        AND content IS NOT NULL 
        AND content != ''
        """
        cursor.execute(select_query)
        records = cursor.fetchall()
        
        print(f"找到 {len(records)} 条需要处理的记录")
        
        # 处理每条记录
        for record in records:
            try:
                # 分割内容
                questions = split_interview_content(record['content'])
                
                # 插入分割后的问题
                insert_query = """
                INSERT INTO questions
                (company, question, category, edit_time, niu_id) 
                VALUES (%s, %s, %s, %s, %s)
                """
                
                # 为每个问题创建记录
                for question in questions:
                    values = (
                        record['company'],
                        question,
                        '其他',  # 默认分类
                        record['edit_time'],
                        record['id']
                    )
                    cursor.execute(insert_query, values)
                
                # 更新原记录状态为2
                update_query = "UPDATE niuke SET status = 2 WHERE id = %s"
                cursor.execute(update_query, (record['id'],))
                
                # 提交事务
                conn.commit()
                print(f"ID {record['id']} 处理完成: 分割出 {len(questions)} 个问题")
                
            except Exception as e:
                print(f"处理记录 {record['id']} 时出错: {e}")
                conn.rollback()
                continue
        
    except Exception as e:
        print(f"数据库操作错误: {e}")
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def test_single_record(record_id):
    """测试单条记录的分割结果"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取指定记录
        cursor.execute("SELECT content FROM niuke WHERE id = %s", (record_id,))
        record = cursor.fetchone()
        
        if record and record['content']:
            print("原始内容:")
            print("-" * 40)
            print(record['content'])
            print("\n分割结果:")
            print("-" * 40)
            questions = split_interview_content(record['content'])
            for i, q in enumerate(questions, 1):
                print(f"{i}. {q}")
        else:
            print(f"未找到ID为 {record_id} 的记录或内容为空")
            
    except Exception as e:
        print(f"测试出错: {e}")
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # 是否进行测试模式
    TEST_MODE = False
    
    if TEST_MODE:
        # 测试模式：测试单条记录
        test_record_id = 49  # 替换为要测试的记录ID
        print("=== 测试模式 ===")
        test_single_record(test_record_id)
    else:
        # 正式处理模式
        print("=== 开始处理面经内容 ===")
        process_interview_content()
        print("=== 处理完成 ===")
