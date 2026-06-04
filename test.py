import requests
import json


headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "content-type": "application/json",
    "origin": "https://www.nowcoder.com",
    "priority": "u=1, i",
    "referer": "https://www.nowcoder.com/",
    "sec-ch-ua": "\"Chromium\";v=\"148\", \"Microsoft Edge\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}

url = "https://gw-c.nowcoder.com/api/sparta/job-experience/experience/job/list"
params = {
    "_": "1780210902580"
}
data = {
    "companyList": [],
    "jobId": 11202, # job_id
    "level": 2,
    "order": 3,# 排序是最新
    "page": 5,
    "isNewJob": True
}
data = json.dumps(data, separators=(',', ':'))
proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}
response = requests.post(url, headers=headers, params=params, data=data, proxies=proxies)

print(response.text)
print(response)
content_id = "876488628204027904"
url = f"https://gw-c.nowcoder.com/api/sparta/detail/content-data/detail/{content_id}"
response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
print(response.text)
print(response)

