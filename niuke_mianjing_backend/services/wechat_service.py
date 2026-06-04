import base64
import json
import random
import re
import tempfile
from collections import Counter
from datetime import datetime, timedelta
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import markdown
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw

from niuke_mianjing_backend.config import settings
from niuke_mianjing_backend.repositories.niuke_repo import NiukeRepository
from niuke_mianjing_backend.repositories.wechat_article_repo import WeChatArticleRepository


WECHAT_API_BASE = "https://api.weixin.qq.com/cgi-bin"
TARGET_COVER_SIZE = (900, 500)


class WeChatService:
    def __init__(self):
        self.article_repo = WeChatArticleRepository()
        self.niuke_repo = NiukeRepository()

    async def init_table(self):
        await self.article_repo.init_table()

    def parse_markdown(self, content: str, fallback_title: str = "未命名文章") -> Tuple[Dict, str, str]:
        metadata: Dict[str, object] = {}
        body = content.strip()

        if body.startswith("---"):
            match = re.match(r"^---\s*\n(.*?)\n---\s*\n?([\s\S]*)$", body)
            if match:
                raw_meta, body = match.groups()
                metadata = self._parse_frontmatter(raw_meta)

        title = str(metadata.get("title") or "").strip() or self._extract_first_heading(body) or fallback_title
        return metadata, body, title

    def render_html(self, markdown_content: str, fallback_title: str = "未命名文章") -> Dict[str, Any]:
        metadata, body, title = self.parse_markdown(markdown_content, fallback_title)
        body_html = markdown.markdown(
            body,
            extensions=["extra", "tables", "fenced_code", "nl2br", "sane_lists"],
            output_format="html5",
        )
        article_html = self._inline_wechat_styles(title, body_html)
        return {
            "title": title,
            "html": f"<!-- WECHAT_ARTICLE_TITLE: {title} -->\n{article_html}",
            "metadata": metadata,
        }

    async def generate_ai_article(
        self,
        markdown_content: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        digest: Optional[str] = None,
        content_source_url: Optional[str] = None,
        source_record_id: Optional[int] = None,
        style: str = "tech",
    ) -> Dict[str, Any]:
        self._ensure_openai_configured()

        fallback = self.parse_markdown(markdown_content, title or "未命名文章")[2]
        prompt = self._build_article_json_prompt(markdown_content, title or fallback, style)
        article = self._generate_article_json(prompt)

        article_title = title or article.get("title") or fallback
        article_digest = digest or article.get("digest") or self._plain_text(article.get("html", ""))[:100]
        html = self._ensure_wechat_html(article_title, article.get("html", ""))
        image_prompt = article.get("cover_prompt") or self._build_cover_prompt(article_title, markdown_content, style)
        cover_base64 = self._generate_cover_with_openai(image_prompt)

        return await self.save_ai_article(
            markdown_content=markdown_content,
            html=html,
            title=article_title,
            author=author or settings.WECHAT_AUTHOR,
            digest=article_digest,
            content_source_url=content_source_url,
            source_record_id=source_record_id,
            style=style,
            cover_prompt=image_prompt,
            cover_base64=cover_base64,
            cover_mime="image/png",
            status="generated",
        )

    async def save_ai_article(
        self,
        markdown_content: str,
        html: str,
        title: str,
        author: Optional[str],
        digest: Optional[str],
        content_source_url: Optional[str],
        source_record_id: Optional[int],
        style: str,
        cover_prompt: Optional[str] = None,
        cover_base64: Optional[str] = None,
        cover_mime: Optional[str] = None,
        status: str = "edited",
    ) -> Dict[str, Any]:
        self._ensure_openai_configured()
        final_html = self._ensure_wechat_html(title, html)
        prompt = cover_prompt or self._build_cover_prompt(title, markdown_content, style)
        final_cover_base64 = self._normalize_base64_image(cover_base64) if cover_base64 else self._generate_cover_with_openai(prompt)
        final_cover_mime = cover_mime or "image/png"
        model_info = {
            "text_model": settings.OPENAI_TEXT_MODEL,
            "image_model": settings.OPENAI_IMAGE_MODEL,
            "style": style,
            "flow": "stream-edit-save",
            "cover_source": "custom_upload" if cover_base64 else "ai_generated",
        }
        article_id = await self.article_repo.create_article(
            source_record_id=source_record_id,
            title=title,
            author=author or settings.WECHAT_AUTHOR,
            digest=digest or self._plain_text(final_html)[:100],
            content_source_url=content_source_url,
            markdown=markdown_content,
            html=final_html,
            cover_base64=final_cover_base64,
            cover_mime=final_cover_mime,
            prompt=prompt,
            model_info=model_info,
            status=status,
        )
        return await self.article_repo.get_article(article_id)

    def stream_wechat_html(self, markdown_content: str, title: Optional[str], style: str) -> Generator[Dict[str, Any], None, None]:
        self._ensure_openai_configured()
        fallback = self.parse_markdown(markdown_content, title or "未命名文章")[2]
        article_title = title or fallback
        prompt = self._build_stream_html_prompt(markdown_content, article_title, style)
        yield from self.stream_prompt_html(prompt, article_title)

    def stream_prompt_html(self, prompt: str, article_title: str) -> Generator[Dict[str, Any], None, None]:
        payload = {
            "model": settings.OPENAI_TEXT_MODEL,
            "stream": True,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是一个中文技术公众号主编。只输出微信公众号 HTML，不要输出解释或 Markdown 代码块。"
                        "文章要像真人编辑写的，有判断、有取舍、有具体复习建议。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        response = requests.post(
            self._chat_completions_url(),
            headers=self._openai_headers(),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            stream=True,
            timeout=(10, 240),
        )
        if response.status_code >= 400:
            raise ValueError(f"OpenAI 流式生成失败：{response.text[:1000]}")

        full_text = ""
        yield {"type": "meta", "title": article_title}
        response.encoding = "utf-8"
        for raw_line in response.iter_lines(decode_unicode=False):
            line = raw_line.decode("utf-8", errors="replace")
            if not line:
                continue
            if line.startswith("data:"):
                payload = line[5:].strip()
            else:
                payload = line.strip()
            if payload == "[DONE]":
                break
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            delta = self._extract_stream_delta(data)
            if not delta:
                continue
            full_text += delta
            yield {"type": "delta", "delta": delta}

        html = self._ensure_wechat_html(article_title, self._clean_html_text(full_text))
        yield {"type": "done", "title": article_title, "html": html}

    async def build_question_analysis(
        self,
        company: str,
        post: str,
        days: int = 30,
        limit: int = 200,
    ) -> Dict[str, Any]:
        start_time = datetime.now() - timedelta(days=days)
        records = await self.niuke_repo.get_recent_records(company, post, start_time, limit)
        if not records:
            raise ValueError(f"最近 {days} 天没有找到 {company} / {post} 的面经数据")

        question_counter: Counter[str] = Counter()
        category_counter: Counter[str] = Counter()

        for record in records:
            questions = self._extract_questions(record.get("content") or "")
            for question in questions:
                normalized = self._normalize_question(question)
                if len(normalized) < 4:
                    continue
                question_counter[normalized] += 1
                category_counter[self._question_category(normalized)] += 1

        if not question_counter:
            for record in records:
                title = self._normalize_question(record.get("title") or "")
                if title:
                    question_counter[title] += 1
                    category_counter[self._question_category(f"{title} {record.get('content') or ''}")] += 1

        top_questions = question_counter.most_common(20)
        title = f"{company}{post}面试趋势分析｜最近{days}天都在问什么"
        digest = f"统计最近 {days} 天 {len(records)} 篇 {company}{post} 面经，拆解高频题、知识点分布、趋势变化和备考优先级。"

        return {
            "title": title,
            "digest": digest,
            "stats": {
                "company": company,
                "post": post,
                "days": days,
                "record_count": len(records),
                "question_count": sum(question_counter.values()),
                "unique_question_count": len(question_counter),
                "top_questions": [
                    {"question": question, "count": count, "category": self._question_category(question)}
                    for question, count in top_questions
                ],
                "categories": [{"name": name, "count": count} for name, count in category_counter.most_common()],
            },
            "records": [
                {
                    "id": record.get("id"),
                    "title": record.get("title"),
                    "edit_time": record.get("edit_time"),
                    "content_id": record.get("content_id"),
                    "content": self._compact_record_content(record),
                }
                for record in records[:40]
            ],
        }

    def build_question_analysis_direct_prompt(self, analysis: Dict[str, Any]) -> str:
        return self._build_question_analysis_html_prompt(analysis)

    async def build_quick_checklist_analysis(
        self,
        company: str,
        post: str,
        limit: int = 10,
        order_by_time: bool = False,
        days: Optional[int] = None,
    ) -> Dict[str, Any]:
        start_time = datetime.now() - timedelta(days=days) if order_by_time and days else None
        records = await self.niuke_repo.get_records_for_analysis(
            company=company,
            post=post,
            limit=limit,
            start_time=start_time,
            order_by_time=order_by_time,
        )
        if not records:
            range_text = f"最近 {days} 天" if start_time else "全部样本"
            raise ValueError(f"{range_text}没有找到 {company} / {post} 的面经数据")

        question_counter: Counter[str] = Counter()
        category_counter: Counter[str] = Counter()
        for record in records:
            for question in self._extract_questions(record.get("content") or ""):
                normalized = self._normalize_question(question)
                if len(normalized) < 4:
                    continue
                question_counter[normalized] += 1
                category_counter[self._question_category(normalized)] += 1

        if not question_counter:
            for record in records:
                title = self._normalize_question(record.get("title") or "")
                if title:
                    question_counter[title] += 1
                    category_counter[self._question_category(f"{title} {record.get('content') or ''}")] += 1

        sample_mode = "按时间倒序" if order_by_time else "随机抽样"
        range_label = f"最近 {days} 天" if start_time else "全部时间"
        title = f"{company}{post}高频题速查清单｜{len(records)}篇面经整理"
        digest = f"{sample_mode}抽取 {range_label} {len(records)} 篇 {company}{post} 面经，整理高频问题、30 秒答法和易错点。"
        return {
            "title": title,
            "digest": digest,
            "stats": {
                "company": company,
                "post": post,
                "limit": limit,
                "record_count": len(records),
                "order_by_time": order_by_time,
                "days": days,
                "range_label": range_label,
                "sample_mode": sample_mode,
                "question_count": sum(question_counter.values()),
                "unique_question_count": len(question_counter),
                "top_questions": [
                    {"question": question, "count": count, "category": self._question_category(question)}
                    for question, count in question_counter.most_common(25)
                ],
                "categories": [{"name": name, "count": count} for name, count in category_counter.most_common()],
            },
            "records": [
                {
                    "id": record.get("id"),
                    "title": record.get("title"),
                    "edit_time": record.get("edit_time"),
                    "content_id": record.get("content_id"),
                    "content": self._compact_record_content(record),
                }
                for record in records
            ],
        }

    def build_quick_checklist_prompt(self, analysis: Dict[str, Any]) -> str:
        return self._build_quick_checklist_html_prompt(analysis)

    async def list_articles(self, limit: int = 20, offset: int = 0):
        return await self.article_repo.list_articles(limit, offset)

    async def get_article(self, article_id: int, include_content: bool = True):
        return await self.article_repo.get_article(article_id, include_content)

    async def publish_saved_article(self, article_id: int) -> Dict[str, Any]:
        article = await self.article_repo.get_article(article_id)
        if not article:
            raise ValueError("公众号稿件不存在")
        if not article.get("html") or not article.get("cover_base64"):
            raise ValueError("稿件缺少 HTML 或封面图，请先重新生成")

        try:
            token = self.get_token()
            with tempfile.TemporaryDirectory() as temp_dir:
                cover_path = str(Path(temp_dir) / f"wechat_cover{self._cover_suffix(article.get('cover_mime'))}")
                self._write_base64_image(article["cover_base64"], cover_path)
                cover_media_id = self.upload_cover(token, cover_path)

            draft = self.push_draft(
                token=token,
                title=article["title"],
                html_content=article["html"],
                cover_media_id=cover_media_id,
                author=article.get("author") or settings.WECHAT_AUTHOR,
                digest=article.get("digest"),
                content_source_url=article.get("content_source_url"),
            )
            await self.article_repo.update_publish_result(
                article_id,
                status="drafted",
                wechat_media_id=draft["media_id"],
                cover_media_id=cover_media_id,
                error_message=None,
            )
            return {
                "title": article["title"],
                "media_id": draft["media_id"],
                "cover_media_id": cover_media_id,
                "wechat_response": draft,
            }
        except Exception as exc:
            await self.article_repo.update_publish_result(article_id, status="failed", error_message=str(exc))
            raise

    def generate_cover(self, output_path: str, theme: str = "auto", markdown_content: str = "") -> str:
        palette = self._pick_palette(theme, markdown_content)
        img = Image.new("RGB", TARGET_COVER_SIZE, palette["background"])
        draw = ImageDraw.Draw(img)

        for _ in range(140):
            x, y = random.randint(0, TARGET_COVER_SIZE[0]), random.randint(0, TARGET_COVER_SIZE[1])
            b = random.randint(120, 255)
            draw.point((x, y), fill=(max(0, b - 60), max(0, b - 30), b))

        overlay = Image.new("RGBA", TARGET_COVER_SIZE, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([120, 80, 580, 420], fill=palette["glow_primary"])
        od.ellipse([430, 20, 820, 360], fill=palette["glow_secondary"])

        if palette["kind"] == "programming":
            for x in range(40, TARGET_COVER_SIZE[0], 42):
                for y in range(-20, TARGET_COVER_SIZE[1] + 20, 38):
                    if random.random() > 0.55:
                        od.text((x, y), random.choice(["0", "1", "{ }", "</>"]), fill=(52, 211, 153, 55))
        else:
            nodes = [(random.randint(140, 760), random.randint(90, 410)) for _ in range(18)]
            for idx, (x, y) in enumerate(nodes):
                for nx, ny in nodes[idx + 1 : idx + 4]:
                    od.line((x, y, nx, ny), fill=palette["line"])
                od.ellipse([x - 4, y - 4, x + 4, y + 4], fill=palette["node"])

        final_img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        final_img.save(output_path, "PNG")
        return output_path

    def get_token(self, appid: Optional[str] = None, secret: Optional[str] = None) -> str:
        appid = appid or settings.WECHAT_APP_ID
        secret = secret or settings.WECHAT_APP_SECRET
        if not appid or not secret:
            raise ValueError("请先在 .env 配置 WECHAT_APP_ID 和 WECHAT_APP_SECRET")

        response = requests.get(
            f"{WECHAT_API_BASE}/token",
            params={"grant_type": "client_credential", "appid": appid, "secret": secret},
            timeout=15,
        )
        data = response.json()
        if "access_token" not in data:
            raise ValueError(f"获取微信 access_token 失败：{data}")
        return data["access_token"]

    def upload_cover(self, token: str, image_path: str) -> str:
        suffix = Path(image_path).suffix.lower()
        mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/webp" if suffix == ".webp" else "image/png"
        with open(image_path, "rb") as f:
            response = requests.post(
                f"{WECHAT_API_BASE}/material/add_material",
                params={"access_token": token, "type": "image"},
                files={"media": (Path(image_path).name, f, mime)},
                timeout=30,
            )
        data = response.json()
        if "media_id" not in data:
            raise ValueError(f"上传微信封面失败：{data}")
        return data["media_id"]

    def push_draft(
        self,
        token: str,
        title: str,
        html_content: str,
        cover_media_id: str,
        author: str,
        digest: Optional[str] = None,
        content_source_url: Optional[str] = None,
    ) -> Dict:
        article = {
            "title": title[:64],
            "author": author[:8],
            "content": html_content,
            "thumb_media_id": cover_media_id,
            "show_cover_pic": 0,
        }
        if digest:
            article["digest"] = digest[:120]
        if content_source_url:
            article["content_source_url"] = content_source_url

        response = requests.post(
            f"{WECHAT_API_BASE}/draft/add",
            params={"access_token": token},
            data=json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30,
        )
        data = response.json()
        if "media_id" not in data:
            raise ValueError(f"创建微信草稿失败：{data}")
        return data

    def create_draft(
        self,
        markdown_content: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        digest: Optional[str] = None,
        content_source_url: Optional[str] = None,
        cover_theme: str = "auto",
    ) -> Dict:
        rendered = self.render_html(markdown_content, title or "未命名文章")
        article_title = title or rendered["title"]
        token = self.get_token()

        with tempfile.TemporaryDirectory() as temp_dir:
            cover_path = str(Path(temp_dir) / "wechat_cover.png")
            self.generate_cover(cover_path, cover_theme, markdown_content)
            cover_media_id = self.upload_cover(token, cover_path)

        draft = self.push_draft(
            token=token,
            title=article_title,
            html_content=rendered["html"],
            cover_media_id=cover_media_id,
            author=author or settings.WECHAT_AUTHOR,
            digest=digest,
            content_source_url=content_source_url,
        )
        return {
            "title": article_title,
            "media_id": draft["media_id"],
            "cover_media_id": cover_media_id,
            "wechat_response": draft,
        }

    def _ensure_openai_configured(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("请先在 .env 配置 OPENAI_API_KEY")

    def _openai_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _generate_article_json(self, prompt: str) -> Dict[str, str]:
        payload = {
            "model": settings.OPENAI_TEXT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个中文技术公众号主编，只返回合法 JSON，不要输出解释。",
                },
                {"role": "user", "content": prompt},
            ],
        }
        response = requests.post(
            self._chat_completions_url(),
            headers=self._openai_headers(),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=90,
        )
        data = response.json()
        if response.status_code >= 400:
            raise ValueError(f"OpenAI 文章生成失败：{data}")

        text = self._extract_chat_completion_text(data)
        parsed = self._parse_json_text(text)
        if not parsed.get("html"):
            raise ValueError("OpenAI 返回内容缺少 html 字段")
        return parsed

    def _generate_cover_with_openai(self, prompt: str) -> str:
        payload = {
            "model": settings.OPENAI_IMAGE_MODEL,
            "prompt": prompt,
            "size": "1536x1024",
            "quality": "medium",
            "n": 1,
        }
        response = requests.post(
            self._image_generations_url(),
            headers=self._openai_headers(),
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=120,
        )
        data = response.json()
        if response.status_code >= 400:
            raise ValueError(f"OpenAI 封面生成失败：{data}")

        image_item = data.get("data", [{}])[0]
        image_base64 = image_item.get("b64_json")
        image_url = image_item.get("url")
        if not image_base64 and image_url:
            image_base64 = self._image_url_to_base64(image_url)
        if not image_base64:
            raise ValueError(f"OpenAI 封面响应缺少 b64_json：{data}")
        return self._resize_cover_base64(image_base64)

    @staticmethod
    def _chat_completions_url() -> str:
        url = (settings.OPENAI_CHAT_COMPLETIONS_URL or "").strip()
        if url:
            return url

        base_url = settings.OPENAI_BASE_URL.rstrip("/")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"

    @staticmethod
    def _image_generations_url() -> str:
        if settings.OPENAI_IMAGE_GENERATIONS_URL:
            return settings.OPENAI_IMAGE_GENERATIONS_URL

        chat_url = WeChatService._chat_completions_url().rstrip("/")
        if chat_url.endswith("/chat/completions"):
            return f"{chat_url.removesuffix('/chat/completions')}/images/generations"
        return f"{settings.OPENAI_BASE_URL.rstrip('/')}/images/generations"

    @staticmethod
    def _extract_chat_completion_text(data: Dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise ValueError(f"OpenAI 返回缺少 choices：{data}")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            chunks = []
            for item in content:
                if isinstance(item, dict) and item.get("text"):
                    chunks.append(item["text"])
                elif isinstance(item, str):
                    chunks.append(item)
            return "\n".join(chunks).strip()

        raise ValueError(f"OpenAI 返回内容为空：{data}")

    @staticmethod
    def _extract_stream_delta(data: Dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if not choices:
            return ""
        delta = choices[0].get("delta") or {}
        content = delta.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in content)
        return ""

    @staticmethod
    def _parse_json_text(text: str) -> Dict[str, str]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", cleaned)
            if match:
                return json.loads(match.group(0))
            raise ValueError("OpenAI 返回不是合法 JSON")

    @staticmethod
    def _resize_cover_base64(image_base64: str) -> str:
        raw = base64.b64decode(image_base64)
        img = Image.open(BytesIO(raw)).convert("RGB")
        src_w, src_h = img.size
        target_ratio = TARGET_COVER_SIZE[0] / TARGET_COVER_SIZE[1]
        src_ratio = src_w / src_h

        if src_ratio > target_ratio:
            new_w = int(src_h * target_ratio)
            left = (src_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, src_h))
        else:
            new_h = int(src_w / target_ratio)
            top = (src_h - new_h) // 2
            img = img.crop((0, top, src_w, top + new_h))

        img = img.resize(TARGET_COVER_SIZE, Image.Resampling.LANCZOS)
        output = BytesIO()
        img.save(output, "PNG")
        return base64.b64encode(output.getvalue()).decode("utf-8")

    @staticmethod
    def _image_url_to_base64(image_url: str) -> str:
        if image_url.startswith("data:image"):
            _, encoded = image_url.split(",", 1)
            return encoded

        response = requests.get(image_url, timeout=60)
        if response.status_code >= 400:
            raise ValueError(f"下载封面图失败：HTTP {response.status_code}")
        return base64.b64encode(response.content).decode("utf-8")

    @staticmethod
    def _write_base64_image(image_base64: str, output_path: str):
        Path(output_path).write_bytes(base64.b64decode(image_base64))

    @staticmethod
    def _normalize_base64_image(image_base64: str) -> str:
        value = image_base64.strip()
        if value.startswith("data:"):
            _, _, value = value.partition(",")
        base64.b64decode(value, validate=True)
        return value

    @staticmethod
    def _cover_suffix(mime: Optional[str]) -> str:
        suffixes = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }
        return suffixes.get((mime or "").lower(), ".png")

    @staticmethod
    def _parse_frontmatter(raw_meta: str) -> Dict:
        metadata: Dict[str, object] = {}
        for line in raw_meta.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                metadata[key.strip()] = [item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip()]
            else:
                metadata[key.strip()] = value.strip("\"'")
        return metadata

    @staticmethod
    def _extract_first_heading(body: str) -> Optional[str]:
        for line in body.splitlines():
            match = re.match(r"^#\s+(.+)$", line.strip())
            if match:
                return match.group(1).strip()
        return None

    @staticmethod
    def _inline_wechat_styles(title: str, body_html: str) -> str:
        soup = BeautifulSoup(body_html, "html.parser")
        styles = {
            "h1": "font-size:22px;line-height:1.4;font-weight:bold;color:#1a1a1a;margin:0 0 24px 0;border-bottom:2px solid #1677ff;padding-bottom:14px;",
            "h2": "font-size:18px;line-height:1.5;font-weight:bold;color:#1a1a1a;margin:30px 0 16px;border-left:4px solid #1677ff;padding-left:10px;",
            "h3": "font-size:16px;line-height:1.5;font-weight:bold;color:#1677ff;margin:22px 0 10px;",
            "p": "font-size:16px;line-height:1.78;color:#333333;margin:0 0 16px;text-align:justify;",
            "ul": "font-size:16px;line-height:1.75;color:#333333;margin:14px 0 16px;padding-left:22px;",
            "ol": "font-size:16px;line-height:1.75;color:#333333;margin:14px 0 16px;padding-left:22px;",
            "li": "font-size:16px;line-height:1.75;color:#333333;margin:0 0 8px;",
            "blockquote": "margin:18px 0;padding:14px 16px;border-left:4px solid #1677ff;background-color:#f0f7ff;color:#555555;",
            "pre": "font-size:13px;line-height:1.65;color:#cdd6f4;background-color:#1e1e2e;border-radius:6px;padding:14px;overflow:auto;",
            "code": "font-family:Consolas,Menlo,monospace;background-color:#f0f0f0;color:#d32f2f;border-radius:3px;padding:2px 5px;",
            "a": "color:#1677ff;text-decoration:none;",
            "table": "width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;",
            "th": "border:1px solid #dddddd;background-color:#1677ff;color:#ffffff;padding:9px 10px;text-align:left;font-weight:bold;",
            "td": "border:1px solid #dddddd;color:#333333;padding:8px 10px;text-align:left;",
            "img": "max-width:100%;height:auto;border-radius:4px;margin:14px auto;display:block;",
            "hr": "border:0;border-top:1px solid #e5e7eb;margin:24px 0;",
            "strong": "font-weight:bold;color:#1a1a1a;",
            "em": "font-style:italic;color:#666666;",
        }
        for tag_name, style in styles.items():
            for tag in soup.find_all(tag_name):
                tag["style"] = f"{tag.get('style', '')}{style}"

        content = str(soup)
        escaped_title = escape(title)
        return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif;color:#333333;">
  <tr>
    <td style="padding:0;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:677px;margin:0 auto;background-color:#ffffff;">
        <tr>
          <td style="padding:18px 16px 24px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:22px;">
              <tr>
                <td style="border-bottom:2px solid #1677ff;padding-bottom:14px;">
                  <p style="font-size:13px;line-height:1.6;color:#1677ff;margin:0 0 8px;">牛客面经助手 · 技术复盘</p>
                  <h1 style="font-size:22px;line-height:1.4;color:#1a1a1a;font-weight:bold;margin:0;">{escaped_title}</h1>
                </td>
              </tr>
            </table>
            {content}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
