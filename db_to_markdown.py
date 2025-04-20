import mysql.connector
from collections import defaultdict
import os
from datetime import datetime

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
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
    # 获取当前日期作为文件夹后缀
    date_suffix = datetime.now().strftime("%Y%m%d")
    
    # 按post和company分组数据
    post_company_data = defaultdict(lambda: defaultdict(list))
    for row in data:
        post = row['post'] if row['post'] else '未知'
        post_company_data[post][row['company']].append(row)
    
    # 为每个post创建单独的目录
    for post, company_data in post_company_data.items():
        # 创建带日期后缀的目录
        output_dir = f"interview_md_{post}_{date_suffix}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存每个公司的面试数据
        for company, interviews in company_data.items():
            # 按时间排序面试数据
            sorted_interviews = sorted(interviews, key=lambda x: x['edit_time'], reverse=True)
            filename = os.path.join(output_dir, f"{company}.md")
            
            with open(filename, 'w', encoding='utf-8') as f:
                for interview in sorted_interviews:
                    f.write(f"# {interview['title']}\n\n")
                    f.write(f"**职位/公司**: {interview['post']}, {interview['company']}\n\n")
                    f.write(f"**面试时间**: {interview['edit_time']}\n\n")
                    f.write(f"**面试内容**:\n{interview['content']}\n\n")
                    f.write("---\n\n")  # 添加分隔符

def save_all_interviews():
    """
    保存所有面试数据到markdown文件，按post分类保存到不同目录
    """
    print("开始获取所有面试数据...")
    data = fetch_interview_data()
    print(f"获取到 {len(data)} 条面试数据")
    
    save_to_markdown(data)
    
    # 打印保存的文件夹和文件列表
    date_suffix = datetime.now().strftime("%Y%m%d")
    print("\n生成的文件列表：")
    for post in ['前端', '后端']:  # 可能的post类型
        output_dir = f"interview_md_{post}_{date_suffix}"
        if os.path.exists(output_dir):
            print(f"\n{output_dir}目录：")
            for file in os.listdir(output_dir):
                print(f"- {file}")

def test_save_markdown():
    """
    测试函数：只获取少量数据进行测试
    """
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 只获取100条数据进行测试
        cursor.execute("SELECT title, content, edit_time, post, company FROM niuke LIMIT 100")
        test_data = cursor.fetchall()
        
        print(f"获取到 {len(test_data)} 条测试数据")
        save_to_markdown(test_data)
        
        # 打印保存的文件列表
        date_suffix = datetime.now().strftime("%Y%m%d")
        print("\n生成的文件列表：")
        for post in ['前端', '后端']:
            output_dir = f"interview_md_{post}_{date_suffix}"
            if os.path.exists(output_dir):
                print(f"\n{output_dir}目录：")
                for file in os.listdir(output_dir):
                    print(f"- {file}")
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # test_save_markdown()  # 注释掉测试函数
    save_all_interviews()  # 保存所有数据
