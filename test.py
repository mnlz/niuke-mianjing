import requests
from datetime import datetime
import re
import mysql.connector
import time
import json
from get_info import extract_company_post

# 获取当前时间的毫秒级时间戳
timestamp = int(time.time() * 1000)



headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "origin": "https://www.nowcoder.com",
    "priority": "u=1, i",
    "referer": "https://www.nowcoder.com/",
    "sec-ch-ua": "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Microsoft Edge\";v=\"128\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}
cookies = {
    "NOWCODERUID": "79CF5DA56D034CD63E4FA1BD571129D4",
    "NOWCODERCLINETID": "41358A50185AFEA32695823EA2494A89",
    "gr_user_id": "ab4a81e0-992e-4e12-8956-1c56fa8f6e02",
    "t": "0711EE6F4D7F6C7CF0B7B3CAA263617C",
    "c196c3667d214851b11233f5c17f99d5_gr_last_sent_cs1": "290269641",
    "username": "%E8%90%8C%E9%92%A0%E7%B2%92%E9%B2%A8",
    "username.sig": "XQkfrLqPGY6xXZL2dF8yDzPZUqBQmVJhyIcoHlsVdew",
    "uid": "290269641",
    "uid.sig": "Qpi1npE2EV0HUDIhcRASWFM8ElZJ2rUHkMX8h0JwIP4",
    "isAgreementChecked": "true",
    "Hm_lvt_a808a1326b6c06c437de769d1b85b870": "1724997286,1725017782,1725020127,1725108047",
    "HMACCOUNT": "14C004ECB6B70208",
    "c196c3667d214851b11233f5c17f99d5_gr_session_id": "fed87fbb-6aeb-4426-a4aa-42b58d59c090",
    "c196c3667d214851b11233f5c17f99d5_gr_last_sent_sid_with_cs1": "fed87fbb-6aeb-4426-a4aa-42b58d59c090",
    "c196c3667d214851b11233f5c17f99d5_gr_session_id_fed87fbb-6aeb-4426-a4aa-42b58d59c090": "true",
    "acw_tc": "e1ff911afa64e341d6eb9bdb8135223a053d4abc3d1b0b45d6211e716b5e886f",
    "displayStyle": "h5",
    "c196c3667d214851b11233f5c17f99d5_gr_cs1": "290269641",
    "Hm_lpvt_a808a1326b6c06c437de769d1b85b870": "1725108528"
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
        post = info.get("post")
        # 格式化时间戳
        endTime_timestamp = source_data.get("editTime")
        endTime_formatted = datetime.fromtimestamp(endTime_timestamp / 1000.0).strftime(
            "%Y-%m-%d %H:%M:%S") if endTime_timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 添加有效内容记录
        if content != "暂无面经内容":
            record_data = {"title": title, "content": content, "endTime": endTime_formatted,"post":post,"company":company}
            data_to_save.append(record_data)

    return data_to_save

def get_page_data(response):
    page_data = response.json().get("data", {})
    total = page_data.get("total")
    totalPage = page_data.get("totalPage")
    return {"total" : total , "totalPage" : totalPage}

def get_total_pages(db_connection):
    cursor = db_connection.cursor()
    try:
        # 构建查询语句
        query = "SELECT totalPage,total FROM `update` ORDER BY `time` DESC LIMIT 1"
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


def get_record(db_connection):
    cursor = db_connection.cursor()
    try:
        # 构建查询语句
        query = "SELECT id, title, content, edit_time FROM `niuke` WHERE `read` = 0 ORDER BY edit_time DESC LIMIT 1;"
        # 执行查询
        cursor.execute(query)
        # 获取查询结果
        result = cursor.fetchone()

        if result:
            record_id = result[0]
            # 更新数据库，将该记录的 read 字段设置为 1
            update_query = "UPDATE `niuke` SET `read` = 1 WHERE `id` = %s;"
            cursor.execute(update_query, (record_id,))
            db_connection.commit()  # 提交更改

            return {"id": result[0], "title": result[1], "content": result[2]}
        else:
            return None  # 如果没有找到匹配的记录，返回 None
    finally:
        # 关闭游标和数据库连接
        cursor.close()


def save_content_data(db_connection,data_to_save):
    cursor = db_connection.cursor()
    # 将字典内容保存到MySQL数据库
    for record_data in data_to_save:
        status = 0
        # 构建插入数据的SQL语句
        sql = "INSERT INTO niuke (title, content, edit_time, post, company, status) VALUES (%s, %s, %s, %s, %s, %s)"
        if record_data['company'] !='未知公司':
            status = 1
        values = (record_data["title"], record_data["content"], record_data["endTime"], record_data["post"], record_data["company"], status)
        # 执行插入操作
        cursor.execute(sql, values)
    cursor.close()
    db_connection.commit()

def save_page_data(db_connection,page_to_save):
    cursor = db_connection.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "INSERT INTO `update` (`time`, `totalPage`,`total`) VALUES (%s, %s,%s)"
    values = (now, page_to_save['totalPage'], page_to_save['total'])
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

def update_records(cnx):
    cursor = cnx.cursor()
    try:
        # 查询数据库中所有满足 status=0 的记录
        query = "SELECT id, title FROM `niuke` WHERE `status` = 0;"
        cursor.execute(query)
        results = cursor.fetchall()

        for result in results:
            record_id = result[0]
            title = result[1]
            extracted_data = extract_company_post(title)

            if extracted_data['company'] != '未知公司':
                # 更新数据库，将该记录的 company 和 post 字段更新
                update_query = "UPDATE `niuke` SET `company` = %s, `post` = %s, `status` = 1 WHERE `id` = %s;"
                cursor.execute(update_query, (extracted_data['company'], extracted_data['post'], record_id))
                cnx.commit()  # 提交更改
                print("id:{},更新完毕,公司名称：{}".format(record_id,extracted_data['company']))

    finally:
        # 关闭游标和数据库连接
        cursor.close()

def export_titles_to_json(cnx):
    cursor = cnx.cursor()
    try:
        # 查询所有 title 字段
        query = "SELECT title FROM `niuke`;"
        cursor.execute(query)
        titles = [row[0] for row in cursor.fetchall()]

        # 将结果写入 JSON 文件
        with open('title.json', 'w', encoding='utf-8') as file:
            json.dump(titles, file, ensure_ascii=False, indent=4)

    finally:
        cursor.close()



if __name__ == '__main__':
    # db_remote_conn = mysql.connector.connect(
    #     host="116.198.250.133",
    #     user="root",
    #     password="123456",
    #     database="mianjing",
    #     charset="utf8mb4"
    # )
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
    page_sql_data = get_total_pages(db_localhost_conn)
    page_online_data = get_page_data(response)
    old_totalPage = page_sql_data['totalPage'] # 373
    new_totalPage = page_online_data['totalPage'] # 416
    update_page = new_totalPage - old_totalPage
    if update_page != 0:
        for i in range(1,update_page+1):
            response_ = get_onlieText(get_params(i))
            # 获得解析之后的数据，保存到数据库中
            data_to_save = get_content(response_)
            # 远程数据库
            # save_content_data(db_remote_conn,data_to_save)
            # 本地数据库
            save_content_data(db_localhost_conn,data_to_save)
            # 保存到txt中
            save_text(data_to_save)
            # 打印保存的信息
            print("第{}页保存完毕，保存内容为:{}".format(i,data_to_save))
        # 保存最新的页码
        # save_page_data(db_remote_conn,page_online_data)
        save_page_data(db_localhost_conn,page_online_data)


