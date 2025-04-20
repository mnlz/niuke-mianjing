import mysql.connector
import pandas as pd

# 定义公司名称映射关系，格式为 "标准公司名": ["别称1", "别称2", ...]
company_aliases = {
    "阿里巴巴": ["阿里", "淘天"],
    
    "腾讯": ["企业微信", "腾讯广告", "WX", "微信", "微众银行", "腾讯游戏"],
    
    "百度": ["度小满", "文心"],
    
    "字节跳动": ["字节", "抖音", "飞书", "TikTok", "今日头条"],
    
    "美团": ["美团点评", "大众点评"],
    
    "京东": ["JD", "京东科技",'jd'],
    
    "华为": ["Huawei", "HW", "华为终端", "华为云"],
    
    "小米": ["米家", "MIUI"],
    
    "拼多多": ["pdd", "PDD", "拼夕夕"],
    
    "哔哩哔哩": ["b站", "bilibili"],
    
    "网易": ["网易游戏", "网易雷火"],
    
    "TP-Link": ["TpLink", "TP-Link普联", "tp"],
    
    "58同城": ["同城"],
    
    "虾皮": ["Shopee","shopee"],
    
    "蚂蚁集团": ["蚂蚁", "支付宝"],
    
    "招商银行": ["招银", "招银网络科技", "招联"],
    
    "中国移动": ["移动"],
    
    "中国电信": ["电信", "天翼"],
    
    "中国联通": ["联通", "联通数科"],
    
    "科大讯飞": ["讯飞"],
    
    "理想汽车": ["理想"],
    
    "Meta": ["meta"],
    
    "未知公司": ["某公司", "某厂", "小公司", "小厂", "广州小公司", "\\N"]
}

# 创建反向映射字典，从别称到标准名称
reverse_mapping = {}
for standard_name, aliases in company_aliases.items():
    for alias in aliases:
        reverse_mapping[alias] = standard_name

def connect_to_db():
    """连接到数据库"""
    try:
        conn = mysql.connector.connect(
            host="116.198.250.133",
            port=13306,  # 添加Docker映射的端口
            user="root",
            password="123456",
            database="mianjing",
            charset="utf8mb4"
        )
        # conn = mysql.connector.connect(
        #     host="localhost",
        #     port=3306,  # 添加Docker映射的端口
        #     user="root",
        #     password="123456",
        #     database="mianjing",
        #     charset="utf8mb4"
        # )

        print("数据库连接成功")
        return conn
    except mysql.connector.Error as err:
        print(f"数据库连接失败: {err}")
        return None

def get_all_companies(conn):
    """获取数据库中所有的公司名称"""
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT company FROM niuke")
    companies = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return companies

def update_company_names(conn, mapping):
    """更新数据库中的公司名称"""
    cursor = conn.cursor()
    
    # 获取所有公司名称
    companies = get_all_companies(conn)
    
    # 统计更新数量
    update_count = 0
    
    # 遍历所有公司名称
    for company in companies:
        # 如果公司名称在映射中，则更新
        if company in mapping:
            standard_name = mapping[company]
            
            # 如果标准名称与原名称不同，则更新
            if standard_name != company:
                sql = "UPDATE niuke SET company = %s WHERE company = %s"
                cursor.execute(sql, (standard_name, company))
                affected_rows = cursor.rowcount
                update_count += affected_rows
                print(f"将 '{company}' 更新为 '{standard_name}', 更新了 {affected_rows} 条记录")
    
    # 提交更改
    conn.commit()
    cursor.close()
    
    return update_count

def main():
    # 连接到数据库
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        # 获取数据库中所有公司名称
        all_companies = get_all_companies(conn)
        print(f"数据库中共有 {len(all_companies)} 个不同的公司名称")
        
        # 更新公司名称
        update_count = update_company_names(conn, reverse_mapping)
        print(f"共更新了 {update_count} 条记录的公司名称")
        
        # 获取更新后的所有公司名称
        updated_companies = get_all_companies(conn)
        print(f"更新后数据库中共有 {len(updated_companies)} 个不同的公司名称")
        
    finally:
        # 关闭数据库连接
        conn.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    main()