""".strip()

    @staticmethod
    def _inline_report_styles(title: str, body_html: str) -> str:
        soup = BeautifulSoup(body_html, "html.parser")
        for tag in soup.find_all(["p", "li"]):
            tag["style"] = (
                "box-sizing:border-box;margin:1.3em 8px;text-align:justify;"
                "line-height:1.75;font-size:14px;letter-spacing:0.08em;color:rgb(63,63,63);"
            )
        for tag in soup.find_all("strong"):
            tag["style"] = "font-weight:bold;color:rgb(15,76,129);"
        for tag in soup.find_all("h1"):
            tag["style"] = (
                "box-sizing:border-box;border-width:0 0 2px;border-style:solid;"
                "border-color:rgb(15,76,129);font-size:16.8px;font-weight:bold;"
                "margin:2em auto 1em;text-align:center;line-height:1.75;display:table;"
                "padding:0 1em;color:rgb(63,63,63);"
            )
        for tag in soup.find_all("h2"):
            tag["style"] = (
                "box-sizing:border-box;font-size:16.8px;font-weight:bold;margin:4em auto 2em;"
                "text-align:center;line-height:1.75;display:table;padding:0 0.4em;"
                "color:#fff;background:rgb(15,76,129);"
            )
        for tag in soup.find_all("h3"):
            tag["style"] = (
                "box-sizing:border-box;font-size:15.5px;font-weight:bold;margin:2.2em 8px 1em;"
                "line-height:1.75;color:rgb(15,76,129);"
            )
        for tag in soup.find_all("hr"):
            tag["style"] = (
                "box-sizing:border-box;border:0;border-top:2px solid #e5e7eb;"
                "height:0;margin:1.5em 0;"
            )
        for table in soup.find_all("table"):
            table["style"] = "box-sizing:border-box;border-collapse:collapse;border-spacing:0;width:100%;margin:1em 0;"
        for cell in soup.find_all(["td", "th"]):
            cell["style"] = (
                "box-sizing:border-box;border:1px solid rgb(223,223,223);text-align:left;"
                "line-height:1.75;font-size:14px;padding:0.25em 0.5em;color:rgb(63,63,63);"
            )
        content = str(soup)
        escaped_title = escape(title)
        return f"""
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff;font-family:-apple-system-font,BlinkMacSystemFont,'Helvetica Neue','PingFang SC','Hiragino Sans GB','Microsoft YaHei UI','Microsoft YaHei',Arial,sans-serif;color:rgb(63,63,63);">
  <tr>
    <td style="padding:0;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:677px;margin:0 auto;background-color:#ffffff;">
        <tr>
          <td style="padding:0 8px 24px;text-align:left;line-height:1.75;font-size:14px;">
            <h1 style="box-sizing:border-box;border-width:0 0 2px;border-style:solid;border-color:rgb(15,76,129);font-size:16.8px;font-weight:bold;margin:2em auto 1em;text-align:center;line-height:1.75;display:table;padding:0 1em;color:rgb(63,63,63);">{escaped_title}</h1>
            {content}
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
""".strip()

    def _ensure_wechat_html(self, title: str, html: str) -> str:
        cleaned = self._clean_html_text(html)
        if "<section" not in cleaned and "<p" not in cleaned:
            cleaned = markdown.markdown(cleaned, extensions=["extra", "tables", "fenced_code", "nl2br", "sane_lists"])
        if self._is_question_analysis_title(title) and "rgb(15, 76, 129)" not in cleaned:
            cleaned = self._inline_report_styles(title, cleaned)
        elif "style=" not in cleaned:
            cleaned = self._inline_wechat_styles(title, cleaned)
        if "WECHAT_ARTICLE_TITLE" not in cleaned:
            cleaned = f"<!-- WECHAT_ARTICLE_TITLE: {title} -->\n{cleaned}"
        return cleaned

    @staticmethod
    def _is_question_analysis_title(title: str) -> bool:
        return any(keyword in title for keyword in ["高频", "趋势", "TOP", "Top", "top", "面试题", "都在问"])

    @staticmethod
    def _clean_html_text(value: str) -> str:
        cleaned = value.strip()
        cleaned = re.sub(r"^```(?:html)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = re.sub(r"[\u200b-\u200f\ufeff]", "", cleaned)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)
        cleaned = re.sub(r"<script[\s\S]*?</script>", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<style[\s\S]*?</style>", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    @staticmethod
    def _plain_text(html: str) -> str:
        return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)

    @staticmethod
    def _build_article_json_prompt(markdown_content: str, title: str, style: str) -> str:
        html_prompt = WeChatService._build_stream_html_prompt(markdown_content, title, style)
        return f"""
