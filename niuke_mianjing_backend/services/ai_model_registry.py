import json
import logging
from dataclasses import dataclass, replace
from typing import List, Optional
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken

from niuke_mianjing_backend.config import settings
from niuke_mianjing_backend.repositories.ai_model_repo import AIModelRepository


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AIModelConfig:
    model: str
    endpoint: str
    api_key: str
    description: str = ""
    enabled: bool = True
    is_default: bool = False
    source: str = "env"
    id: int = 0
    channel_name: str = "默认线路"


def normalize_chat_endpoint(endpoint: str) -> str:
    value = endpoint.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("模型 Endpoint 必须是有效的 HTTP(S) 地址")
    return value if value.endswith("/chat/completions") else f"{value}/chat/completions"


def parse_env_models(raw: str) -> List[AIModelConfig]:
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("AI_MODELS_JSON 不是有效 JSON") from exc
    if not isinstance(items, list) or not items:
        raise ValueError("AI_MODELS_JSON 必须是非空数组")

    models = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("AI_MODELS_JSON 中的模型必须是对象")
        model = str(item.get("model") or "").strip()
        api_key = str(item.get("api_key") or "").strip()
        if not model or not api_key:
            raise ValueError("模型名和 API Key 不能为空")
        models.append(AIModelConfig(
            model=model,
            endpoint=normalize_chat_endpoint(str(item.get("endpoint") or "")),
            api_key=api_key,
            description=str(item.get("description") or "").strip(),
            enabled=bool(item.get("enabled", True)),
            is_default=bool(item.get("is_default", False)),
        ))

    if len({item.model for item in models}) != len(models):
        raise ValueError("AI_MODELS_JSON 中的模型名不能重复")
    if sum(item.is_default for item in models) > 1:
        raise ValueError("AI_MODELS_JSON 最多只能配置一个默认模型")
    if not any(item.is_default for item in models):
        models[0] = replace(models[0], is_default=True)
    return models


def _fernet(secret_key: str) -> Fernet:
    if not secret_key:
        raise ValueError("请先配置 AI_MODEL_SECRET_KEY")
    try:
        return Fernet(secret_key.encode())
    except (TypeError, ValueError) as exc:
        raise ValueError("AI_MODEL_SECRET_KEY 格式无效") from exc


def encrypt_api_key(value: str, secret_key: str) -> str:
    return _fernet(secret_key).encrypt(value.encode()).decode()


def decrypt_api_key(value: str, secret_key: str) -> str:
    try:
        return _fernet(secret_key).decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("模型 API Key 解密失败") from exc


