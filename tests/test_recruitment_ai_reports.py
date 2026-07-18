import asyncio

import pytest

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

    def fake_call(prompt, model=None, model_id=None):
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

    def fake_call(prompt, model=None, model_id=None):
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


def test_full_report_contract_connects_all_three_sources():
    jobs = recruitment.jobs_brief([{
        "company": "字节跳动",
        "title": "AI 应用后端",
        "description": "负责大模型应用和支付系统",
        "requirements": "Java、算法、高并发",
    }])
    prompt = recruitment.build_full_report_prompt(jobs, [{
        "id": 7,
        "title": "后端一面",
        "post": "后端开发",
        "edit_time": "2026-07-01",
        "content": "项目深挖后手撕算法",
    }], "OpenAI SDK、SSE、订单补偿")

    for section in ["本场必看", "近期高频题", "项目拷打地图", "简历触发八股", "最可能的算法题", "简历修改建议", "附录"]:
        assert section in prompt
    assert "【JD-01】" in prompt
    assert "【面经-01｜记录 #7】" in prompt
    assert "【简历】" in prompt
    assert "OpenAI SDK、SSE、订单补偿" in prompt
    assert "只分析输入的精确岗位" in prompt
    assert "本节绝对不要输出题解" in prompt
    assert "【需本人替换：具体事实】" in prompt
    assert "岗位选择与投递优先级" not in prompt
    assert "7 天冲刺计划" not in prompt
    assert "60 分钟模拟面试" not in prompt


def test_full_report_requires_an_exact_job(monkeypatch):
    monkeypatch.setattr(recruitment.ai_model_registry, "resolve", lambda **kwargs: None)
    request = recruitment.RecruitmentAIReportRequest(
        report_type="full",
        source="bytedance",
        recruitment_type="campus",
        track="backend",
        resume="候选人简历",
    )

    with pytest.raises(recruitment.BadRequestException) as exc_info:
        asyncio.run(recruitment.generate_recruitment_ai_report(request, user_id=1))

    assert exc_info.value.message == "完整报告需要选择具体目标岗位"