请基于下面要求生成公众号稿件，并只返回 JSON：
{{
  "title": "不超过 30 字的公众号标题",
  "digest": "不超过 100 字的摘要",
  "html": "完整微信公众号 HTML",
  "cover_prompt": "英文封面图提示词，不含文字、logo、水印"
}}

HTML 生成要求：
{html_prompt}
""".strip()

    @staticmethod
    def _build_stream_html_prompt(markdown_content: str, title: str, style: str) -> str:
        content_prompt = WeChatService._wechat_content_type_prompt(style)
        return f"""
请把原始素材改写成一篇适合微信公众号阅读的中文技术文章。

只输出微信公众号 HTML，不要输出 Markdown 代码块，不要解释。

通用内容要求：
1. 保留原始事实，不编造公司、岗位、轮次、结果。
2. 标题和开头要有钩子，但不要标题党，不要夸大数据或面试难度。
3. 使用真人技术号编辑口吻，可以有判断和提醒，但不要空泛说教。
4. 段落短一点，长段拆开；每一屏都要有小标题、列表或提示块形成视觉节奏。
5. 除“面试趋势分析”外，尽量少用表格；确需表格时最多 3-5 行，列数不超过 3，避免手机阅读横向拥挤。
6. 结尾要给可执行的复习建议或收藏清单，并自然引导读者互动。

