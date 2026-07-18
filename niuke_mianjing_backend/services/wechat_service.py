import json
import re
import tempfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import markdown
import requests
from bs4 import BeautifulSoup

from niuke_mianjing_backend.config import settings
from niuke_mianjing_backend.repositories.niuke_repo import NiukeRepository
from niuke_mianjing_backend.repositories.wechat_article_repo import WeChatArticleRepository
from niuke_mianjing_backend.services.ai_model_registry import ai_model_registry
from niuke_mianjing_backend.services.openai_client import (
    ensure_openai_configured,
    extract_chat_completion_text,
    image_generations_url,
    openai_headers,
)
from niuke_mianjing_backend.services.wechat_api_client import (
    get_token,
    push_draft,
    push_newspic_draft,
    upload_cover,
)
from niuke_mianjing_backend.services.wechat_prompts import (
    _build_article_json_prompt,
    _build_cover_prompt,
    _build_question_analysis_html_prompt,
    _build_question_analysis_markdown_prompt,
    _build_quick_checklist_html_prompt,
    _build_quick_checklist_markdown_prompt,
    _build_stream_html_prompt,
    _build_stream_markdown_prompt,
)
from niuke_mianjing_backend.services.wechat_media import (
    cover_suffix,
    generate_cover,
    image_url_to_base64,
    normalize_base64_image,
    resize_cover_base64,
    write_base64_image,
)
from niuke_mianjing_backend.services.wechat_formatter import (
    get_raphael_theme_groups,
    render_markdown_as_raphael_html,
    render_raphael_wechat_html,
)


