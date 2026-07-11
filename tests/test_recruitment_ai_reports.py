import asyncio

from niuke_mianjing_backend.api.routes import recruitment


class FakeReportRepo:
    async def save(self, user_id, report):
        return {**report, "report_code": "RPT-TEST", "created_at": None, "updated_at": None}


def test_resume_job_report_uses_jobs_and_resume(monkeypatch):
    captured = {}

    async def fake_job_samples(source, recruitment_type, track, limit):
        return [{"title": "后端开发", "requirements": "Python"}]

    monkeypatch.setattr(recruitment, "_job_samples", fake_job_samples)
    monkeypatch.setattr(recruitment, "jobs_brief", lambda jobs: "岗位要求：Python")

    def fake_call(prompt):
        captured["prompt"] = prompt
        return "# 简历诊断"

    monkeypatch.setattr(recruitment, "call_ai_report", fake_call)
    monkeypatch.setattr(recruitment, "ai_report_repo", FakeReportRepo())
    request = recruitment.RecruitmentAIReportRequest(
        report_type="resume_job",
        source="tencent",
        recruitment_type="campus",
        track="backend",
        resume="候选人有 FastAPI 项目经验",
    )

    response = asyncio.run(recruitment.generate_recruitment_ai_report(request, user_id=1))

    assert response.data["report"] == "# 简历诊断"
    assert "岗位要求：Python" in captured["prompt"]
    assert "候选人有 FastAPI 项目经验" in captured["prompt"]


def test_resume_match_compares_companies_with_resume(monkeypatch):
    captured = {}

    async def fake_list_latest_jobs(source, recruitment_type):
        return [{"title": f"{source} 后端", "requirements": "分布式"}]

    monkeypatch.setattr(recruitment.recruitment_job_repo, "list_latest_jobs", fake_list_latest_jobs)
    monkeypatch.setattr(recruitment, "_filter_saved_jobs", lambda jobs, keyword, track, page, page_size: {"items": jobs})
    monkeypatch.setattr(recruitment, "job_brief", lambda job: f"岗位：{job['title']}")

    def fake_call(prompt):
        captured["prompt"] = prompt
        return "# 反向匹配"

    monkeypatch.setattr(recruitment, "call_ai_report", fake_call)
    monkeypatch.setattr(recruitment, "ai_report_repo", FakeReportRepo())
    request = recruitment.RecruitmentAIReportRequest(
        report_type="resume_match",
        recruitment_type="campus",
        track="backend",
        compare_sources=["tencent", "bytedance"],
        resume="候选人擅长高并发服务",
    )

    response = asyncio.run(recruitment.generate_recruitment_ai_report(request, user_id=1))

    assert response.data["report"] == "# 反向匹配"
    assert "腾讯" in captured["prompt"]
    assert "字节跳动" in captured["prompt"]
    assert "候选人擅长高并发服务" in captured["prompt"]
