import requests


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
params = {
    "pageNo": "1",
    "categoryType": "1",
    "tabId": "818",
    "_": "1725108538170"
}
response = requests.get(url, headers=headers, cookies=cookies, params=params)

print(response.text)
print(response)