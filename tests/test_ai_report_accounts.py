import asyncio

import pytest

from niuke_mianjing_backend.api.middleware.error_handler import NotFoundException
from niuke_mianjing_backend.api.routes import recruitment


class FakeReportRepo:
    def __init__(self):
        self.saved = []

    async def save(self, user_id, report):
        row = {**report, "report_code": "RPT-TEST", "user_id": user_id, "created_at": "2026-07-10T00:00:00"}
        self.saved.append(row)
        return row

    async def list_by_user(self, user_id):
        return [row for row in self.saved if row["user_id"] == user_id]

    async def get_by_code(self, user_id, report_code):
        return next((row for row in self.saved if row["user_id"] == user_id and row["report_code"] == report_code), None)

    async def delete_by_code(self, user_id, report_code):
        row = await self.get_by_code(user_id, report_code)
        if not row:
            return False
        self.saved.remove(row)
        return True


def test_generated_report_is_saved_for_current_user(monkeypatch):
    repo = FakeReportRepo()

    async def fake_job_samples(source, recruitment_type, track, limit):
        return [{"title": "后端开发"}]

    monkeypatch.setattr(recruitment, "ai_report_repo", repo)
    monkeypatch.setattr(recruitment, "_job_samples", fake_job_samples)
    monkeypatch.setattr(recruitment, "jobs_brief", lambda jobs: "岗位样本")
    monkeypatch.setattr(recruitment, "call_ai_report", lambda prompt: "# 岗位报告")

    response = asyncio.run(recruitment.generate_recruitment_ai_report(
        recruitment.RecruitmentAIReportRequest(report_type="job", source="tencent", track="backend"),
        user_id=7,
    ))

    assert response.data["report_code"] == "RPT-TEST"
    assert repo.saved[0]["user_id"] == 7
    assert repo.saved[0]["content"] == "# 岗位报告"


def test_report_detail_and_delete_are_account_scoped(monkeypatch):
    repo = FakeReportRepo()
    monkeypatch.setattr(recruitment, "ai_report_repo", repo)
    awaitable = repo.save(7, {"title": "测试", "content": "# 报告"})
    asyncio.run(awaitable)

    detail = asyncio.run(recruitment.get_ai_report("RPT-TEST", user_id=7))
    assert detail.data["title"] == "测试"

    with pytest.raises(NotFoundException):
        asyncio.run(recruitment.get_ai_report("RPT-TEST", user_id=8))

    asyncio.run(recruitment.delete_ai_report("RPT-TEST", user_id=7))
    assert asyncio.run(repo.get_by_code(7, "RPT-TEST")) is None
