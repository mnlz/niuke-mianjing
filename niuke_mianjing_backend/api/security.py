import base64
import hashlib
import hmac
import json
import time
from typing import Optional

from niuke_mianjing_backend.config import settings


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_admin_token(hours: int = 12) -> str:
    if not settings.API_KEY:
        raise ValueError("API_KEY is not configured")
    payload = _encode(json.dumps({"exp": int(time.time()) + hours * 3600}).encode("utf-8"))
    signature = hmac.new(settings.API_KEY.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest()
    return f"{payload}.{_encode(signature)}"


def is_valid_admin_token(token: Optional[str]) -> bool:
    if not settings.API_KEY or not token or "." not in token:
        return False
    payload, signature = token.split(".", 1)
    expected = _encode(hmac.new(settings.API_KEY.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        return False
    try:
        data = json.loads(_decode(payload))
        return int(data.get("exp", 0)) > int(time.time())
    except (ValueError, TypeError, json.JSONDecodeError):
        return False
