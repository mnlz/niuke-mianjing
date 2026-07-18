import json

import pytest
from cryptography.fernet import Fernet

from niuke_mianjing_backend.services.ai_model_registry import (
    AIModelConfig,
    AIModelRegistry,
    decrypt_api_key,
    encrypt_api_key,
    mask_api_key,
    normalize_chat_endpoint,
    parse_env_models,
)
from niuke_mianjing_backend.services.openai_client import post_chat_completion


class FakeModelRepository:
    def __init__(self, rows):
        self.rows = rows
        self.saved_model_id = None

    async def list_all(self):
        return self.rows

    async def save(self, item, model_id=None):
        self.saved_model_id = model_id
        return True


def test_normalize_chat_endpoint_accepts_base_or_full_url():
    assert normalize_chat_endpoint("https://api.example.com/v1") == "https://api.example.com/v1/chat/completions"
    assert normalize_chat_endpoint("https://api.example.com/v1/chat/completions") == "https://api.example.com/v1/chat/completions"


def test_parse_env_models_uses_real_model_name():
    models = parse_env_models(json.dumps([{
        "model": "deepseek/deepseek-chat",
        "endpoint": "https://api.example.com/v1",
        "api_key": "sk-test",
        "description": "深度分析",
        "enabled": True,
        "is_default": True,
    }]))

    assert models[0].model == "deepseek/deepseek-chat"
    assert models[0].endpoint.endswith("/chat/completions")
    assert models[0].is_default is True


@pytest.mark.parametrize("raw", ["not-json", "{}", "[]"])
def test_parse_env_models_rejects_invalid_or_empty_config(raw):
    with pytest.raises(ValueError):
        parse_env_models(raw)


def test_parse_env_models_rejects_duplicate_or_multiple_defaults():
    with pytest.raises(ValueError):
        parse_env_models(json.dumps([
            {"model": "same", "endpoint": "https://one.example/v1", "api_key": "a"},
            {"model": "same", "endpoint": "https://two.example/v1", "api_key": "b"},
        ]))
    with pytest.raises(ValueError):
        parse_env_models(json.dumps([
            {"model": "one", "endpoint": "https://one.example/v1", "api_key": "a", "is_default": True},
            {"model": "two", "endpoint": "https://two.example/v1", "api_key": "b", "is_default": True},
        ]))


def test_api_key_encryption_round_trip_and_masking():
    secret = Fernet.generate_key().decode()
    encrypted = encrypt_api_key("sk-secret-value", secret)

    assert encrypted != "sk-secret-value"
    assert decrypt_api_key(encrypted, secret) == "sk-secret-value"
    assert mask_api_key("sk-secret-value") == "sk-s••••••••lue"
    assert mask_api_key("") == ""


def test_registry_merges_database_overrides_and_keeps_one_default():
    secret = Fernet.generate_key().decode()
    env_models = [AIModelConfig(
        model="env-model",
        endpoint="https://env.example/v1/chat/completions",
        api_key="sk-env-secret",
        description="环境模型",
        is_default=True,
    )]
    repo = FakeModelRepository([
        {
            "model": "env-model", "endpoint": "https://db.example/v1", "api_key_encrypted": "",
            "description": "数据库覆盖", "enabled": True, "is_default": False,
        },
        {
            "model": "db-model", "endpoint": "https://new.example/v1",
            "api_key_encrypted": encrypt_api_key("sk-db-secret", secret),
            "description": "数据库模型", "enabled": True, "is_default": True,
        },
    ])
    registry = AIModelRegistry(env_models, repo, secret)

    import asyncio
    asyncio.run(registry.refresh())

    inherited = registry.resolve("env-model")
    assert inherited.endpoint == "https://db.example/v1/chat/completions"
    assert inherited.api_key == "sk-env-secret"
    assert inherited.source == "database"
    assert registry.resolve().model == "db-model"


def test_registry_keeps_duplicate_model_names_and_resolves_by_permanent_id():
    secret = Fernet.generate_key().decode()
    repo = FakeModelRepository([
        {
            "id": 41, "model": "gpt-5.5", "channel_name": "主线路",
            "endpoint": "https://one.example/v1", "api_key_encrypted": encrypt_api_key("sk-one", secret),
            "description": "", "enabled": True, "is_default": True,
        },
        {
            "id": 42, "model": "gpt-5.5", "channel_name": "备用线路",
            "endpoint": "https://two.example/v1", "api_key_encrypted": encrypt_api_key("sk-two", secret),
            "description": "", "enabled": True, "is_default": False,
        },
    ])
    registry = AIModelRegistry([], repo, secret)

    import asyncio
    asyncio.run(registry.refresh())

    assert [(item["id"], item["channel_name"]) for item in registry.list_public()] == [
        (41, "主线路"), (42, "备用线路"),
    ]
    assert registry.resolve(model_id=41).endpoint == "https://one.example/v1/chat/completions"
    assert registry.resolve(model_id=42).api_key == "sk-two"


def test_registry_safe_views_and_disabled_model_rejection():
    models = [
        AIModelConfig("enabled", "https://one.example/v1/chat/completions", "sk-enabled", is_default=True),
        AIModelConfig("disabled", "https://two.example/v1/chat/completions", "sk-disabled", enabled=False),
    ]
    registry = AIModelRegistry(models, FakeModelRepository([]), "")

    public = registry.list_public()
    admin = registry.list_admin()

    assert public == [{
        "id": -1, "model": "enabled", "channel_name": "默认线路",
        "description": "", "is_default": True,
    }]
    assert all("api_key" not in item and "endpoint" not in item for item in public)
    assert all("api_key" not in item for item in admin)
    assert admin[0]["api_key_masked"] == "sk-e••••••••led"
    with pytest.raises(ValueError, match="未启用"):
        registry.resolve("disabled")
    with pytest.raises(ValueError, match="不存在"):
        registry.resolve("missing")


def test_editing_environment_fallback_creates_database_record():
    repo = FakeModelRepository([])
    registry = AIModelRegistry([
        AIModelConfig("legacy", "https://one.example/v1/chat/completions", "sk-legacy", is_default=True),
    ], repo, Fernet.generate_key().decode())

    import asyncio
    asyncio.run(registry.save_override({
        "model": "legacy", "channel_name": "主线路", "endpoint": "https://new.example/v1",
        "api_key": "", "enabled": True, "is_default": True,
    }, model_id=-1))

    assert repo.saved_model_id is None


def test_chat_request_uses_selected_model_endpoint_and_key(monkeypatch):
    from niuke_mianjing_backend.services import openai_client

    previous = openai_client.ai_model_registry._models
    openai_client.ai_model_registry._models = {
        91: AIModelConfig(
            "custom/model", "https://custom.example/v1/chat/completions", "sk-custom",
            is_default=True, id=91, channel_name="主线路",
        )
    }
    captured = {}

    class Response:
        status_code = 200

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return Response()

    monkeypatch.setattr(openai_client.requests, "post", fake_post)
    try:
        post_chat_completion([{"role": "user", "content": "hello"}], model_id=91)
    finally:
        openai_client.ai_model_registry._models = previous

    assert captured["url"] == "https://custom.example/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer sk-custom"
    assert captured["json"]["model"] == "custom/model"
