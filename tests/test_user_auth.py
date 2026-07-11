import asyncio
import re

import pytest
from pymysql.err import IntegrityError

from niuke_mianjing_backend.api.middleware.error_handler import AppException
from niuke_mianjing_backend.api.routes import user_auth


class FakeAccountRepo:
    def __init__(self):
        self.account = None

    async def get_account_by_email(self, email):
        return self.account if self.account and self.account["email"] == email else None

    async def create_account(self, email, password_hash, display_name):
        self.account = {"id": 7, "email": email, "password_hash": password_hash, "display_name": display_name}
        return self.account

    async def get_account_by_id(self, user_id):
        return self.account if self.account and self.account["id"] == user_id else None

    async def set_account_display_name(self, user_id, display_name):
        self.account["display_name"] = display_name
        return self.account


def test_register_login_and_me(monkeypatch):
    repo = FakeAccountRepo()
    monkeypatch.setattr(user_auth, "account_repo", repo)
    monkeypatch.setattr(user_auth, "create_user_token", lambda user_id: f"token-{user_id}")

    registered = asyncio.run(user_auth.register(user_auth.RegisterRequest(email=" Test@Example.com ", password="password123")))
    assert registered.data["id"] == 7
    assert registered.data["email"] == "test@example.com"
    assert registered.data["token"] == "token-7"
    assert re.fullmatch(r"[\u4e00-\u9fff]+·\d{4}", registered.data["display_name"])

    logged_in = asyncio.run(user_auth.login(user_auth.LoginRequest(email="TEST@example.com", password="password123")))
    assert logged_in.data["email"] == "test@example.com"

    current = asyncio.run(user_auth.me(7))
    assert current.data == {
        "id": 7,
        "email": "test@example.com",
        "display_name": registered.data["display_name"],
    }


def test_login_lazily_adds_display_name(monkeypatch):
    repo = FakeAccountRepo()
    repo.account = {
        "id": 7,
        "email": "legacy@example.com",
        "password_hash": user_auth.hash_password("password123"),
        "display_name": None,
    }
    monkeypatch.setattr(user_auth, "account_repo", repo)
    monkeypatch.setattr(user_auth, "create_user_token", lambda user_id: f"token-{user_id}")

    logged_in = asyncio.run(user_auth.login(user_auth.LoginRequest(email="legacy@example.com", password="password123")))

    assert logged_in.data["display_name"] == repo.account["display_name"]
    assert re.fullmatch(r"[\u4e00-\u9fff]+·\d{4}", logged_in.data["display_name"])


def test_duplicate_and_bad_credentials_use_safe_errors(monkeypatch):
    repo = FakeAccountRepo()
    monkeypatch.setattr(user_auth, "account_repo", repo)
    monkeypatch.setattr(user_auth, "create_user_token", lambda user_id: f"token-{user_id}")
    asyncio.run(user_auth.register(user_auth.RegisterRequest(email="test@example.com", password="password123")))

    with pytest.raises(AppException) as duplicate:
        asyncio.run(user_auth.register(user_auth.RegisterRequest(email="test@example.com", password="password123")))
    assert duplicate.value.code == 409

    with pytest.raises(AppException) as invalid:
        asyncio.run(user_auth.login(user_auth.LoginRequest(email="test@example.com", password="wrongpass")))
    assert invalid.value.code == 401
    assert invalid.value.message == "邮箱或密码错误"


def test_registration_race_still_returns_conflict(monkeypatch):
    class RaceRepo(FakeAccountRepo):
        async def create_account(self, email, password_hash, display_name):
            raise IntegrityError(1062, "duplicate")

    monkeypatch.setattr(user_auth, "account_repo", RaceRepo())
    with pytest.raises(AppException) as duplicate:
        asyncio.run(user_auth.register(user_auth.RegisterRequest(email="test@example.com", password="password123")))
    assert duplicate.value.code == 409
