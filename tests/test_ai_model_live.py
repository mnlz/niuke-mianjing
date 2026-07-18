import os
import sys
import time
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from niuke_mianjing_backend.services.ai_model_registry import ai_model_registry
from niuke_mianjing_backend.services.openai_client import extract_chat_completion_text, post_chat_completion


def run_live_test():
    if os.getenv("RUN_AI_MODEL_LIVE_TEST") != "1":
        pytest.skip("set RUN_AI_MODEL_LIVE_TEST=1 to call a real model")
    requested_id = os.getenv("AI_MODEL_TEST_ID")
    requested = os.getenv("AI_MODEL_TEST_MODEL") or None
    if requested_id:
        asyncio.run(ai_model_registry.refresh())
    selected = ai_model_registry.resolve(requested, model_id=int(requested_id) if requested_id else None)
    started = time.perf_counter()
    response = post_chat_completion(
        [{"role": "user", "content": "只回复 OK"}],
        temperature=0,
        timeout=30,
        model_id=selected.id,
    )
    response.raise_for_status()
    assert extract_chat_completion_text(response.json())
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    print(f"model={selected.model} elapsed_ms={elapsed_ms} success")


def test_live_model_request():
    run_live_test()


if __name__ == "__main__":
    run_live_test()
