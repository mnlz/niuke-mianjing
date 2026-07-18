from niuke_mianjing_backend.api import security


def test_user_password_and_token_are_separate_from_admin(monkeypatch):
    monkeypatch.setattr(security.settings, "API_KEY", "test-secret")

    assert security.normalize_email("  Test@Example.COM ") == "test@example.com"

    encoded = security.hash_password("password123")
    assert security.verify_password("password123", encoded)
    assert not security.verify_password("wrong-password", encoded)
    assert not security.verify_password("password123", "broken")

    token = security.create_user_token(42)
    assert security.decode_user_token(token) == 42
    assert not security.is_valid_admin_token(token)
    assert security.decode_user_token(security.create_user_token(42, days=0)) is None
    assert security.decode_user_token("broken") is None
