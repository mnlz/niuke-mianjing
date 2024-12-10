import mysql.connector
from trie_classifier import TrieClassifier

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

# 创建全局的分类器实例
classifier = TrieClassifier('keywords.json')

def categorize_question(question):
    """
    对单个问题进行分类
    返回最多两个最匹配的类别，用英文逗号隔开
    """
    categories, _ = classifier.search(question)
    if not categories or categories == ["未知"]:
        return "其他"
    elif len(categories) == 1:
        return categories[0]
    else:
        return ",".join(categories[:2])  # 最多返回两个类别，用逗号隔开

def update_categories(batch_size=5000):
    """
    更新数据库中的问题分类，每次处理指定数量的记录
    Args:
        batch_size: 每批处理的记录数量
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取总记录数
        cursor.execute("SELECT COUNT(*) as total FROM questions WHERE category = '其他'")
        total_count = cursor.fetchone()['total']
        print(f"总共找到 {total_count} 个待分类的问题")
        
        # 更新计数器
        categories_count = {}
        processed_count = 0
        
        while processed_count < total_count:
            # 获取一批数据
            cursor.execute(
                "SELECT id, question FROM questions WHERE category = '其他' LIMIT %s OFFSET %s",
                (batch_size, processed_count)
            )
            questions = cursor.fetchall()
            
            if not questions:  # 如果没有更多数据了就退出
                break
            
            # 处理这一批数据
            for question_data in questions:
                category = categorize_question(question_data['question'])
                
                # 更新问题分类
                update_query = "UPDATE questions SET category = %s WHERE id = %s"
                cursor.execute(update_query, (category, question_data['id']))
                
                # 更新计数
                categories_count[category] = categories_count.get(category, 0) + 1
            
            # 提交这一批的更改
            conn.commit()
            processed_count += len(questions)
            print(f"已处理 {processed_count}/{total_count} 个问题 ({(processed_count/total_count*100):.2f}%)")
            
            # 打印当前批次的分类统计
            print("\n当前分类统计:")
            print("-" * 40)
            for category, count in categories_count.items():
                print(f"{category}: {count} 个问题")
            print("-" * 40)
        
        print("\n全部处理完成!")
        
    except Exception as e:
        print(f"更新分类时出错: {e}")
        conn.rollback()
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def test_categorization(num_samples=5):
    """测试分类效果"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 随机获取一些问题进行测试
        cursor.execute("SELECT question FROM questions ORDER BY RAND() LIMIT %s", (num_samples,))
        questions = cursor.fetchall()
        
        print(f"\n测试 {num_samples} 个随机问题的分类效果:")
        print("-" * 60)
        
        for q in questions:
            question = q['question']
            print(f"\n问题: {question}")
            
            # 获取分类和匹配详情
            categories, matched_keywords = classifier.search(question)
            category = categories[0] if not categories or categories == ["未知"] else ",".join(categories[:2])
            
            # 打印匹配详情
            print("\n匹配详情:")
            for cat, keywords in matched_keywords.items():
                print(f"{cat}: 匹配到的关键词 {keywords}")
                print(f"  - 匹配数量: {len(keywords)}")
                print(f"  - 关键词总长度: {sum(len(keyword) for keyword in keywords)}")
            
            # 打印最终分类
            print(f"\n最终分类: {category}")
            
    except Exception as e:
        print(f"测试分类时出错: {e}")
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # 先测试分类效果
    print("=== 测试分类效果 ===")
    # test_categorization(5)
    
    # 确认是否继续
    response = input("\n要开始更新所有问题的分类吗？(y/n): ")
    if response.lower() == 'y':
        print("\n=== 开始更新问题分类 ===")
        update_categories()
        print("\n=== 分类更新完成 ===")
