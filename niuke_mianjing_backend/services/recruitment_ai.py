from typing import List

from niuke_mianjing_backend.services.openai_client import extract_chat_completion_text, post_chat_completion


def job_brief(job: dict) -> str:
    return f"""
公司：{job.get("company")}
岗位：{job.get("title")}
类型：{job.get("recruitment_type")}
方向：{job.get("display_category") or job.get("inferred_track_name") or job.get("category")}
岗位职责：
{(job.get("description") or "")[:2500]}
任职要求：
{(job.get("requirements") or "")[:2500]}
"""


def jobs_brief(jobs: List[dict]) -> str:
    if not jobs:
        return "暂无匹配岗位。"
    return "\n\n---\n\n".join(job_brief(job) for job in jobs[:8])


def interviews_brief(records: List[dict]) -> str:
    if not records:
        return "暂无匹配面经。"
    parts = []
    for item in records[:8]:
        parts.append(
            f"标题：{item.get('title')}\n方向：{item.get('post')}\n时间：{item.get('edit_time')}\n内容：{(item.get('content') or '')[:1200]}"
        )
    return "\n\n---\n\n".join(parts)


def call_ai_report(prompt: str) -> str:
    response = post_chat_completion(
        [
            {"role": "system", "content": "你是资深招聘与技术面试分析师，输出中文 Markdown 报告，直接给结论。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        timeout=120,
    )
    if response.status_code >= 400:
        raise ValueError(f"AI 报告生成失败：{response.text[:500]}")
    return extract_chat_completion_text(response.json())
