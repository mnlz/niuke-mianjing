import base64
import hashlib
import hmac
import json
import secrets
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


def normalize_email(value: str) -> str:
    return value.strip().lower()


def hash_password(password: str, iterations: int = 260_000) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${_encode(salt)}${_encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, raw_iterations, raw_salt, raw_digest = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            _decode(raw_salt),
            int(raw_iterations),
        )
        return hmac.compare_digest(digest, _decode(raw_digest))
    except (ValueError, TypeError):
        return False


def _user_secret() -> Optional[bytes]:
    if not settings.API_KEY:
        return None
    return hmac.new(settings.API_KEY.encode("utf-8"), b"offerlens-user-auth", hashlib.sha256).digest()


def create_user_token(user_id: int, days: int = 30) -> str:
    secret = _user_secret()
    if not secret:
        raise ValueError("API_KEY is not configured")
    payload = _encode(json.dumps({"sub": user_id, "kind": "user", "exp": int(time.time()) + days * 86400}).encode("utf-8"))
    signature = hmac.new(secret, payload.encode("ascii"), hashlib.sha256).digest()
    return f"{payload}.{_encode(signature)}"


def decode_user_token(token: Optional[str]) -> Optional[int]:
    secret = _user_secret()
    if not secret or not token or "." not in token:
        return None
    payload, signature = token.split(".", 1)
    expected = _encode(hmac.new(secret, payload.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        data = json.loads(_decode(payload))
        if data.get("kind") != "user" or int(data.get("exp", 0)) <= int(time.time()):
            return None
        user_id = int(data.get("sub", 0))
        return user_id if user_id > 0 else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
