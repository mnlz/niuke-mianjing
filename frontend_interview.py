import requests
from datetime import datetime
import re
import mysql.connector
import time
from get_info import extract_company_post
from clean_data import clean_duplicate_and_empty_data

# 获取当前时间的毫秒级时间戳
timestamp = int(time.time() * 1000)

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "origin": "https://www.nowcoder.com",
    "priority": "u=1, i",
    "referer": "https://www.nowcoder.com/",
    "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Microsoft Edge\";v=\"134\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}
cookies = {
    "gr_user_id": "6ab87d03-a9ce-413e-b345-308a6382137c",
    "Hm_lvt_a808a1326b6c06c437de769d1b85b870": "1743597767",
    "HMACCOUNT": "75A0074A9AC42EDC",
    "NOWCODERCLINETID": "2E4D3C48D7DC993D451515C64957254B",
    "NOWCODERUID": "6d6c3a2100bc4a65888622a07c7553f0",
    "acw_tc": "e0ad5c6e983b81ac3e2cb0548cf41de5fec7b1b7111ce3f29a614f90b5b5d9c1",
    "isAgreementChecked": "true",
    "t": "9094A79B0BA2A635722D1841620E525E",
    "c196c3667d214851b11233f5c17f99d5_gr_last_sent_sid_with_cs1": "09817570-4114-442e-8d2b-4661052d8864",
    "c196c3667d214851b11233f5c17f99d5_gr_last_sent_cs1": "290269641",
    "c196c3667d214851b11233f5c17f99d5_gr_cs1": "290269641",
    "c196c3667d214851b11233f5c17f99d5_gr_session_id": "09817570-4114-442e-8d2b-4661052d8864",
    "c196c3667d214851b11233f5c17f99d5_gr_session_id_09817570-4114-442e-8d2b-4661052d8864": "true"
}
url = "https://gw-c.nowcoder.com/api/sparta/home/tab/content"


def get_params(pageNo):
    params = {
        "pageNo": f"{pageNo}",
        "categoryType": "1",
        "tabId": "818",
        "_": f"{timestamp}"
    }
    return params


def get_onlieText(params):
    response = requests.get(url, headers=headers, cookies=cookies, params=params)
    print(response.text)
    return response


def strip_html_tags(text):
    return re.sub(r'<[^>]+>', '', text)


def get_content(response):
    data_to_save = []
    records = response.json().get("data", {}).get("records", [])

    for record in records:
        # 优先从 momentData 提取数据；如果 momentData 为空且 contentData 存在，则从 contentData 提取数据
        if record.get('momentData'):
            source_data = record['momentData']
        elif record.get('contentData'):
            source_data = record['contentData']
        else:
            continue  # 如果两个字段都为空，跳过当前记录

        title = source_data.get("title", "无标题字段")
        content = strip_html_tags(source_data.get("content", "暂无面经内容"))
        # 根据title提取post和company
        info = extract_company_post(title)
        company = info.get("company")
        post = "前端"
        # 格式化时间戳
        endTime_timestamp = source_data.get("editTime")
        endTime_formatted = datetime.fromtimestamp(endTime_timestamp / 1000.0).strftime(
            "%Y-%m-%d %H:%M:%S") if endTime_timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 添加有效内容记录
        if content != "暂无面经内容":
            record_data = {"title": title, "content": content, "endTime": endTime_formatted, "post": post,
                           "company": company}
            data_to_save.append(record_data)

    return data_to_save


def get_page_data(response):
    page_data = response.json().get("data", {})
    total = page_data.get("total")
    totalPage = page_data.get("totalPage")
    return {"total": total, "totalPage": totalPage}


def get_total_pages(db_connection):
    cursor = db_connection.cursor()
    try:
        # 构建查询语句
        query = "SELECT totalPage,total FROM `update` where post = '前端' ORDER BY `time` DESC LIMIT 1"
        # 执行查询
        cursor.execute(query)
        # 获取查询结果
        result = cursor.fetchone()
        if result:
            return {"total": result[1], "totalPage": result[0]}
        else:
            return None  # 如果没有找到匹配的记录，返回 None
    finally:
        # 关闭游标和数据库连接
        cursor.close()



def save_content_data(db_connection, data_to_save):
    cursor = db_connection.cursor()
    # 将字典内容保存到MySQL数据库
    for record_data in data_to_save:
        status = 0
        # 构建插入数据的SQL语句
        sql = "INSERT INTO niuke (title, content, edit_time, post, company, status) VALUES (%s, %s, %s, %s, %s, %s)"
        if record_data['company'] != '未知公司':
            status = 1
        values = (record_data["title"], record_data["content"], record_data["endTime"], record_data["post"],
                  record_data["company"], status)
        # 执行插入操作
        cursor.execute(sql, values)
    cursor.close()
    db_connection.commit()


def save_page_data(db_connection, page_to_save):
    cursor = db_connection.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "INSERT INTO `update` (`time`,`totalPage`,`total`,`post`) VALUES (%s, %s,%s,%s)"
    values = (now, page_to_save['totalPage'], page_to_save['total'], "前端")
    cursor.execute(sql, values)
    cursor.close()
    db_connection.commit()


def save_text(data_to_save):
    # 将字典内容保存到txt文件
    with open("面经-1.txt", "a", encoding="utf-8") as file:
        for record_data in data_to_save:
            # 只处理有内容的content字段
            if record_data["content"]:
                # 将字段写入文件
                file.write(f"{record_data['title']}\n{record_data['content']}\n{record_data['endTime']}\n\n")






if __name__ == '__main__':
    db_remote_conn = mysql.connector.connect(
        host="116.198.250.133",
        port=13306,  # 添加Docker映射的端口
        user="root",
        password="123456",
        database="mianjing",
        charset="utf8mb4"
    )
    db_localhost_conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="123456",
        database="mianjing",
        charset="utf8mb4"
    )

    # 先发出请求获取最新的totalpage
    params = get_params(1)
    response = get_onlieText(params)
    # page_sql_data = get_total_pages(db_remote_conn)
    page_size = 20
    page_sql_data = get_total_pages(db_localhost_conn)
    page_online_data = get_page_data(response)
    old_totalPage = page_sql_data['totalPage']  # 100
    old_total = page_sql_data['total'] #2000
    new_totalPage = page_online_data['totalPage']  # 219
    new_total = page_online_data['total'] #4366
    update_page = new_totalPage - old_totalPage
    update_total = new_total - old_total
    update_count = int(update_total / page_size) + 1
    print("需要更新的页数：{}".format(update_count))
    if update_total != 0:
        for i in range(1, update_count + 4):
            response_ = get_onlieText(get_params(i))
            # 获得解析之后的数据，保存到数据库中
            data_to_save = get_content(response_)
            # 远程数据库
            save_content_data(db_remote_conn, data_to_save)
            # 本地数据库
            save_content_data(db_localhost_conn, data_to_save)
            # 保存到txt中
            save_text(data_to_save)
            # 打印保存的信息
            print("第{}页保存完毕，保存内容为:{}".format(i, data_to_save))
        # 保存最新的页码 本地和远程
        save_page_data(db_remote_conn, page_online_data)
        save_page_data(db_localhost_conn, page_online_data)

    # 清理重复和空数据
    print("\n开始清理数据...")
    clean_duplicate_and_empty_data(db_localhost_conn)
    clean_duplicate_and_empty_data(db_remote_conn)