class WeChatService:
    def __init__(self):
        self.article_repo = WeChatArticleRepository()
        self.niuke_repo = NiukeRepository()

    async def init_table(self):
        await self.article_repo.init_table()

    def get_wechat_theme_groups(self) -> List[Dict[str, Any]]:
        return get_raphael_theme_groups()

    def parse_markdown(self, content: str, fallback_title: str = "未命名文章") -> Tuple[Dict, str, str]:
        metadata: Dict[str, object] = {}
        body = self._clean_markdown_text(content)

        if body.startswith("---"):
            match = re.match(r"^---\s*\n(.*?)\n---\s*\n?([\s\S]*)$", body)
            if match:
                raw_meta, body = match.groups()
                metadata = self._parse_frontmatter(raw_meta)
                body = self._remove_empty_markdown_list_items(body)

        title = str(metadata.get("title") or "").strip() or self._extract_first_heading(body) or fallback_title
        return metadata, body, title

    def render_html(
        self,
        markdown_content: str,
        fallback_title: str = "未命名文章",
        wechat_theme: Optional[str] = None,
    ) -> Dict[str, Any]:
        metadata, body, title = self.parse_markdown(markdown_content, fallback_title)
        body_html = markdown.markdown(
            body,
            extensions=["extra", "tables", "fenced_code", "nl2br", "sane_lists"],
            output_format="html5",
        )
        article_html = render_markdown_as_raphael_html(title, body_html, "manual_rewrite", wechat_theme)
        return {
            "title": title,
            "html": article_html,
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
        wechat_theme: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._ensure_text_model_configured()
        self._ensure_image_model_configured()

        fallback = self.parse_markdown(markdown_content, title or "未命名文章")[2]
        prompt = _build_article_json_prompt(markdown_content, title or fallback, style)
        article = self._generate_article_json(prompt)

        article_title = title or article.get("title") or fallback
        article_digest = digest or article.get("digest") or self._plain_text(article.get("html", ""))[:100]
        html = self._ensure_wechat_html(article_title, article.get("html", ""), style, wechat_theme)
        image_prompt = article.get("cover_prompt") or _build_cover_prompt(article_title, markdown_content, style)
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
            wechat_theme=wechat_theme,
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
        wechat_theme: Optional[str] = None,
        cover_prompt: Optional[str] = None,
        cover_base64: Optional[str] = None,
        cover_mime: Optional[str] = None,
        status: str = "edited",
    ) -> Dict[str, Any]:
        final_html = self._ensure_wechat_html(title, html, style, wechat_theme)
        prompt = cover_prompt or _build_cover_prompt(title, markdown_content, style)
        final_cover_base64 = normalize_base64_image(cover_base64) if cover_base64 else None
        final_cover_mime = cover_mime or "image/png"
        model_info = {
            "text_model": ai_model_registry.resolve().model,
            "image_model": settings.OPENAI_IMAGE_MODEL,
            "style": style,
            "wechat_theme": wechat_theme or "auto",
            "flow": "stream-edit-save",
            "formatter": "raphael_python",
            "cover_source": "provided" if cover_base64 else "not_generated",
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

    def generate_ai_cover(
        self,
        markdown_content: str,
        title: str,
        style: str,
        cover_prompt: Optional[str] = None,
    ) -> Dict[str, str]:
        self._ensure_image_model_configured()
        prompt = cover_prompt or _build_cover_prompt(title, markdown_content, style)
        cover_base64 = self._generate_cover_with_openai(prompt)
        return {
            "cover_base64": cover_base64,
            "cover_mime": "image/png",
            "cover_prompt": prompt,
        }

    def stream_wechat_html(
        self,
        markdown_content: str,
        title: Optional[str],
        style: str,
        wechat_theme: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        self._ensure_text_model_configured()
        fallback = self.parse_markdown(markdown_content, title or "未命名文章")[2]
        article_title = title or fallback
        prompt = _build_stream_html_prompt(markdown_content, article_title, style)
        yield from self.stream_prompt_html(prompt, article_title, style, wechat_theme)

    def stream_wechat_markdown(
        self,
        markdown_content: str,
        title: Optional[str],
        style: str,
    ) -> Generator[Dict[str, Any], None, None]:
        self._ensure_text_model_configured()
        fallback = self.parse_markdown(markdown_content, title or "未命名文章")[2]
        article_title = title or fallback
        prompt = _build_stream_markdown_prompt(markdown_content, article_title, style)
        yield from self.stream_prompt_markdown(prompt, article_title)

    def stream_prompt_html(
        self,
        prompt: str,
        article_title: str,
        content_type: str = "single_interpretation",
        wechat_theme: Optional[str] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        system_prompt = (
            "你是一个中文技术公众号主编。只输出微信公众号 HTML，不要输出解释或 Markdown 代码块。"
            "文章要像真人编辑写的，有判断、有取舍、有具体复习建议。"
        )
        full_text = ""
        yield {"type": "meta", "title": article_title}
        for delta in self._stream_openai_text(system_prompt, prompt, "OpenAI 流式生成失败"):
            full_text += delta
            yield {"type": "delta", "delta": delta}

        html = self._ensure_wechat_html(article_title, self._clean_html_text(full_text), content_type, wechat_theme)
        yield {"type": "done", "title": article_title, "html": html}

    def stream_prompt_markdown(self, prompt: str, article_title: str) -> Generator[Dict[str, Any], None, None]:
        system_prompt = (
            "你是一个中文技术公众号主编。只输出 Markdown 正文，不要输出 HTML，不要输出解释。"
            "文章要像真人编辑写的，有判断、有取舍、有具体复习建议，少一点 AI 腔。"
        )
        full_text = ""
        yield {"type": "meta", "title": article_title}
        for delta in self._stream_openai_text(system_prompt, prompt, "OpenAI 流式生成 Markdown 失败"):
            full_text += delta
            yield {"type": "delta", "delta": delta}

        markdown_text = self._clean_markdown_text(full_text)
        yield {"type": "done", "title": article_title, "markdown": markdown_text}

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
        return _build_question_analysis_html_prompt(analysis)

    def build_question_analysis_markdown_prompt(self, analysis: Dict[str, Any]) -> str:
        return _build_question_analysis_markdown_prompt(analysis)

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
        return _build_quick_checklist_html_prompt(analysis)

    def build_quick_checklist_markdown_prompt(self, analysis: Dict[str, Any]) -> str:
        return _build_quick_checklist_markdown_prompt(analysis)

    async def list_articles(self, limit: int = 20, offset: int = 0):
        return await self.article_repo.list_articles(limit, offset)

    async def get_article(self, article_id: int, include_content: bool = True):
        return await self.article_repo.get_article(article_id, include_content)

    async def publish_saved_article(self, article_id: int) -> Dict[str, Any]:
        article = await self.article_repo.get_article(article_id)
        if not article:
            raise ValueError("公众号稿件不存在")
        if not article.get("html") or not article.get("cover_base64"):
            raise ValueError("稿件缺少 HTML 或封面图，请先生成/上传封面并保存")

        try:
            token = get_token()
            with tempfile.TemporaryDirectory() as temp_dir:
                cover_path = str(Path(temp_dir) / f"wechat_cover{cover_suffix(article.get('cover_mime'))}")
                write_base64_image(article["cover_base64"], cover_path)
                cover_media_id = upload_cover(token, cover_path)

            draft = push_draft(
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

    def create_newspic_draft(
        self,
        title: str,
        content: str,
        images: List[str],
        image_mimes: Optional[List[str]] = None,
        need_open_comment: int = 1,
        only_fans_can_comment: int = 0,
    ) -> Dict:
        clean_title = (title or "").strip()
        if not clean_title:
            raise ValueError("Draft title is required")
        if not images:
            raise ValueError("At least one card image is required")
        if len(images) > 20:
            raise ValueError("WeChat newspic draft supports at most 20 images in this app")

        token = get_token()
        image_media_ids: List[str] = []

        with tempfile.TemporaryDirectory() as temp_dir:
            for index, image_base64 in enumerate(images):
                normalized = normalize_base64_image(image_base64)
                mime = image_mimes[index] if image_mimes and index < len(image_mimes) else "image/png"
                image_path = str(Path(temp_dir) / f"newspic_card_{index + 1}{cover_suffix(mime)}")
                write_base64_image(normalized, image_path)
                image_media_ids.append(upload_cover(token, image_path))

        draft = push_newspic_draft(
            token=token,
            title=clean_title,
            content=content or "",
            image_media_ids=image_media_ids,
            need_open_comment=need_open_comment,
            only_fans_can_comment=only_fans_can_comment,
        )
        return {
            "title": clean_title,
            "media_id": draft["media_id"],
            "image_media_ids": image_media_ids,
            "wechat_response": draft,
        }

    def create_draft(
        self,
        markdown_content: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        digest: Optional[str] = None,
        content_source_url: Optional[str] = None,
        cover_theme: str = "auto",
        wechat_theme: Optional[str] = None,
    ) -> Dict:
        rendered = self.render_html(markdown_content, title or "未命名文章", wechat_theme)
        article_title = title or rendered["title"]
        token = get_token()

        with tempfile.TemporaryDirectory() as temp_dir:
            cover_path = str(Path(temp_dir) / "wechat_cover.png")
            generate_cover(cover_path, cover_theme, markdown_content)
            cover_media_id = upload_cover(token, cover_path)

        draft = push_draft(
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

    @staticmethod
    def _ensure_text_model_configured():
        ai_model_registry.resolve()

    @staticmethod
    def _ensure_image_model_configured():
        ensure_openai_configured()

    def _openai_headers(self) -> Dict[str, str]:
        return openai_headers()

    def _generate_article_json(self, prompt: str) -> Dict[str, str]:
        selected = ai_model_registry.resolve()
        payload = {
            "model": selected.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个中文技术公众号主编，只返回合法 JSON，不要输出解释。",
                },
                {"role": "user", "content": prompt},
            ],
        }
        response = requests.post(
            selected.endpoint,
            headers={
                "Authorization": f"Bearer {selected.api_key}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=payload,
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
            image_base64 = image_url_to_base64(image_url)
        if not image_base64:
            raise ValueError(f"OpenAI 封面响应缺少 b64_json：{data}")
        return resize_cover_base64(image_base64)

    @staticmethod
    def _image_generations_url() -> str:
        return image_generations_url()

    @staticmethod
    def _extract_chat_completion_text(data: Dict[str, Any]) -> str:
        return extract_chat_completion_text(data)

    def _stream_openai_text(
        self,
        system_prompt: str,
        user_prompt: str,
        error_prefix: str,
    ) -> Generator[str, None, None]:
        selected = ai_model_registry.resolve()
        payload = {
            "model": selected.model,
            "stream": True,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        response = requests.post(
            selected.endpoint,
            headers={
                "Authorization": f"Bearer {selected.api_key}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=payload,
            stream=True,
            timeout=(10, 240),
        )
        if response.status_code >= 400:
            raise ValueError(f"{error_prefix}：{response.text[:1000]}")

        response.encoding = "utf-8"
        for raw_line in response.iter_lines(decode_unicode=False):
            line = raw_line.decode("utf-8", errors="replace")
            if not line:
                continue
            if line.startswith("data:"):
                payload_text = line[5:].strip()
            else:
                payload_text = line.strip()
            if payload_text == "[DONE]":
                break
            try:
                data = json.loads(payload_text)
            except json.JSONDecodeError:
                continue
            delta = self._extract_stream_delta(data)
            if delta:
                yield delta

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

    def _ensure_wechat_html(
        self,
        title: str,
        html: str,
        content_type: str = "single_interpretation",
        wechat_theme: Optional[str] = None,
    ) -> str:
        cleaned = self._clean_html_text(html)
        if "<section" not in cleaned and "<p" not in cleaned:
            cleaned = self._remove_empty_markdown_list_items(cleaned)
            cleaned = markdown.markdown(cleaned, extensions=["extra", "tables", "fenced_code", "nl2br", "sane_lists"])
        resolved_type = "trend_analysis" if self._is_question_analysis_title(title) else content_type
        return render_raphael_wechat_html(title, cleaned, resolved_type, wechat_theme)

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
    def _clean_markdown_text(value: str) -> str:
        cleaned = value.strip()
        cleaned = re.sub(r"^```(?:markdown|md)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = re.sub(r"<!--\s*WECHAT_ARTICLE_TITLE:.*?-->\s*", "", cleaned, flags=re.IGNORECASE | re.S)
        cleaned = re.sub(r"[\u200b-\u200f\ufeff]", "", cleaned)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)
        return WeChatService._remove_empty_markdown_list_items(cleaned).strip()

    @staticmethod
    def _remove_empty_markdown_list_items(value: str) -> str:
        lines = value.splitlines()
        cleaned_lines: List[str] = []
        for line in lines:
            stripped = re.sub(r"[\s\u00a0\u200b\u200c\u200d\ufeff]+", "", line)
            if re.fullmatch(r"[-*+]", stripped):
                continue
            if re.fullmatch(r"\d{1,3}[.)、．。]", stripped):
                continue
            cleaned_lines.append(line)
        text = "\n".join(cleaned_lines)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    @staticmethod
    def _plain_text(html: str) -> str:
        return BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)










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