本次内容类型模板：
{content_prompt}

去 AI 味要求：
1. 禁止出现：作为 AI、本文将、综上所述、希望对你有帮助、值得注意的是、事实上、不难发现、总体来说、综合来看。
2. 尽量不用：赋能、闭环、生态、抓手、底层逻辑、范式、沉淀、势能、护城河、降维打击。
3. 不要“首先、其次、最后”机械三段式；用更自然的过渡。
4. 读起来要像技术号编辑写给同学看的复盘，信息密度高，但不端着。

排版要求：
1. 只能使用微信公众号兼容的 HTML 和内联 style。
2. 不要使用 style 标签、script、svg、canvas、外链 CSS、伪元素、Flexbox、Grid。
3. 不要使用 linear-gradient、rgba/hsla、box-shadow；颜色用 #RRGGBB 或 rgb(r,g,b) 纯色。
4. 复杂视觉块可以用 table 做外层布局，但正文内容不要滥用表格。
5. 用 HTML + CSS 绘制简单视觉块：导读卡片、重点提示、复习优先级、收藏清单。
6. 正文字号 15-16px，line-height 1.75-1.85，移动端阅读舒服。
7. 必须包含注释：<!-- WECHAT_ARTICLE_TITLE: {title} -->
8. 推荐白底、浅蓝/浅黄提示块、深蓝标题，不要大面积彩色背景。

