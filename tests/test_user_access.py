import asyncio

import pytest

from niuke_mianjing_backend.api.middleware.error_handler import UnauthorizedException
from niuke_mianjing_backend.api.routes import user_auth
from niuke_mianjing_backend.services.review_service import ReviewService


class FakeProgressRepo:
    async def get_progress_map(self, user_id, record_ids):
        return {record_ids[0]: {"record_id": record_ids[0], "favorite": True}}

    async def upsert_progress(self, user_id, record_id, favorite, mastery, note):
        return {"record_id": record_id, "favorite": bool(favorite), "user_id": user_id}


def test_anonymous_access_stops_after_two_pages():
    user_auth.require_public_window(12, 12, None)
    user_auth.require_public_window(24, 100, 7)

    with pytest.raises(UnauthorizedException):
        user_auth.require_public_window(24, 12, None)
    with pytest.raises(UnauthorizedException):
        user_auth.require_public_window(0, 25, None)
    with pytest.raises(UnauthorizedException):
        user_auth.require_public_window(24, 24, None)


def test_review_progress_uses_authenticated_user_id():
    service = ReviewService()
    service.review_repo = FakeProgressRepo()

    rows = asyncio.run(service.get_progress(7, [11, 12]))
    assert rows[0]["favorite"] is True
    assert rows[1]["record_id"] == 12

    saved = asyncio.run(service.update_progress(7, 11, favorite=True))
    assert saved["user_id"] == 7
