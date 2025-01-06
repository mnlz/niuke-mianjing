import requests
import json


headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/json",
    "origin": "https://www.nowcoder.com",
    "priority": "u=1, i",
    "referer": "https://www.nowcoder.com/",
    "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}
cookies = {
    "NOWCODERUID": "AECF304345D01FF7AED30D13BF0346B7",
    "NOWCODERCLINETID": "67ECA5A75E02B8691AB9B71B14CAE890",
    "gr_user_id": "4c00fcb8-0a43-4435-a585-098f71fe24a6",
    "c196c3667d214851b11233f5c17f99d5_gr_session_id": "161de6a1-9078-48cd-b221-7c357ebfabcc",
    "c196c3667d214851b11233f5c17f99d5_gr_session_id_161de6a1-9078-48cd-b221-7c357ebfabcc": "true",
    "acw_tc": "4fc7ec760601a7cd81460c305dcaa32a1244aa1848ce7affcbc7765ac1f04c95",
    "Hm_lvt_a808a1326b6c06c437de769d1b85b870": "1736168206,1736168393,1736168569",
    "HMACCOUNT": "8EEE9D677193F82B",
    "isAgreementChecked": "true",
    "c196c3667d214851b11233f5c17f99d5_gr_last_sent_sid_with_cs1": "161de6a1-9078-48cd-b221-7c357ebfabcc",
    "c196c3667d214851b11233f5c17f99d5_gr_last_sent_cs1": "290269641",
    "Hm_lpvt_a808a1326b6c06c437de769d1b85b870": "1736168663"
}
url = "https://gw-c.nowcoder.com/api/sparta/job-experience/experience/job/list"
params = {
    "_": "1736168829529"
}
data = {
    "companyList": [],
    "jobId": 11201,
    "level": 2,
    "order": 3,
    "page": 100,
    "isNewJob": True
}
data = json.dumps(data, separators=(',', ':'))
response = requests.post(url, headers=headers, cookies=cookies, params=params, data=data)

print(response.text)
print(response)