import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup

from niuke_mianjing_backend.config import get_proxy_config, settings
from niuke_mianjing_backend.crawler.feishu_bot import FeishuBot
from niuke_mianjing_backend.repositories.crawl_log_repo import CrawlLogRepository
from niuke_mianjing_backend.repositories.niuke_repo import NiukeRepository
from niuke_mianjing_backend.schemas.ws import WSMessageType
from niuke_mianjing_backend.services.event_bus import EventBus
from niuke_mianjing_backend.utils.extractor import extract_company_post
from niuke_mianjing_backend.utils.job_map import get_job_id


HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "content-type": "application/json",
    "origin": "https://www.nowcoder.com",
    "priority": "u=1, i",
    "referer": "https://www.nowcoder.com/",
    "sec-ch-ua": '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}

LIST_URL = "https://gw-c.nowcoder.com/api/sparta/job-experience/experience/job/list"
DETAIL_URL = "https://gw-c.nowcoder.com/api/sparta/detail/content-data/detail"
NO_CONTENT = "暂无面经内容"


class CrawlService:
    def __init__(self, feishu_webhook: str = None):
        self.niuke_repo = NiukeRepository()
        self.log_repo = CrawlLogRepository()
        self.event_bus = EventBus()
        self.feishu_bot = FeishuBot(feishu_webhook) if feishu_webhook else None
        self.proxies = get_proxy_config()
        self._running_posts = set()

    def _build_list_payload(self, job_id: int, page: int, level: int = 2, order: int = 3) -> str:
        body = {
            "companyList": [],
            "jobId": job_id,
            "level": level,
            "order": order,
            "page": page,
            "isNewJob": True,
        }
        return json.dumps(body, separators=(",", ":"))

    def _fetch_list_page(self, job_id: int, page: int, level: int = 2, order: int = 3):
        params = {"_": str(int(time.time() * 1000))}
        data = self._build_list_payload(job_id, page, level, order)
        return requests.post(LIST_URL, headers=HEADERS, params=params, data=data, proxies=self.proxies, timeout=30)

    def _get_long_content(self, content_id: str) -> str:
        url = f"{DETAIL_URL}/{content_id}"
        response = requests.get(url, headers=HEADERS, proxies=self.proxies, timeout=30)
        data = response.json().get("data")
        if data is not None:
            html_content = data.get("content", NO_CONTENT)
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text()
        return NO_CONTENT

    @staticmethod
    def _strip_html_tags(text: str) -> str:
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text()

    def _parse_content(self, response, post: str) -> List[Dict]:
        data_to_save = []
        records = response.json().get("data", {}).get("records", [])
        for record in records:
            source = record.get("momentData") or record.get("contentData")
            content_id = record.get("contentId")
            if not source:
                continue

            title = source.get("title", "无标题")
            if len(str(content_id)) == 7:
                content = self._strip_html_tags(source.get("content", NO_CONTENT))
            else:
                content = self._get_long_content(content_id)

            company = extract_company_post(title)
            end_ts = source.get("editTime")
            end_time = (
                datetime.fromtimestamp(end_ts / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
                if end_ts
                else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            if content != NO_CONTENT:
                data_to_save.append(
                    {
                        "title": title,
                        "content": content,
                        "endTime": end_time,
                        "post": post,
                        "company": company,
                        "contentId": content_id,
                    }
                )
        return data_to_save

    @staticmethod
    def _get_page_data(response) -> dict:
        data = response.json().get("data", {})
        return {"total": data.get("total"), "totalPage": data.get("totalPage")}

    async def crawl_post(self, post: str, max_pages: int = 15) -> Dict:
        start_time = datetime.now()
        print(f"\n===== 开始抓取【{post}】面经 =====")

        await self.event_bus.publish(
            WSMessageType.CRAWL_START,
            {"post": post, "max_pages": max_pages},
            f"开始爬取【{post}】",
        )

        job_id = get_job_id(post)
        if not job_id:
            msg = f"未找到 {post} 对应的 jobId，请检查方向名称"
            print(msg)
            await self.event_bus.publish(WSMessageType.CRAWL_ERROR, {"post": post, "error": msg}, msg)
            return {"new": 0, "updated": 0, "status": "failed", "error": msg}

        if post in self._running_posts:
            msg = f"{post} 方向已有爬取任务正在执行"
            await self.event_bus.publish(WSMessageType.CRAWL_ERROR, {"post": post, "error": msg}, msg)
            return {"new": 0, "updated": 0, "status": "skipped", "error": msg}
        self._running_posts.add(post)

        try:
            resp = await asyncio.to_thread(self._fetch_list_page, job_id, 1, 2, 3)
            online = await asyncio.to_thread(self._get_page_data, resp)

            total_new = 0
            total_updated = 0

            for i in range(1, max_pages + 1):
                r = await asyncio.to_thread(self._fetch_list_page, job_id, i, 2, 3)
                data = await asyncio.to_thread(self._parse_content, r, post)
                result = await self.niuke_repo.upsert_content(data)
                new_count = result["new"]
                updated_count = result["updated"]
                total_new += new_count
                total_updated += updated_count
                print(f"第 {i} 页保存完成，共 {len(data)} 条记录（新增 {new_count}，更新 {updated_count}）")

                await self.event_bus.publish(
                    WSMessageType.CRAWL_PAGE_DONE,
                    {
                        "post": post,
                        "page": i,
                        "total_pages": max_pages,
                        "new_count": new_count,
                        "updated_count": updated_count,
                    },
                    f"【{post}】第 {i}/{max_pages} 页完成",
                )

                await asyncio.sleep(settings.SLEEP_INTERVAL)

            await self.niuke_repo.save_page_data(online, post)

            end_time = datetime.now()
            await self.log_repo.add_log(post, start_time, end_time, max_pages, total_new, total_updated, "success")

            print(f"【{post}】方向抓取完成：新增 {total_new} 条，更新 {total_updated} 条")

            if self.feishu_bot:
                self.feishu_bot.send_crawl_summary(post, total_new, total_updated, "success")

            await self.event_bus.publish(
                WSMessageType.CRAWL_POST_DONE,
                {"post": post, "new_count": total_new, "updated_count": total_updated, "status": "success"},
                f"【{post}】爬取完成：新增 {total_new}，更新 {total_updated}",
            )

            return {"new": total_new, "updated": total_updated, "status": "success"}

        except Exception as e:
            end_time = datetime.now()
            error_msg = str(e)
            print(f"【{post}】方向抓取失败：{error_msg}")

            await self.log_repo.add_log(post, start_time, end_time, 0, 0, 0, "failed", error_msg)

            if self.feishu_bot:
                self.feishu_bot.send_crawl_summary(post, 0, 0, "failed", error_msg)

            await self.event_bus.publish(
                WSMessageType.CRAWL_POST_DONE,
                {"post": post, "new_count": 0, "updated_count": 0, "status": "failed", "error": error_msg},
                f"【{post}】爬取失败：{error_msg}",
            )

            return {"new": 0, "updated": 0, "status": "failed", "error": error_msg}
        finally:
            self._running_posts.discard(post)

    async def crawl_all(self, post_list: List[str], max_pages: int = 15) -> List[Dict]:
        summary = []
        for post in post_list:
            result = await self.crawl_post(post, max_pages)
            summary.append({"post": post, "new": result["new"], "updated": result["updated"]})

        print("\n开始清理重复和空数据...")
        await self.niuke_repo.clean_duplicates_and_empty()

        if self.feishu_bot:
            self.feishu_bot.send_daily_report(summary)

        await self.event_bus.publish(
            WSMessageType.CRAWL_ALL_DONE,
            {"summary": summary},
            "所有方向爬取完成",
        )

        return summary
