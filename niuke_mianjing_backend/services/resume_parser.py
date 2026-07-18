import io
import re

from pypdf import PdfReader


SECTION_TITLES = {
    "教育经历": "education",
    "工作经历": "work",
    "实习经历": "internship",
    "项目经历": "projects",
    "专业技能": "skills",
    "技能": "skills",
    "技能/证书及其他": "skills",
    "荣誉奖项": "awards",
    "校园经历": "campus",
    "工作以外经历": "other",
    "个人总结": "summary",
    "其他": "other",
}

_SENTENCE_ENDINGS = tuple("。；！？!?;：:")
_NEW_ITEM_PREFIXES = (
    "熟悉", "熟练", "掌握", "了解", "精通", "负责", "参与", "具备", "能够", "善于",
    "项目名称", "项目简介", "项目描述", "项目成果", "主要工作", "核心技术", "受奖经历",
)


def _extract_page(page) -> str:
    try:
        return page.extract_text(extraction_mode="layout") or ""
    except Exception:
        return page.extract_text() or ""


def _clean_lines(text: str) -> list[str]:
    return [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines() if line.strip()]


def _looks_like_new_item(line: str) -> bool:
    return (
        line in SECTION_TITLES
        or line.startswith(_NEW_ITEM_PREFIXES)
        or bool(re.match(r"^\d+[、.．)]", line))
        or bool(re.match(r"^.{1,12}[：:]", line))
    )


def _join_wrapped_lines(lines: list[str]) -> list[str]:
    result: list[str] = []
    previous_source_length = 0
    for line in lines:
        if (
            result
            and previous_source_length >= 55
            and not result[-1].endswith(_SENTENCE_ENDINGS)
            and not _looks_like_new_item(line)
        ):
            result[-1] += line
        else:
            result.append(line)
        previous_source_length = len(line)
    return result


def _extract_name(lines: list[str]) -> str:
    for line in lines[:20]:
        if line in SECTION_TITLES:
            break
        match = re.match(r"^([\u4e00-\u9fff]{2,4})(?:\s|$)", line)
        if match and match.group(1) not in SECTION_TITLES:
            return match.group(1)
    return ""


def _split_sections(lines: list[str]) -> list[dict]:
    sections: list[dict] = []
    current_title = ""
    current_lines: list[str] = []

    def flush():
        if not current_title or not current_lines:
            return
        content = "\n".join(current_lines).strip()
        key = SECTION_TITLES[current_title]
        existing = next((item for item in sections if item["key"] == key), None)
        if existing:
            existing["content"] += f"\n{content}"
        else:
            sections.append({"key": key, "title": current_title, "content": content})

    for line in lines:
        if line in SECTION_TITLES:
            flush()
            current_title = line
            current_lines = []
        elif current_title:
            current_lines.append(line)
    flush()
    return sections


def parse_resume_pdf(content: bytes) -> dict:
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            raise ValueError("PDF 已加密，请上传未加密的简历")
        raw_text = "\n".join(_extract_page(page) for page in reader.pages[:12])
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"PDF 解析失败：{exc}") from exc

    lines = _join_wrapped_lines(_clean_lines(raw_text))
    text = "\n".join(lines).strip()[:12000]
    if not text:
        raise ValueError("PDF 未解析出可用文本，请换成文本型 PDF")

    phone_match = re.search(r"(?<!\d)1[3-9](?:[ -]?\d){9}(?!\d)", text)
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    return {
        "text": text,
        "name": _extract_name(lines),
        "phone": re.sub(r"[ -]", "", phone_match.group(0)) if phone_match else "",
        "email": email_match.group(0) if email_match else "",
        "page_count": len(reader.pages),
        "char_count": len(text),
        "sections": _split_sections(lines),
    }
