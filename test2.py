import time

import requests
from datetime import datetime
import mysql.connector

"""
pip install mysql-connector-python
"""

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
pageT = 0
def get_result(totalPage_old):
    global pageT
    url = "https://gw-c.nowcoder.com/api/sparta/home/tab/content"
    params = {
        "pageNo": "1",
        "categoryType": "1",
        "tabId": "818",
        "_": "1725108538170"
    }

    response = requests.get(url, headers=headers, cookies=cookies, params=params)
    reponse_json = response.json()
    totalPage = reponse_json.get("data", {}).get("totalPage")
    print(totalPage)
    pageT = totalPage_old
    updates = totalPage - totalPage_old
    data_to_save = []
    # 获取当前时间戳（以秒为单位），然后乘以1000转换为毫秒
    timestamp = int(time.time() * 1000)
    if updates > 0:
        pageT = totalPage
        for i in range(1,updates+1):
            print(i)
            params = {
                "pageNo": f"{i}",
                "categoryType": "2",
                "tabId": "818",
                "_": f"{timestamp}"
            }
            response = requests.get(url, headers=headers, cookies=cookies, params=params)
            reponse_json = response.json()
            records = reponse_json.get("data", {}).get("records", [])
            for record in records:
                momentData = record.get('momentData', {})
                # 使用 get() 处理缺失的键
                title = momentData.get("title", "N/A")
                content = momentData.get("content", "N/A")
                endTime_timestamp = momentData.get("editTime", None)

                # 检查是否存在endTime字段
                if endTime_timestamp is not None:
                    # 将时间戳转换为日期
                    endTime_datetime = datetime.fromtimestamp(endTime_timestamp / 1000.0)
                    # 格式化日期，这里使用了默认格式 "%Y-%m-%d %H:%M:%S"
                    endTime_formatted = endTime_datetime.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    # 使用当前日期作为默认值
                    endTime_datetime = datetime.now()
                    endTime_formatted = endTime_datetime.strftime("%Y-%m-%d %H:%M:%S")
                if content !="N/A":
                    record_data = {"title": title, "content": content, "endTime": endTime_formatted}
                    data_to_save.append(record_data)
                    print(title, content, endTime_formatted)
    else:
        print("今天没有更新")
        return data_to_save

    # 将字典内容保存到txt文件
    with open("面经.txt", "a", encoding="utf-8") as file:
        for record_data in data_to_save:
            # 只处理有内容的content字段
            if record_data["content"]:
                # 将字段写入文件
                file.write(f"{record_data['title']}\n{record_data['content']}\n{record_data['endTime']}\n\n")
    return data_to_save

def save_mysql(db_connection,data_to_save):
    global pageT
    # Create a cursor object to interact with the database
    cursor = db_connection.cursor()
    # 将字典内容保存到MySQL数据库
    for record_data in data_to_save:
        # 构建插入数据的SQL语句
        sql = "INSERT INTO niuke (title, content, edit_time) VALUES (%s, %s, %s)"
        values = (record_data["title"], record_data["content"], record_data["endTime"])

        # 执行插入操作
        cursor.execute(sql, values)

    # Commit the changes to the database
    db_connection.commit()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "INSERT INTO `update` (`time`, `totalPage`) VALUES (%s, %s)"
    values = (now, pageT)
    cursor.execute(sql, values)
    cursor.close()
    db_connection.commit()


def get_total_pages(db_connection):
    cursor = db_connection.cursor()
    try:
        # 构建查询语句
        query = "SELECT MAX(totalPage) FROM `update`"

        # 执行查询
        cursor.execute(query)

        # 获取查询结果
        result = cursor.fetchone()

        if result:
            return result[0]  # 返回查询到的 title 值
        else:
            return None  # 如果没有找到匹配的记录，返回 None

    finally:
        # 关闭游标和数据库连接
        cursor.close()




if __name__ == '__main__':
    # Establish a MySQL connection
    #https://blog.csdn.net/qq_41906934/article/details/112285015
    db_connection = mysql.connector.connect(
        host="116.198.250.133",
        user="root",
        password="root123456",
        database="mianjing",
        charset="utf8mb4"
    )
    #通过数据库查询最新的总页数
    totalPage_old = get_total_pages(db_connection)
    # #根据最新的总页数来判断是否要更新
    data_to_save = get_result(totalPage_old)
    if data_to_save !=[]:
         save_mysql(db_connection, data_to_save)

    db_connection.close()


"""
CREATE TABLE `niuke` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `content` text COLLATE utf8mb4_unicode_ci,
  `edit_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=75 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

CREATE TABLE `update` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `time` datetime DEFAULT NULL,
  `totalPage` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

"""