默认标题：{title}

原始 Markdown：
{markdown_content[:12000]}
""".strip()

    @staticmethod
    def _wechat_content_type_prompt(content_type: str) -> str:
        prompts = {
            "single_interpretation": """
内容类型：单篇面经解读。
目标：把一篇真实面经写成完整公众号解读文，读者看完知道这场面试难在哪、该怎么复盘。
推荐模板：
1. 开头钩子：用 80-120 字说明公司/岗位/面试感受/为什么值得看。
2. 面经速览：用短段落或轻量提示块写公司、岗位、轮次、整体难度、适合人群，不要做大表格。
3. 问题拆解：挑 6-10 个代表性问题，每个问题写“考点是什么 / 该怎么答 / 复习提醒”。
4. 面试官真正想看什么：总结基础深挖、项目表达、工程经验或算法能力。
5. 复习优先级：用列表给出 A/B/C 级复习顺序。
6. 结尾：提醒收藏，并抛一个自然的问题引导评论。
表格限制：原则上不用表格；如果必须用，最多 3 行。
""",
            "knowledge_deep_dive": """
内容类型：技术知识点精讲。
目标：从一篇面经中挑 3-5 个最值得展开的知识点，写成“能学到东西”的技术精讲文。
推荐模板：
1. 开头钩子：指出这篇面经里最值得复盘的几个知识点。
2. 知识点选择理由：解释为什么 AI 选这些点，它们为什么高频、为什么容易被追问。
3. 每个知识点独立成节，结构固定为：面试怎么问 / 核心原理 / 30 秒答题模板 / 常见追问 / 易错点 / 复习建议。
4. 知识点之间要有自然过渡，不要像题库列表。
5. 结尾给“今天先补哪几个点”的行动清单。
表格限制：不要用大表格；知识点内容用小标题、列表、提示块呈现。
""",
            "manual_rewrite": """
