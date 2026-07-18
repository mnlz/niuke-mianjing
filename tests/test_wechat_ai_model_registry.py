import asyncio
from types import SimpleNamespace

from niuke_mianjing_backend.services import wechat_service as wechat_module


class FakeStreamResponse:
    status_code = 200
    text = ""
    encoding = "utf-8"

    def iter_lines(self, decode_unicode=False):
        del decode_unicode
        yield b'data: {"choices":[{"delta":{"content":"DeepSeek OK"}}]}'
        yield b"data: [DONE]"


class FakeJsonResponse:
    status_code = 200

    def json(self):
        return {
            "choices": [{
                "message": {
                    "content": '{"title":"测试","digest":"摘要","html":"<p>正文</p>","cover_prompt":"封面"}'
                }
            }]
        }


def test_wechat_markdown_stream_uses_default_model_registry(monkeypatch):
    selected = SimpleNamespace(
        model="deepseek-v4-flash",
        endpoint="https://api.deepseek.com/chat/completions",
        api_key="encrypted-at-rest-key",
    )
    monkeypatch.setattr(wechat_module.settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(wechat_module.ai_model_registry, "resolve", lambda: selected)
    captured = {}

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return FakeStreamResponse()

    monkeypatch.setattr(wechat_module.requests, "post", fake_post)

    events = list(wechat_module.WeChatService().stream_wechat_markdown("# 输入", "测试", "manual_rewrite"))

    assert captured["url"] == selected.endpoint
    assert captured["headers"]["Authorization"] == f"Bearer {selected.api_key}"
    assert captured["json"]["model"] == selected.model
    assert events[-1]["type"] == "done"
    assert "DeepSeek OK" in events[-1]["markdown"]


def test_ai_article_requests_json_output(monkeypatch):
    selected = SimpleNamespace(
        model="deepseek-v4-flash",
        endpoint="https://api.deepseek.com/chat/completions",
        api_key="encrypted-at-rest-key",
    )
    monkeypatch.setattr(wechat_module.settings, "OPENAI_API_KEY", "image-provider-key")
    monkeypatch.setattr(wechat_module.ai_model_registry, "resolve", lambda: selected)
    captured = {}

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return FakeJsonResponse()

    service = wechat_module.WeChatService()
    monkeypatch.setattr(wechat_module.requests, "post", fake_post)
    monkeypatch.setattr(service, "_generate_cover_with_openai", lambda prompt: "cover")

    async def fake_save(**kwargs):
        return kwargs

    monkeypatch.setattr(service, "save_ai_article", fake_save)

    result = asyncio.run(service.generate_ai_article("# 输入", title="测试"))

    assert captured["url"] == selected.endpoint
    assert captured["json"]["response_format"] == {"type": "json_object"}
    assert captured["json"]["max_tokens"] == 8192
    assert result["title"] == "测试"
