import json
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from niuke_mianjing_backend.config import settings
from niuke_mianjing_backend.repositories.niuke_repo import NiukeRepository
from niuke_mianjing_backend.repositories.review_repo import ReviewRepository
from niuke_mianjing_backend.services.openai_client import extract_chat_completion_text, post_chat_completion


class ReviewService:
    def __init__(self):
        self.niuke_repo = NiukeRepository()
        self.review_repo = ReviewRepository()

    async def init_tables(self):
        await self.review_repo.init_tables()

    async def get_progress(self, user_id: int, record_ids: List[int]) -> List[Dict[str, Any]]:
        progress_map = await self.review_repo.get_progress_map(user_id, record_ids)
        return [progress_map.get(record_id, ReviewRepository.default_progress(record_id)) for record_id in record_ids]

    async def update_progress(
        self,
        user_id: int,
        record_id: int,
        favorite: Optional[bool] = None,
        mastery: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        if mastery and mastery not in {"new", "learning", "fuzzy", "mastered"}:
            raise ValueError("掌握状态不合法")
        return await self.review_repo.upsert_progress(user_id, record_id, favorite, mastery, note)

    async def build_overview(
        self,
        company: str,
        post: str,
        days: int = 30,
        limit: int = 80,
    ) -> Dict[str, Any]:
        start_time = datetime.now() - timedelta(days=days)
        records = await self.niuke_repo.get_records_for_analysis(
            company=company,
            post=post,
            limit=limit,
            start_time=start_time,
            order_by_time=True,
        )
        if not records:
            records = await self.niuke_repo.get_records_for_analysis(
                company=company,
                post=post,
                limit=min(limit, 30),
                order_by_time=False,
            )

        questions: List[str] = []
        for record in records:
            questions.extend(self._extract_questions(record.get("content") or ""))

        question_counter = Counter(self._normalize_question(question) for question in questions if question.strip())
        question_counter = Counter({question: count for question, count in question_counter.items() if len(question) >= 4})
        top_questions = [
            {
                "question": question,
                "count": count,
                "category": self._category(question),
            }
            for question, count in question_counter.most_common(12)
        ]
        category_counter = Counter(item["category"] for item in top_questions)

        return {
            "company": company,
            "post": post,
            "days": days,
            "record_count": len(records),
            "question_count": len(questions),
            "top_questions": top_questions,
            "categories": [{"name": name, "count": count} for name, count in category_counter.most_common()],
            "sample_records": [
                {
                    "id": record.get("id"),
                    "title": record.get("title"),
                    "edit_time": record.get("edit_time"),
                    "read": record.get("read"),
                }
                for record in records[:8]
            ],
            "empty": not records,
        }

    async def get_ai_review(self, record_id: int, refresh: bool = False) -> Dict[str, Any]:
        if not refresh:
            cached = await self.review_repo.get_ai_review(record_id)
            if cached:
                return {**cached, "cached": True}

        record = await self.niuke_repo.get_by_id(record_id)
        if not record:
            raise ValueError("面经记录不存在")

        prompt = self._build_ai_review_prompt(record)
        review = self._generate_ai_review(prompt)
        saved = await self.review_repo.save_ai_review(record_id, review, prompt, settings.OPENAI_TEXT_MODEL)
        return {**saved, "cached": False}

    def _generate_ai_review(self, prompt: str) -> Dict[str, Any]:
        response = post_chat_completion(
            [
                {"role": "system", "content": "你是资深技术面试教练，输出必须是严格 JSON，不要包裹 Markdown。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.55,
            timeout=90,
        )
        if response.status_code >= 400:
            raise ValueError(f"AI 复盘生成失败：{response.text[:500]}")
        text = extract_chat_completion_text(response.json())
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.S)
            if not match:
                raise ValueError("AI 返回内容不是合法 JSON")
            result = json.loads(match.group(0))
        return self._normalize_ai_review(result)

    @staticmethod
    def _build_ai_review_prompt(record: Dict[str, Any]) -> str:
        content = (record.get("content") or "")[:7000]
        return f"""
请基于下面这篇真实面经，生成一个面试复习版 AI 复盘。

要求：
1. 不要写公众号文案，不要营销腔，要像一个懂面试的教练在帮候选人梳理。
2. 输出严格 JSON，字段包括：
   summary: string，80 字以内总结这篇面经的考察特点。
   difficulty: string，只能是 "偏基础"、"中等"、"偏深入"、"综合强" 之一。
   priority: string，只能是 "低"、"中"、"高" 之一。
   questions: array，每项包含 question、answer、followups、tags。answer 是 30 秒回答思路，followups 是追问数组，tags 是知识点标签数组。
   knowledge_points: array，每项包含 name、why、review_tip。
   action_plan: array，给 3-5 条具体复习动作。
3. questions 最多 8 个，优先选择真实出现或明显隐含的高频技术问题。
4. 回答要简洁、像真人复盘，少一点 AI 味。

面经标题：{record.get("title")}
公司：{record.get("company")}
岗位方向：{record.get("post")}
正文：
{content}
"""

    @staticmethod
    def _normalize_ai_review(result: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": str(result.get("summary") or "这篇面经适合用来梳理高频问题和项目追问路径。")[:180],
            "difficulty": result.get("difficulty") or "中等",
            "priority": result.get("priority") or "中",
            "questions": list(result.get("questions") or [])[:8],
            "knowledge_points": list(result.get("knowledge_points") or [])[:8],
            "action_plan": list(result.get("action_plan") or [])[:6],
        }

    @staticmethod
    def _extract_questions(content: str) -> List[str]:
        normalized = (
            content.replace("\r", "\n")
            .replace("？", "?\n")
            .replace("。", "。\n")
            .replace("；", "；\n")
        )
        normalized = re.sub(r"([^\n])\s+(\d{1,2}[.、]\s*)", r"\1\n\2", normalized)
        candidates = []
        for line in normalized.splitlines():
            line = re.sub(r"^\s*\d{1,2}[.、]\s*", "", line.strip())
            if not line or len(line) > 90:
                continue
            if re.search(r"\?|什么|如何|怎么|区别|原理|介绍|讲讲|说说|实现|场景|为什么|哪些|是否|能不能", line):
                candidates.append(line.rstrip("。；,，"))
        return candidates

    @staticmethod
    def _normalize_question(question: str) -> str:
        question = re.sub(r"\s+", " ", question.strip())
        question = re.sub(r"^[一二三四五六七八九十]+[、.]\s*", "", question)
        return question[:80]

    @staticmethod
    def _category(question: str) -> str:
        lower = question.lower()
        if any(key in lower for key in ["java", "jvm", "spring", "mybatis", "线程", "锁", "并发"]):
            return "Java/并发"
        if any(key in lower for key in ["redis", "缓存", "mysql", "索引", "事务", "数据库", "sql"]):
            return "存储/数据库"
        if any(key in lower for key in ["算法", "复杂度", "链表", "数组", "树", "动态规划"]):
            return "算法"
        if any(key in lower for key in ["项目", "业务", "场景", "架构", "系统", "设计"]):
            return "项目/系统设计"
        if any(key in lower for key in ["网络", "http", "tcp", "操作系统", "进程"]):
            return "计算机基础"
        return "通用问题"
