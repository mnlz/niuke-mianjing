from __future__ import annotations

import requests
from typing import Any, Dict, List, Tuple

from niuke_mianjing_backend.config import settings
from niuke_mianjing_backend.services.ai_model_registry import ai_model_registry


def ensure_openai_configured():
    if not settings.OPENAI_API_KEY:
        raise ValueError("请先在 .env 配置 OPENAI_API_KEY")


def openai_headers() -> Dict[str, str]:
    ensure_openai_configured()
    return {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json; charset=utf-8",
    }


def chat_completions_url() -> str:
    url = (settings.OPENAI_CHAT_COMPLETIONS_URL or "").strip()
    if url:
        return url
    base_url = settings.OPENAI_BASE_URL.rstrip("/")
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def image_generations_url() -> str:
    if settings.OPENAI_IMAGE_GENERATIONS_URL:
        return settings.OPENAI_IMAGE_GENERATIONS_URL
    chat_url = chat_completions_url().rstrip("/")
    if chat_url.endswith("/chat/completions"):
        return f"{chat_url.removesuffix('/chat/completions')}/images/generations"
    return f"{settings.OPENAI_BASE_URL.rstrip('/')}/images/generations"


def extract_chat_completion_text(data: Dict[str, Any]) -> str:
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


def post_chat_completion(
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0.4,
    timeout: int | Tuple[int, int] = 90,
    stream: bool = False,
    model: str | None = None,
    model_id: int | None = None,
) -> requests.Response:
    selected = ai_model_registry.resolve(model, model_id=model_id)
    try:
        return requests.post(
            selected.endpoint,
            headers={
                "Authorization": f"Bearer {selected.api_key}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={
                "model": selected.model,
                "messages": messages,
                "temperature": temperature,
                **({"stream": True} if stream else {}),
            },
            stream=stream,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise ValueError(f"OpenAI 请求失败：{exc}") from exc
