import io
import asyncio
from pathlib import Path

import pytest
from fastapi import UploadFile
from pypdf import PdfWriter

from niuke_mianjing_backend.api.middleware.error_handler import AppException
from niuke_mianjing_backend.api.routes import recruitment
from niuke_mianjing_backend.services import resume_parser
from niuke_mianjing_backend.services.resume_parser import parse_resume_pdf


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = {
    "zzw_0410.pdf": "朱志伟",
    "刘子宇简历-Final.pdf": "刘子宇",
    "刘子扬+南京邮电大学+电子信息.pdf": "刘子扬",
    "朱小媚.pdf": "朱小媚",
    "翁叶-简历 .pdf": "翁叶",
}


@pytest.mark.parametrize(("filename", "name"), SAMPLES.items())
def test_real_resume_samples(filename, name):
    result = parse_resume_pdf((ROOT / "简历" / filename).read_bytes())

    assert result["name"] == name
    assert result["phone"]
    assert result["email"]
    assert result["page_count"] == 1
    assert result["char_count"] == len(result["text"])
    assert result["sections"]
    assert any(section["content"] for section in result["sections"])


def test_soft_wraps_join_without_swallowing_new_items():
    wrapped = "主要包含硬件模块、后台服务模块、客户端模块、分析报告模块、采集模块与存储模块；本人负责硬件选型、后台服务及相关业务模块开发，并"
    another = "熟悉性能测试工具、监控工具和完整的软件测试流程，能够独立完成测试计划、测试执行、缺陷跟踪和结果分析"

    assert resume_parser._join_wrapped_lines([
        wrapped,
        "预研跨局域网通信；开发时间：90个工作日。",
        "项目经历",
        another,
        "2、性能分析：使用监控仪表板分析服务器性能指标；",
    ]) == [
        f"{wrapped}预研跨局域网通信；开发时间：90个工作日。",
        "项目经历",
        another,
        "2、性能分析：使用监控仪表板分析服务器性能指标；",
    ]


def test_real_project_section_has_no_layout_soft_wraps():
    result = parse_resume_pdf((ROOT / "简历" / "刘子扬+南京邮电大学+电子信息.pdf").read_bytes())
    projects = next(section["content"] for section in result["sections"] if section["key"] == "projects")

    assert "开发，并\n预研" not in projects
    assert "无线\n通讯模块" not in projects
    assert "数据帧格\n式" not in projects
    assert "信息进\n行匹配" not in projects


def test_invalid_pdf_is_rejected():
    with pytest.raises(ValueError, match="PDF 解析失败"):
        parse_resume_pdf(b"not-a-pdf")


def test_pdf_without_text_is_rejected():
    output = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=595, height=842)
    writer.write(output)

    with pytest.raises(ValueError, match="PDF 未解析出可用文本"):
        parse_resume_pdf(output.getvalue())


def test_route_rejects_non_pdf_and_fake_pdf():
    with pytest.raises(AppException, match="请上传 PDF 简历"):
        asyncio.run(recruitment.parse_resume_pdf(UploadFile(io.BytesIO(b"text"), filename="resume.txt"), 1))

    with pytest.raises(AppException, match="请上传有效的 PDF 简历"):
        asyncio.run(recruitment.parse_resume_pdf(UploadFile(io.BytesIO(b"not-a-pdf"), filename="resume.pdf"), 1))


def test_route_returns_structured_resume():
    content = (ROOT / "简历" / "zzw_0410.pdf").read_bytes()
    response = asyncio.run(recruitment.parse_resume_pdf(UploadFile(io.BytesIO(content), filename="resume.pdf"), 1))

    assert response.data["name"] == "朱志伟"
    assert response.data["page_count"] == 1
    assert response.data["char_count"] == len(response.data["text"])
    assert response.data["sections"]