内容类型：手动粘贴。
目标：根据用户粘贴的 Markdown 判断素材类型，并改写成一篇公众号文章。
推荐模板：
1. 如果素材是面经：按“单篇面经解读”写。
2. 如果素材是知识笔记：按“技术知识点精讲”写。
3. 如果素材是零散问题：整理成清单文，补充简答关键词和复习建议。
4. 如果素材已经是文章：优化标题、开头、节奏和移动端排版，保留核心观点。
5. 结尾给可执行建议或互动问题。
表格限制：默认不用表格；除非原素材强依赖表格，且表格要短。
""",
            "quick_checklist": """
内容类型：高频题速查清单。
目标：把一篇面经整理成适合收藏、临考前快速翻看的题目清单。
推荐模板：
1. 开头钩子：说明这份清单适合什么读者、什么时候看。
2. 速查规则：告诉读者每题只看三件事：问法、30 秒答法、易错点。
3. 清单正文：整理 10-15 个问题，每个问题用独立小块呈现：题目 / 30 秒答法 / 易错点 / 复习优先级。
4. 如果问题很多，按 Java 基础、并发、数据库、框架、项目等分组。
5. 结尾给“今晚先背这 5 个”的短清单。
表格限制：不要做大表格；用编号卡片或短列表。最多用一个 3 行以内的小表总结优先级。
""",
            "interviewer_chain": """
内容类型：面试官追问链路。
目标：不是罗列题目，而是还原面试官如何从一个问题继续追问，帮助读者练“接招能力”。
推荐模板：
1. 开头钩子：指出很多人不是不会第一问，而是倒在第二问、第三问。
2. 选择 3-5 个核心问题，每个问题写成一条追问链。
3. 每条追问链结构：第一问 / 合格回答 / 面试官可能继续追问 1-3 个 / 追问背后的考察点 / 怎么答更稳 / 容易暴露的短板。
4. 加一节“被追问时别急着背八股”，讲表达策略。
5. 结尾给模拟练习方法。
表格限制：不用表格；追问链用箭头、短段落和提示块呈现。
""",
            "trend_analysis": """
