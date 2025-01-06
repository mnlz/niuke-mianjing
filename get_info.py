import json

def load_data_from_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def extract_company_post(title):
    # 从JSON文件加载公司和职位数据
    data = load_data_from_json('info.json')
    companies = data.get("companies", [])
    posts = data.get("posts", [])

    company = '未知公司'
    post = '后端'

    # 遍历公司列表以确定公司名称
    for comp in companies:
        if comp in title.lower():
            company = comp
            break

    # 根据关键词判断职位
    for pt in posts:
        if pt in title.lower():
            post = pt
            break

    return {
        'company': company,
        'post': post
    }