def mask_api_key(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 7:
        return "•" * len(value)
    return f"{value[:4]}{'•' * 8}{value[-3:]}"


def configured_env_models() -> List[AIModelConfig]:
    if settings.AI_MODELS_JSON.strip():
        return parse_env_models(settings.AI_MODELS_JSON)
    endpoint = settings.OPENAI_CHAT_COMPLETIONS_URL or settings.OPENAI_BASE_URL
    if not settings.OPENAI_TEXT_MODEL or not endpoint or not settings.OPENAI_API_KEY:
        return []
    return [AIModelConfig(
        model=settings.OPENAI_TEXT_MODEL,
        endpoint=normalize_chat_endpoint(endpoint),
        api_key=settings.OPENAI_API_KEY,
        description="默认分析模型",
        is_default=True,
        source="legacy",
    )]


class AIModelRegistry:
    def __init__(
        self,
        env_models: Optional[List[AIModelConfig]] = None,
        repo: Optional[AIModelRepository] = None,
        secret_key: Optional[str] = None,
    ):
        self.env_models = list(configured_env_models() if env_models is None else env_models)
        self.env_models = [replace(item, id=item.id or -(index + 1)) for index, item in enumerate(self.env_models)]
        self.repo = repo or AIModelRepository()
        self.secret_key = settings.AI_MODEL_SECRET_KEY if secret_key is None else secret_key
        self._models = {item.id: item for item in self._normalize_defaults(self.env_models)}

    @staticmethod
    def _normalize_defaults(models: List[AIModelConfig], preferred: int = 0) -> List[AIModelConfig]:
        enabled = [item for item in models if item.enabled]
        selected = preferred if any(item.id == preferred and item.enabled for item in models) else 0
        if not selected:
            selected = next((item.id for item in enabled if item.is_default), enabled[0].id if enabled else 0)
        return [replace(item, is_default=item.id == selected) for item in models]

    async def refresh(self) -> None:
        try:
            rows = await self.repo.list_all()
        except Exception as exc:
            logger.warning("读取数据库 AI 模型配置失败，使用环境变量配置：%s", exc)
            rows = []

        database_models = {str(row.get("model") or "").strip() for row in rows}
        merged = {item.id: item for item in self.env_models if item.model not in database_models}
        env_by_model = {item.model: item for item in self.env_models}
        database_default = 0
        for fallback_id, row in enumerate(rows, 1):
            model = str(row.get("model") or "").strip()
            base = env_by_model.get(model)
            encrypted = str(row.get("api_key_encrypted") or "")
            api_key = decrypt_api_key(encrypted, self.secret_key or "") if encrypted else (base.api_key if base else "")
            if not model or not api_key:
                logger.warning("忽略缺少模型名或 API Key 的数据库模型配置")
                continue
            model_id = int(row.get("id") or fallback_id)
            merged[model_id] = AIModelConfig(
                model=model,
                endpoint=normalize_chat_endpoint(str(row.get("endpoint") or "")),
                api_key=api_key,
                description=str(row.get("description") or ""),
                enabled=bool(row.get("enabled", True)),
                is_default=bool(row.get("is_default", False)),
                source="database",
                id=model_id,
                channel_name=str(row.get("channel_name") or "默认线路").strip(),
            )
            if row.get("is_default"):
                database_default = model_id
        normalized = self._normalize_defaults(list(merged.values()), database_default)
        self._models = {item.id: item for item in normalized}

    def resolve(self, model: Optional[str] = None, *, model_id: Optional[int] = None) -> AIModelConfig:
        if model_id is not None:
            item = self._models.get(model_id)
            if not item:
                raise ValueError(f"AI 模型不存在：{model_id}")
            if not item.enabled:
                raise ValueError(f"AI 模型未启用：{item.model} · {item.channel_name}")
            return item
        if model:
            matches = [item for item in self._models.values() if item.model == model]
            item = next((value for value in matches if value.enabled and value.is_default),
                        next((value for value in matches if value.enabled), None))
            if not item:
                if matches:
                    raise ValueError(f"AI 模型未启用：{model}")
                raise ValueError(f"AI 模型不存在：{model}")
            return item
        item = next((value for value in self._models.values() if value.enabled and value.is_default), None)
        if not item:
            raise ValueError("当前没有可用的 AI 模型")
        return item

    def list_public(self) -> List[dict]:
        return [{"id": item.id, "model": item.model, "channel_name": item.channel_name,
                 "description": item.description, "is_default": item.is_default}
                for item in self._models.values() if item.enabled]

    def list_admin(self) -> List[dict]:
        return [{
            "id": item.id,
            "model": item.model,
            "channel_name": item.channel_name,
            "endpoint": item.endpoint,
            "description": item.description,
            "enabled": item.enabled,
            "is_default": item.is_default,
            "source": item.source,
            "api_key_masked": mask_api_key(item.api_key),
        } for item in self._models.values()]

    async def save_override(self, data: dict, model_id: Optional[int] = None) -> None:
        model = str(data.get("model") or "").strip()
        channel_name = str(data.get("channel_name") or "").strip()
        endpoint = normalize_chat_endpoint(str(data.get("endpoint") or ""))
        api_key = str(data.get("api_key") or "").strip()
        if not model:
            raise ValueError("模型名不能为空")
        if not channel_name:
            raise ValueError("渠道名称不能为空")
        if model_id is not None and model_id not in self._models:
            raise ValueError(f"AI 模型不存在：{model_id}")
        if not api_key and model_id is None:
            raise ValueError("新模型必须提供 API Key")
        encrypted = encrypt_api_key(api_key, self.secret_key or "") if api_key else ""
        saved = await self.repo.save({
            "model": model,
            "channel_name": channel_name,
            "endpoint": endpoint,
            "api_key_encrypted": encrypted,
            "description": str(data.get("description") or "").strip(),
            "enabled": bool(data.get("enabled", True)),
            "is_default": bool(data.get("is_default", False)),
        }, model_id if model_id and model_id > 0 else None)
        if not saved:
            raise ValueError(f"AI 模型不存在：{model_id}")
        await self.refresh()

    async def delete_override(self, model_id: int) -> bool:
        deleted = await self.repo.delete(model_id)
        await self.refresh()
        return deleted


ai_model_registry = AIModelRegistry()