内容类型：面试趋势分析。
该类型通常由专门的高频分析接口生成。如果误走当前接口，请按“单篇素材中的趋势观察”处理，不要伪造频次。
""",
        }
        return prompts.get(content_type, prompts["single_interpretation"]).strip()

    @staticmethod
    def _build_question_analysis_html_prompt(analysis: Dict[str, Any]) -> str:
        title = analysis["title"]
        stats = analysis.get("stats", {})
        records = analysis.get("records", [])
        top_questions = stats.get("top_questions", [])
        categories = stats.get("categories", [])
        source_payload = {
            "title": title,
            "digest": analysis.get("digest"),
            "stats": stats,
            "top_questions": top_questions,
            "categories": categories,
            "records": records,
        }
        return f"""
请基于下面的真实牛客面经素材，直接分析并写成一篇适合微信公众号发布的中文技术选题文章。

只输出微信公众号 HTML，不要输出 Markdown 代码块，不要解释。

参考版式方向：
用户想要接近这类公众号报告文风：标题直给，正文是白底深蓝数据报告风；少用花哨卡片，多用分割线、居中小标题、表格榜单、频次数字加粗、分类清单。整体像“某公司某岗位高频题 TOP 清单 + 备考指南”，不是营销海报。

内容目标：
1. 你要真的读完 records 里的真实面经素材，综合面经语境、问题频次和知识点分类做判断，不要只改写统计字段。
2. 标题和开头要有点击欲，但不要标题党，不要夸大数据。
3. 开头 80 字内说清楚：统计了哪家公司、哪个岗位、什么时间范围、样本数、对读者有什么用。
4. 文章必须包含：引子、数据结论、高频 TOP10 表格、分类 TOP 清单、趋势观察、最低限度备考清单、最后收藏提醒。
5. 高频问题不能只罗列，要补充“为什么爱问 / 简答抓手 / 复习建议”，并尽量带出现频次。
6. 需要有 2-4 句像真人编辑的观察，比如“最近更偏基础深挖还是项目追问”“哪些题看似八股但其实在考工程经验”。
7. 语气像有经验的技术号编辑，少一点 AI 腔，不要出现“作为 AI”“本文将”“综上所述”等套话。
8. 可以提醒数据来自当前库内面经样本，不代表全部面试。
9. 不要把 records 原文整段粘贴出来，要消化成“趋势 + 高频题 + 备考策略”。
10. 结尾要自然引导收藏和复盘，可以抛一个问题让读者留言，不要硬广。

去 AI 味要求：
1. 禁止出现：作为 AI、本文将、综上所述、希望对你有帮助、值得注意的是、事实上、不难发现、总体来说、综合来看。
2. 尽量不用：赋能、闭环、生态、抓手、底层逻辑、范式、沉淀、势能、护城河、降维打击。
3. 不要“首先、其次、最后”机械连接，过渡要像真人编辑写稿。

排版要求：
1. 只能使用微信公众号兼容的 HTML 和内联 style。
2. 不要使用 style 标签、script、svg、canvas、外链 CSS、伪元素、Flexbox、Grid。
3. 不要使用 linear-gradient、rgba/hsla、box-shadow；复杂布局尽量用 table，避免同步到微信后样式丢失。
4. 主色使用深蓝 rgb(15,76,129)，正文文字 rgb(63,63,63)，白底，不要渐变，不要大面积彩色背景。
5. 正文段落统一 14px、line-height 1.75、letter-spacing 0.08em-0.1em、margin 1.3em 8px、text-align justify。
6. H1 使用居中、下边框深蓝、display:table、padding:0 1em、font-size:16.8px。
7. H2 使用居中深蓝底白字小标签，margin:4em auto 2em，display:table，padding:0 0.4em，font-size:16.8px。
8. 章节之间使用 hr，样式为浅灰 2px 横线，margin:1.5em 0，不要使用 rgba。
9. 高频榜必须用 table，列包括“排名 / 高频题 / 频次 / 复习抓手”。表格边框 #dfdfdf，单元格 padding 0.25em 0.5em，频次用深蓝 strong 加粗。
10. 分类部分可以继续用小表格或编号段落，避免一堆圆角卡片；最多使用 1 个浅蓝提示块作为结尾提醒。
11. 必须包含注释：<!-- WECHAT_ARTICLE_TITLE: {title} -->

建议 HTML 样式骨架：
<section style="text-align:left;line-height:1.75;font-family:-apple-system-font,BlinkMacSystemFont,'Helvetica Neue','PingFang SC','Microsoft YaHei',Arial,sans-serif;font-size:14px;color:rgb(63,63,63);background:#fff;">
  <h1 style="font-size:16.8px;font-weight:bold;margin:2em auto 1em;text-align:center;display:table;padding:0 1em;color:rgb(63,63,63);border-bottom:2px solid rgb(15,76,129);">标题</h1>
  <p style="margin:1.5em 8px;text-align:justify;line-height:1.75;font-size:14px;letter-spacing:0.1em;color:rgb(63,63,63);">正文...</p>
  <hr style="border:0;border-top:2px solid #e5e7eb;height:0;margin:1.5em 0;" />
  <h2 style="font-size:16.8px;font-weight:bold;margin:4em auto 2em;text-align:center;display:table;padding:0 0.4em;color:#fff;background:rgb(15,76,129);">章节标题</h2>
</section>

默认标题：{title}

真实面经素材和轻量统计 JSON：
{json.dumps(source_payload, ensure_ascii=False)[:18000]}
""".strip()

    @staticmethod
    def _build_quick_checklist_html_prompt(analysis: Dict[str, Any]) -> str:
        title = analysis["title"]
        stats = analysis.get("stats", {})
        records = analysis.get("records", [])
        source_payload = {
            "title": title,
            "digest": analysis.get("digest"),
            "stats": stats,
            "records": records,
        }
        return f"""
请基于下面的真实牛客面经样本，写成一篇适合微信公众号发布的“高频题速查清单”。

只输出微信公众号 HTML，不要输出 Markdown 代码块，不要解释。

重要边界：
1. 这是 {stats.get("sample_mode", "样本抽取")}，范围是 {stats.get("range_label", "当前样本")}，样本数 {stats.get("record_count", 0)} 篇。
2. 不要写成“全网统计”或“全部面试趋势”，只能说“从当前样本看”。
3. 你要读 records 里的真实面经内容，结合轻量频次统计整理速查清单。

