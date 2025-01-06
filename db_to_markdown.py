import mysql.connector
from collections import defaultdict
import os
from datetime import datetime

def connect_db():
    return mysql.connector.connect(
        host="116.198.250.133",
        port=13306,
        user="root",
        password="123456",
        database="mianjing",
        charset="utf8mb4"
    )

def fetch_interview_data():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT title, content, edit_time, post, company FROM niuke")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def save_to_markdown(data):
    # Group data by company
    company_data = defaultdict(list)
    for row in data:
        company_data[row['company']].append(row)
    
    # Create output directory if it doesn't exist
    output_dir = "interview_md"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save data for each company
    for company, interviews in company_data.items():
        # Sort interviews by edit_time in descending order
        sorted_interviews = sorted(interviews, key=lambda x: x['edit_time'], reverse=True)
        filename = os.path.join(output_dir, f"{company}.md")
        with open(filename, 'w', encoding='utf-8') as f:
            for interview in sorted_interviews:
                f.write(f"# {interview['title']}\n\n")
                f.write(f"**职位/公司**: {interview['post']}, {interview['company']}\n\n")
                f.write(f"**面试时间**: {interview['edit_time']}\n\n")
                f.write(f"**面试内容**:\n{interview['content']}\n\n")
                f.write("---\n\n")  # Add separator between interviews

def save_all_interviews():
    """
    保存所有面试数据到markdown文件
    """
    print("开始获取所有面试数据...")
    data = fetch_interview_data()
    print(f"获取到 {len(data)} 条面试数据")
    
    save_to_markdown(data)
    print("所有数据已保存到 interview_md 目录")
    
    # 打印保存的文件列表
    output_dir = "interview_md"
    if os.path.exists(output_dir):
        print("\n生成的文件列表：")
        for file in os.listdir(output_dir):
            print(f"- {file}")

def test_save_markdown():
    """
    测试函数：只获取少量数据进行测试
    """
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 只获取3条数据进行测试
        cursor.execute("SELECT title, content, edit_time, post, company FROM niuke LIMIT 100")
        test_data = cursor.fetchall()
        
        print(f"获取到 {len(test_data)} 条测试数据")
        save_to_markdown(test_data)
        print("测试数据已保存到 interview_md 目录")
        
        # 打印保存的文件列表
        output_dir = "interview_md"
        if os.path.exists(output_dir):
            print("\n生成的文件列表：")
            for file in os.listdir(output_dir):
                print(f"- {file}")
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # test_save_markdown()  # 注释掉测试函数
    save_all_interviews()  # 保存所有数据
