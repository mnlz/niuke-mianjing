import requests
import json
from datetime import datetime


class FeishuBot:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url

    def send_text(self, content: str) -> bool:
        if not self.webhook_url:
            return False
        data = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        return self._send(data)

    def send_post(self, title: str, content: list) -> bool:
        if not self.webhook_url:
            return False
        data = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": content
                    }
                }
            }
        }
        return self._send(data)

    def send_interactive(self, card: dict) -> bool:
        if not self.webhook_url:
            return False
        data = {
            "msg_type": "interactive",
            "card": card
        }
        return self._send(data)

    def _send(self, data: dict) -> bool:
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.webhook_url, headers=headers, 
                                    data=json.dumps(data), timeout=10)
            result = response.json()
            
            if result.get("StatusCode") == 0 or result.get("code") == 0:
                return True
            else:
                print(f"飞书发送失败: {result}")
                return False
        except Exception as e:
            print(f"飞书发送异常: {e}")
            return False

    def send_crawl_summary(self, post: str, new_records: int, 
                          updated_records: int, status: str, 
                          error_msg: str = None) -> bool:
        if not self.webhook_url:
            return False
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        title = f"📊 牛客面经爬取通知 - {post}"
        
        content = [
            [{"tag": "text", "text": f"⏰ 爬取时间: {now}"}],
            [{"tag": "text", "text": f"🎯 爬取方向: {post}"}],
            [{"tag": "text", "text": f"✅ 新增记录: {new_records} 条"}],
            [{"tag": "text", "text": f"🔄 更新记录: {updated_records} 条"}],
        ]
        
        if status == "success":
            content.append([{"tag": "text", "text": f"🎉 状态: 爬取成功"}])
        elif status == "failed":
            content.append([{"tag": "text", "text": f"❌ 状态: 爬取失败"}])
            if error_msg:
                content.append([{"tag": "text", "text": f"⚠️ 错误: {error_msg}"}])
        else:
            content.append([{"tag": "text", "text": f"⚠️ 状态: 部分成功"}])
        
        return self.send_post(title, content)

    def send_daily_report(self, summary_data: list) -> bool:
        if not self.webhook_url:
            return False
        
        title = "📈 牛客面经每日爬取报告"
        
        content = [
            [{"tag": "text", "text": f"📅 日期: {datetime.now().strftime('%Y-%m-%d')}"}],
            [{"tag": "text", "text": ""}],
        ]
        
        total_new = 0
        total_updated = 0
        
        for item in summary_data:
            content.append([{"tag": "text", "text": f"🎯 {item['post']}:"}])
            content.append([{"tag": "text", "text": f"   新增: {item['new']} 条, 更新: {item['updated']} 条"}])
            total_new += item['new']
            total_updated += item['updated']
        
        content.append([{"tag": "text", "text": ""}])
        content.append([{"tag": "text", "text": f"📊 今日总计: 新增 {total_new} 条, 更新 {total_updated} 条"}])
        
        return self.send_post(title, content)

    def send_error_alert(self, error_type: str, error_msg: str) -> bool:
        if not self.webhook_url:
            return False
        
        title = "🚨 爬虫系统异常告警"
        content = [
            [{"tag": "text", "text": f"❌ 异常类型: {error_type}"}],
            [{"tag": "text", "text": f"📝 错误信息: {error_msg}"}],
            [{"tag": "text", "text": f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}],
        ]
        return self.send_post(title, content)