内容目标：
1. 开头 80 字内说清：公司、岗位、样本数、抽样方式、这篇适合谁收藏。
2. 输出 10-15 个最值得背的高频题，每题包括：题目、30 秒答法、易错点、复习优先级。
3. 如果题目多，按 Java 基础、并发、数据库、框架、项目、算法等分组。
4. 补充“今晚优先背哪 5 个”和“面试前 10 分钟怎么扫一遍”。
5. 语气像有经验的技术号编辑，短句多一点，适合手机快速阅读。

表格限制：
1. 不要做大表格，不要 4 列以上表格。
2. 正文清单用编号、小标题、浅色提示块呈现。
3. 最多允许一个 3 行以内的小表格，用来总结复习优先级。

排版要求：
1. 只能使用微信公众号兼容的 HTML 和内联 style。
2. 不要使用 style 标签、script、svg、canvas、外链 CSS、伪元素、Flexbox、Grid。
3. 不要使用 linear-gradient、rgba/hsla、box-shadow。
4. 白底，深蓝标题，正文 15-16px，line-height 1.75-1.85。
5. 必须包含注释：<!-- WECHAT_ARTICLE_TITLE: {title} -->

默认标题：{title}

真实面经样本 JSON：
{json.dumps(source_payload, ensure_ascii=False)[:18000]}
""".strip()

    @staticmethod
    def _extract_questions(content: str) -> List[str]:
        questions: List[str] = []
        for raw_line in re.split(r"[\n\r]+", content or ""):
            line = re.sub(r"\s+", " ", raw_line).strip()
            line = re.sub(r"^[\-*•\s]*\d{1,3}[\.、)]\s*", "", line)
            if not line or len(line) > 120:
                continue
            if "？" in line or "?" in line:
                questions.append(line)
                continue
            if re.match(r"^(说说|讲讲|介绍|解释|什么是|为什么|如何|怎么|有没有|哪些|区别|原理|实现|场景|用过)", line):
                questions.append(line)
        return questions[:80]

    @staticmethod
    def _compact_record_content(record: Dict[str, Any]) -> str:
        content = re.sub(r"\s+", " ", record.get("content") or "").strip()
        return content[:900]

    @staticmethod
    def _normalize_question(question: str) -> str:
        value = re.sub(r"\s+", " ", question).strip()
        value = re.sub(r"^[\-*•\s]*\d{1,3}[\.、)]\s*", "", value)
        value = value.strip(" ：:，,。；;？?")
        return value[:90]

    @staticmethod
    def _question_category(question: str) -> str:
        text = question.lower()
        categories = [
            ("Java 基础", ["java", "string", "集合", "hashmap", "反射", "泛型", "注解", "对象", "继承"]),
            ("并发编程", ["线程", "并发", "锁", "volatile", "synchronized", "threadlocal", "线程池", "cas", "aqs"]),
            ("JVM", ["jvm", "垃圾回收", "gc", "内存", "类加载", "堆", "栈"]),
            ("数据库/MySQL", ["mysql", "数据库", "索引", "事务", "隔离", "sql", "binlog", "mvcc"]),
            ("缓存/Redis", ["redis", "缓存", "雪崩", "击穿", "穿透", "分布式锁"]),
            ("框架/Spring", ["spring", "springboot", "bean", "ioc", "aop", "mybatis", "事务传播"]),
            ("算法与数据结构", ["算法", "数组", "链表", "树", "排序", "复杂度", "动态规划", "leetcode"]),
            ("项目与系统设计", ["项目", "系统", "设计", "架构", "高并发", "限流", "消息队列", "mq"]),
            ("计算机基础", ["操作系统", "网络", "tcp", "http", "进程", "死锁", "linux"]),
        ]
        for name, keywords in categories:
            if any(keyword in text for keyword in keywords):
                return name
        return "业务与开放问题"

    @staticmethod
    def _build_cover_prompt(title: str, markdown_content: str, style: str) -> str:
        cover_direction = WeChatService._wechat_cover_direction(style)
        return f"""
Create a premium WeChat official account cover image for a Chinese technical interview article.
Canvas target: 900x500, clean 9:5 editorial composition, suitable for mobile feed preview.
Topic: {title}.
Visual direction: {cover_direction}.
Style: modern but restrained, crisp composition, high contrast focal area, no clutter.
Color: deep blue, white, light gray, small gold or cyan accent; avoid purple gradient and noisy neon.
Do not include readable Chinese/English text, logo, watermark, UI screenshot, cartoon character, or messy symbols.
""".strip()

    @staticmethod
    def _wechat_cover_direction(content_type: str) -> str:
        directions = {
            "single_interpretation": "interview notes interpretation, document review, selected questions, subtle code and checklist elements",
            "knowledge_deep_dive": "deep technical knowledge explanation, layered architecture, code snippets as abstract shapes, focused learning atmosphere",
            "trend_analysis": "professional data report, question frequency analysis, clean charts, ranking list shapes, knowledge graph",
            "manual_rewrite": "editorial technology article, clean reading experience, abstract article layout and notebook elements",
            "quick_checklist": "compact study checklist, flash cards, priority markers, interview preparation notes",
            "interviewer_chain": "interviewer follow-up chain, conversation flow, connected question nodes, reasoning path",
        }
        return directions.get(content_type, directions["single_interpretation"])

    @staticmethod
    def _pick_palette(theme: str, markdown_content: str) -> Dict:
        text = f"{theme} {markdown_content}".lower()
        if any(keyword in text for keyword in ["code", "java", "python", "前端", "后端", "编程", "程序"]):
            return {
                "kind": "programming",
                "background": "#071512",
                "glow_primary": (34, 197, 94, 42),
                "glow_secondary": (20, 184, 166, 34),
                "line": (74, 222, 128, 70),
                "node": (134, 239, 172, 150),
            }
        if any(keyword in text for keyword in ["ai", "大模型", "算法", "机器学习"]):
            return {
                "kind": "ai",
                "background": "#160f08",
                "glow_primary": (249, 115, 22, 46),
                "glow_secondary": (251, 191, 36, 34),
                "line": (251, 146, 60, 75),
                "node": (253, 186, 116, 160),
            }
        return {
            "kind": "tech",
            "background": "#0a0a1a",
            "glow_primary": (100, 140, 255, 42),
            "glow_secondary": (34, 211, 238, 28),
            "line": (125, 211, 252, 70),
            "node": (191, 219, 254, 150),
        }
