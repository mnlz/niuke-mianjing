import json
import re
from functools import lru_cache
from html import escape
from pathlib import Path
from typing import Dict, Optional

from bs4 import BeautifulSoup, Comment, NavigableString, Tag


BASE_FONT = "-apple-system-font,BlinkMacSystemFont,'Helvetica Neue','PingFang SC','Hiragino Sans GB','Microsoft YaHei',Arial,sans-serif"
THEME_RESOURCE_PATH = Path(__file__).resolve().parents[1] / "resources" / "raphael_themes.json"


RAPHAEL_THEMES: Dict[str, Dict[str, str]] = {
    "editorial_blue": {
        "container": f"box-sizing:border-box;max-width:100%;margin:0 auto;padding:22px 18px 44px;background:#ffffff;color:#2f3a4a;font-family:{BASE_FONT};font-size:16px;line-height:1.82;text-align:left;word-break:break-word;",
        "eyebrow": "box-sizing:border-box;margin:0 0 10px;color:#2f6feb;font-size:13px;line-height:1.6;font-weight:600;letter-spacing:0.04em;",
        "h1": "box-sizing:border-box;margin:0 0 24px;padding:0 0 14px;border-bottom:2px solid #2f6feb;color:#101828;font-size:23px;line-height:1.38;font-weight:800;letter-spacing:0;",
        "h2": "box-sizing:border-box;margin:34px 0 18px;padding:0 0 0 12px;border-left:4px solid #2f6feb;color:#101828;font-size:19px;line-height:1.45;font-weight:800;",
        "h3": "box-sizing:border-box;margin:26px 0 12px;color:#2f6feb;font-size:17px;line-height:1.5;font-weight:800;",
        "h4": "box-sizing:border-box;margin:22px 0 10px;color:#344054;font-size:16px;line-height:1.5;font-weight:700;",
        "p": "box-sizing:border-box;margin:0 0 18px;color:#344054;font-size:16px;line-height:1.82;text-align:justify;",
        "ul": "box-sizing:border-box;margin:14px 0 18px;padding-left:24px;color:#344054;list-style-type:disc;list-style-position:outside;",
        "ol": "box-sizing:border-box;margin:14px 0 18px;padding-left:24px;color:#344054;list-style-type:decimal;list-style-position:outside;",
        "li": "box-sizing:border-box;margin:0 0 9px;color:#344054;font-size:16px;line-height:1.78;",
        "blockquote": "box-sizing:border-box;margin:22px 0;padding:16px 18px;border-left:4px solid #2f6feb;background:#f2f7ff;color:#475467;font-size:15px;line-height:1.78;border-radius:6px;",
        "strong": "font-weight:800;color:#1d4ed8;",
        "em": "font-style:italic;color:#667085;",
        "a": "color:#2f6feb;text-decoration:none;border-bottom:1px solid #2f6feb;",
        "code": "font-family:Consolas,Menlo,'SF Mono',monospace;background:#eef4ff;color:#1d4ed8;border-radius:4px;padding:2px 5px;font-size:13px;",
        "pre": "box-sizing:border-box;margin:22px 0;padding:16px;background:#0f172a;color:#e5e7eb;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.7;",
        "table": "box-sizing:border-box;width:100%;border-collapse:collapse;margin:20px 0;font-size:14px;line-height:1.65;",
        "th": "box-sizing:border-box;border:1px solid #d0d7e2;background:#eef4ff;color:#1f2937;padding:9px 10px;text-align:left;font-weight:800;",
        "td": "box-sizing:border-box;border:1px solid #d0d7e2;color:#344054;padding:8px 10px;text-align:left;",
        "hr": "box-sizing:border-box;border:0;border-top:1px solid #e5e7eb;height:0;margin:28px 0;",
        "img": "box-sizing:border-box;display:block;width:100%;max-width:100%;height:auto;margin:24px auto;border-radius:10px;border:1px solid #e5e7eb;",
    },
    "knowledge_focus": {
        "container": f"box-sizing:border-box;max-width:100%;margin:0 auto;padding:22px 18px 44px;background:#fbfcff;color:#263238;font-family:{BASE_FONT};font-size:16px;line-height:1.84;text-align:left;word-break:break-word;",
        "eyebrow": "box-sizing:border-box;margin:0 0 10px;color:#0f766e;font-size:13px;line-height:1.6;font-weight:700;letter-spacing:0.04em;",
        "h1": "box-sizing:border-box;margin:0 0 24px;padding:0 0 14px;border-bottom:2px solid #0f766e;color:#0f172a;font-size:23px;line-height:1.38;font-weight:800;",
        "h2": "box-sizing:border-box;margin:34px 0 18px;padding:7px 12px;background:#e6fffb;color:#0f766e;font-size:19px;line-height:1.45;font-weight:800;border-radius:6px;",
        "h3": "box-sizing:border-box;margin:26px 0 12px;color:#0f766e;font-size:17px;line-height:1.5;font-weight:800;",
        "h4": "box-sizing:border-box;margin:22px 0 10px;color:#334155;font-size:16px;line-height:1.5;font-weight:700;",
        "p": "box-sizing:border-box;margin:0 0 18px;color:#334155;font-size:16px;line-height:1.84;text-align:justify;",
        "ul": "box-sizing:border-box;margin:14px 0 18px;padding-left:24px;color:#334155;list-style-type:disc;list-style-position:outside;",
        "ol": "box-sizing:border-box;margin:14px 0 18px;padding-left:24px;color:#334155;list-style-type:decimal;list-style-position:outside;",
        "li": "box-sizing:border-box;margin:0 0 9px;color:#334155;font-size:16px;line-height:1.8;",
        "blockquote": "box-sizing:border-box;margin:22px 0;padding:16px 18px;border-left:4px solid #0f766e;background:#ecfdf5;color:#475569;font-size:15px;line-height:1.78;border-radius:6px;",
        "strong": "font-weight:800;color:#0f766e;",
        "em": "font-style:italic;color:#64748b;",
        "a": "color:#0f766e;text-decoration:none;border-bottom:1px solid #0f766e;",
        "code": "font-family:Consolas,Menlo,'SF Mono',monospace;background:#ecfdf5;color:#0f766e;border-radius:4px;padding:2px 5px;font-size:13px;",
        "pre": "box-sizing:border-box;margin:22px 0;padding:16px;background:#10201d;color:#d1fae5;border-radius:8px;overflow-x:auto;font-size:13px;line-height:1.7;",
        "table": "box-sizing:border-box;width:100%;border-collapse:collapse;margin:20px 0;font-size:14px;line-height:1.65;",
        "th": "box-sizing:border-box;border:1px solid #b7e4da;background:#e6fffb;color:#0f172a;padding:9px 10px;text-align:left;font-weight:800;",
        "td": "box-sizing:border-box;border:1px solid #b7e4da;color:#334155;padding:8px 10px;text-align:left;",
        "hr": "box-sizing:border-box;border:0;border-top:1px solid #dbeafe;height:0;margin:28px 0;",
        "img": "box-sizing:border-box;display:block;width:100%;max-width:100%;height:auto;margin:24px auto;border-radius:10px;border:1px solid #dbeafe;",
    },
    "report_blue": {
        "container": f"box-sizing:border-box;max-width:100%;margin:0 auto;padding:0 8px 32px;background:#ffffff;color:rgb(63,63,63);font-family:{BASE_FONT};font-size:14px;line-height:1.75;text-align:left;word-break:break-word;",
        "eyebrow": "box-sizing:border-box;margin:1.2em 8px 0;color:rgb(15,76,129);font-size:13px;line-height:1.75;font-weight:bold;",
        "h1": "box-sizing:border-box;border-width:0 0 2px;border-style:solid;border-color:rgb(15,76,129);font-size:16.8px;font-weight:bold;margin:2em auto 1em;text-align:center;line-height:1.75;display:table;padding:0 1em;color:rgb(63,63,63);",
        "h2": "box-sizing:border-box;font-size:16.8px;font-weight:bold;margin:4em auto 2em;text-align:center;line-height:1.75;display:table;padding:0 0.4em;color:#ffffff;background:rgb(15,76,129);",
        "h3": "box-sizing:border-box;font-size:15.5px;font-weight:bold;margin:2.2em 8px 1em;line-height:1.75;color:rgb(15,76,129);",
        "h4": "box-sizing:border-box;font-size:14px;font-weight:bold;margin:1.8em 8px 0.8em;line-height:1.75;color:rgb(63,63,63);",
        "p": "box-sizing:border-box;margin:1.3em 8px;text-align:justify;line-height:1.75;font-size:14px;letter-spacing:0.08em;color:rgb(63,63,63);",
        "ul": "box-sizing:border-box;margin:1em 8px 1.2em;padding-left:1.4em;line-height:1.75;font-size:14px;color:rgb(63,63,63);list-style-type:disc;list-style-position:outside;",
        "ol": "box-sizing:border-box;margin:1em 8px 1.2em;padding-left:1.4em;line-height:1.75;font-size:14px;color:rgb(63,63,63);list-style-type:decimal;list-style-position:outside;",
        "li": "box-sizing:border-box;margin:0.4em 0;line-height:1.75;font-size:14px;color:rgb(63,63,63);letter-spacing:0.06em;",
        "blockquote": "box-sizing:border-box;margin:1.4em 8px;padding:0.8em 1em;border-left:4px solid rgb(15,76,129);background:#f4f8fb;color:rgb(63,63,63);font-size:14px;line-height:1.75;",
        "strong": "font-weight:bold;color:rgb(15,76,129);",
        "em": "font-style:italic;color:rgb(99,99,99);",
        "a": "color:rgb(15,76,129);text-decoration:none;border-bottom:1px solid rgb(15,76,129);",
        "code": "font-family:Consolas,Menlo,monospace;background:#f4f8fb;color:rgb(15,76,129);border-radius:3px;padding:1px 4px;font-size:13px;",
        "pre": "box-sizing:border-box;margin:1.4em 8px;padding:0.9em;background:#f4f8fb;color:rgb(63,63,63);border:1px solid #dfdfdf;overflow-x:auto;font-size:13px;line-height:1.65;",
        "table": "box-sizing:border-box;border-collapse:collapse;border-spacing:0;width:100%;margin:1em 0;font-size:14px;line-height:1.75;",
        "th": "box-sizing:border-box;border:1px solid rgb(223,223,223);background:#f4f8fb;text-align:left;line-height:1.75;font-size:14px;padding:0.35em 0.5em;color:rgb(15,76,129);font-weight:bold;",
        "td": "box-sizing:border-box;border:1px solid rgb(223,223,223);text-align:left;line-height:1.75;font-size:14px;padding:0.35em 0.5em;color:rgb(63,63,63);",
        "hr": "box-sizing:border-box;border:0;border-top:2px solid #e5e7eb;height:0;margin:1.5em 0;",
        "img": "box-sizing:border-box;display:block;width:100%;max-width:100%;height:auto;margin:1.4em auto;border-radius:4px;",
    },
}


CONTENT_THEME_MAP = {
    "single_interpretation": "editorial_blue",
    "manual_rewrite": "editorial_blue",
    "interviewer_chain": "editorial_blue",
    "knowledge_deep_dive": "knowledge_focus",
    "quick_checklist": "knowledge_focus",
    "trend_analysis": "report_blue",
}


def get_raphael_theme_groups() -> list:
    payload = _load_raphael_theme_payload()
    if not payload:
        return [
            {
                "label": "内置",
                "themes": [
                    {"id": "editorial_blue", "name": "编辑蓝", "description": "清爽的大厂公众号排版"},
                    {"id": "knowledge_focus", "name": "知识绿", "description": "适合知识点精讲和速查清单"},
                    {"id": "report_blue", "name": "报告蓝", "description": "适合趋势分析和数据报告"},
                ],
            }
        ]
    return [
        {
            "label": group.get("label", "Raphael"),
            "themes": [
                {
                    "id": theme.get("id"),
                    "name": theme.get("name"),
                    "description": theme.get("description", ""),
                }
                for theme in group.get("themes", [])
                if theme.get("id") and theme.get("name")
            ],
        }
        for group in payload.get("groups", [])
    ]


def render_raphael_wechat_html(
    title: str,
    html: str,
    content_type: str = "single_interpretation",
    theme_id: Optional[str] = None,
) -> str:
    theme = _resolve_theme(content_type, theme_id)
    soup = BeautifulSoup(html or "", "html.parser")
    _remove_unsafe_nodes(soup)

    body = soup.body if soup.body else soup
    content_nodes = _extract_content_nodes(body)
    content_soup = BeautifulSoup("", "html.parser")
    section = content_soup.new_tag("section")
    section["style"] = theme["container"]

    _append_title(section, content_soup, title, theme)
    for node in content_nodes:
        section.append(node)

    _drop_duplicate_first_heading(section, title)
    _normalize_lists_for_wechat(section, content_soup)
    _normalize_tree(section, theme)
    _convert_image_grids(section, content_soup)
    _force_text_inheritance(section, theme)
    _restore_header_styles(section, theme)

    return f"<!-- WECHAT_ARTICLE_TITLE: {escape(title)} -->\n{section}"


def render_markdown_as_raphael_html(
    title: str,
    body_html: str,
    content_type: str = "single_interpretation",
    theme_id: Optional[str] = None,
) -> str:
    return render_raphael_wechat_html(title, body_html, content_type, theme_id)


@lru_cache(maxsize=1)
def _load_raphael_theme_payload() -> dict:
    if not THEME_RESOURCE_PATH.exists():
        return {}
    return json.loads(THEME_RESOURCE_PATH.read_text(encoding="utf-8"))


def _resolve_theme(content_type: str, theme_id: Optional[str] = None) -> Dict[str, str]:
    if theme_id and theme_id != "auto":
        if theme_id in RAPHAEL_THEMES:
            return RAPHAEL_THEMES[theme_id]
        external_theme = _find_external_theme(theme_id)
        if external_theme:
            return _normalize_external_theme(external_theme["styles"], content_type)
    default_theme_id = CONTENT_THEME_MAP.get(content_type, "editorial_blue")
    return RAPHAEL_THEMES.get(default_theme_id, RAPHAEL_THEMES["editorial_blue"])


def _find_external_theme(theme_id: str) -> Optional[dict]:
    payload = _load_raphael_theme_payload()
    for group in payload.get("groups", []):
        for theme in group.get("themes", []):
            if theme.get("id") == theme_id:
                return theme
    return None


def _normalize_external_theme(styles: Dict[str, str], content_type: str) -> Dict[str, str]:
    fallback_id = CONTENT_THEME_MAP.get(content_type, "editorial_blue")
    fallback = RAPHAEL_THEMES.get(fallback_id, RAPHAEL_THEMES["editorial_blue"])
    theme = {**fallback, **styles}
    theme["container"] = _merge_style(
        theme.get("container", fallback["container"]),
        "box-sizing:border-box;max-width:100%;word-break:break-word;",
    )
    theme["eyebrow"] = _merge_style(
        "box-sizing:border-box;margin:0 0 12px;font-size:13px;line-height:1.6;font-weight:600;letter-spacing:0.04em;",
        _extract_accent_style(theme),
    )
    for key, value in list(theme.items()):
        if key != "eyebrow":
            theme[key] = _merge_style("box-sizing:border-box;", value)
    return theme


def _extract_accent_style(theme: Dict[str, str]) -> str:
    for key in ("h2", "h1", "strong", "a"):
        match = re.search(r"color:\s*([^;!]+)", theme.get(key, ""))
        if match:
            return f"color:{match.group(1).strip()};"
    return "color:#2f6feb;"


def _remove_unsafe_nodes(soup: BeautifulSoup) -> None:
    for node in soup.find_all(["script", "style", "svg", "canvas", "iframe"]):
        node.decompose()
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if "WECHAT_ARTICLE_TITLE" not in str(comment):
            comment.extract()


def _extract_content_nodes(body: Tag) -> list:
    if len(body.find_all(["section", "article"], recursive=False)) == 1:
        wrapper = body.find(["section", "article"], recursive=False)
        return [child.extract() for child in list(wrapper.children)]
    if len(body.find_all("div", recursive=False)) == 1:
        wrapper = body.find("div", recursive=False)
        return [child.extract() for child in list(wrapper.children)]
    return [child.extract() for child in list(body.children)]


def _append_title(section: Tag, soup: BeautifulSoup, title: str, theme: Dict[str, str]) -> None:
    eyebrow = soup.new_tag("p")
    eyebrow["data-raphael-role"] = "eyebrow"
    eyebrow["style"] = theme["eyebrow"]
    eyebrow.string = "牛客面经助手 · 公众号排版"
    section.append(eyebrow)

    h1 = soup.new_tag("h1")
    h1["data-raphael-role"] = "title"
    h1["style"] = theme["h1"]
    h1.string = title
    section.append(h1)


def _drop_duplicate_first_heading(section: Tag, title: str) -> None:
    headings = [child for child in section.children if isinstance(child, Tag) and child.name in {"h1", "h2"}]
    if len(headings) < 2:
        return
    first_content_heading = headings[1]
    if _normalize_text(first_content_heading.get_text()) == _normalize_text(title):
        first_content_heading.decompose()


def _normalize_lists_for_wechat(section: Tag, soup: BeautifulSoup) -> None:
    _remove_empty_list_marker_paragraphs(section)
    _absorb_ordered_list_continuations(section)
    _merge_adjacent_lists(section)

    for list_tag in list(section.find_all(["ul", "ol"])):
        for li in list(list_tag.find_all("li", recursive=False)):
            _replace_list_paragraphs_with_spans(li, soup)
            _trim_list_item_breaks(li)
            if _is_empty_list_item(li):
                li.decompose()
        if not list_tag.find("li", recursive=False):
            list_tag.decompose()
        elif list_tag.name == "ol" and list_tag.has_attr("start"):
            del list_tag.attrs["start"]


def _remove_empty_list_marker_paragraphs(section: Tag) -> None:
    for tag in list(section.find_all(["p", "div"])):
        if tag.find_parent(["li", "pre", "code"]):
            continue
        if _is_empty_list_marker_text(tag.get_text("", strip=True)):
            tag.decompose()


def _merge_adjacent_lists(section: Tag) -> None:
    for list_tag in list(section.find_all(["ul", "ol"])):
        if not list_tag.parent:
            continue
        cursor = list_tag.next_sibling
        while cursor is not None:
            if _is_blank_node(cursor):
                next_cursor = cursor.next_sibling
                cursor.extract()
                cursor = next_cursor
                continue
            if isinstance(cursor, Tag) and cursor.name == list_tag.name:
                next_cursor = cursor.next_sibling
                for li in list(cursor.find_all("li", recursive=False)):
                    list_tag.append(li.extract())
                cursor.decompose()
                cursor = next_cursor
                continue
            break


def _absorb_ordered_list_continuations(section: Tag) -> None:
    for list_tag in list(section.find_all("ol")):
        if not list_tag.parent:
            continue
        items = list_tag.find_all("li", recursive=False)
        if not items:
            continue
        target = items[-1]
        cursor = list_tag.next_sibling
        while cursor is not None:
            if _is_blank_node(cursor):
                next_cursor = cursor.next_sibling
                cursor.extract()
                cursor = next_cursor
                continue
            if isinstance(cursor, Tag) and cursor.name == "ol":
                break
            if isinstance(cursor, Tag) and cursor.name in {"h1", "h2", "h3", "h4", "h5", "h6", "hr", "table"}:
                break
            if isinstance(cursor, Tag) and cursor.name in {"p", "div", "blockquote", "pre", "ul"}:
                next_cursor = cursor.next_sibling
                target.append(cursor.extract())
                cursor = next_cursor
                continue
            break


def _replace_list_paragraphs_with_spans(li: Tag, soup: BeautifulSoup) -> None:
    for paragraph in list(li.find_all("p")):
        if paragraph.find_parent("li") is not li:
            continue
        if not paragraph.get_text("", strip=True) and not paragraph.find(["img", "table", "pre", "code", "ul", "ol"]):
            paragraph.decompose()
            continue
        span = soup.new_tag("span")
        if paragraph.get("style"):
            span["style"] = _merge_style(paragraph["style"], "display:block;")
        else:
            span["style"] = "display:block;"
        for child in list(paragraph.contents):
            span.append(child.extract())
        paragraph.replace_with(span)


def _is_empty_list_marker_text(text: str) -> bool:
    normalized = re.sub(r"[\s\u00a0\u200b\u200c\u200d\ufeff]+", "", text or "")
    return bool(re.fullmatch(r"(?:[-*+]|[0-9]{1,3}[.)、．。])", normalized))


def _is_empty_list_item(li: Tag) -> bool:
    if li.find(["img", "table", "pre", "code", "ul", "ol"]):
        return False
    return not li.get_text("", strip=True)


def _has_previous_visible_sibling(tag: Tag) -> bool:
    node = tag.previous_sibling
    while node is not None:
        if not _is_blank_node(node):
            return True
        node = node.previous_sibling
    return False


def _trim_list_item_breaks(li: Tag) -> None:
    while li.contents and _is_blank_node(li.contents[0]):
        li.contents[0].extract()
    while li.contents and _is_blank_node(li.contents[-1]):
        li.contents[-1].extract()
    for br in list(li.find_all("br")):
        previous = br.previous_sibling
        next_node = br.next_sibling
        if (previous is None or _is_blank_node(previous)) and (next_node is None or _is_blank_node(next_node)):
            br.decompose()


def _normalize_tree(section: Tag, theme: Dict[str, str]) -> None:
    for tag in section.find_all(True):
        if tag.name in {"section"}:
            continue
        _clean_attributes(tag)
        style = theme.get(tag.name)
        if style:
            tag["style"] = _merge_style(tag.get("style", ""), style)

    for pre in section.find_all("pre"):
        for code in pre.find_all("code"):
            code["style"] = "display:block;font-family:Consolas,Menlo,'SF Mono',monospace;background:transparent;color:inherit;padding:0;font-size:inherit;line-height:inherit;white-space:pre;word-break:normal;overflow-wrap:normal;"

    for ul in section.find_all("ul"):
        ul["style"] = _merge_style(ul.get("style", ""), "list-style-type:disc!important;list-style-position:outside;")
    for ol in section.find_all("ol"):
        ol["style"] = _merge_style(ol.get("style", ""), "list-style-type:decimal!important;list-style-position:outside;")

    for table in section.find_all("table"):
        table["cellpadding"] = "0"
        table["cellspacing"] = "0"
        table["border"] = "0"

    _attach_cjk_punctuation(section)


def _clean_attributes(tag: Tag) -> None:
    allowed = {"href", "src", "alt", "title", "start", "colspan", "rowspan", "cellpadding", "cellspacing", "border"}
    for attr in list(tag.attrs):
        if attr == "data-raphael-role":
            continue
        if attr.startswith("data-") or attr in {"class", "id"}:
            del tag.attrs[attr]
            continue
        if attr not in allowed and attr != "style":
            del tag.attrs[attr]


def _convert_image_grids(section: Tag, soup: BeautifulSoup) -> None:
    paragraphs = list(section.find_all("p"))
    for paragraph in paragraphs:
        children = [child for child in paragraph.children if not _is_blank_node(child)]
        if len(children) <= 1:
            continue
        images = []
        for child in children:
            if isinstance(child, Tag) and child.name == "img":
                images.append(child)
            elif isinstance(child, Tag) and child.name == "a" and child.find("img") and len(child.find_all("img")) == 1:
                images.append(child)
            else:
                images = []
                break
        if len(images) <= 1:
            continue
        table = soup.new_tag("table")
        table["style"] = "width:100%;border-collapse:collapse;margin:16px 0;border:none!important;background:transparent!important;"
        tbody = soup.new_tag("tbody")
        tr = soup.new_tag("tr")
        tr["style"] = "border:none!important;background:transparent!important;"
        for image in images[:3]:
            td = soup.new_tag("td")
            td["style"] = "padding:0 4px;vertical-align:top;border:none!important;background:transparent!important;"
            image.extract()
            if image.name == "img":
                image["style"] = _merge_style(image.get("style", ""), "width:100%!important;display:block;margin:0 auto;")
            td.append(image)
            tr.append(td)
        tbody.append(tr)
        table.append(tbody)
        paragraph.replace_with(table)


def _force_text_inheritance(section: Tag, theme: Dict[str, str]) -> None:
    container_style = theme["container"]
    font_match = re.search(r"font-family:([^;]+);", container_style)
    line_match = re.search(r"line-height:([^;]+);", container_style)
    color_match = re.search(r"color:([^;]+);", container_style)
    for tag in section.find_all(["p", "li", "blockquote", "span"]):
        if tag.find_parent(["pre", "code"]):
            continue
        extra = ""
        style = tag.get("style", "")
        if font_match and "font-family:" not in style:
            extra += f"font-family:{font_match.group(1)};"
        if line_match and "line-height:" not in style:
            extra += f"line-height:{line_match.group(1)};"
        if color_match and "color:" not in style:
            extra += f"color:{color_match.group(1)};"
        tag["style"] = _merge_style(style, extra)


def _restore_header_styles(section: Tag, theme: Dict[str, str]) -> None:
    eyebrow = section.find(attrs={"data-raphael-role": "eyebrow"})
    if eyebrow:
        eyebrow["style"] = theme["eyebrow"]
        del eyebrow.attrs["data-raphael-role"]

    title = section.find(attrs={"data-raphael-role": "title"})
    if title:
        title["style"] = theme["h1"]
        del title.attrs["data-raphael-role"]


def _attach_cjk_punctuation(section: Tag) -> None:
    punct = "，。：；！？、）】》”’"
    for tag in section.find_all(["strong", "b", "em", "span", "a", "code"]):
        next_node = tag.next_sibling
        if not isinstance(next_node, NavigableString):
            continue
        text = str(next_node)
        match = re.match(rf"^\s*([{re.escape(punct)}])(.*)$", text, flags=re.S)
        if not match:
            continue
        tag.append(match.group(1))
        rest = match.group(2)
        if rest:
            next_node.replace_with(rest)
        else:
            next_node.extract()


def _merge_style(existing: str, addition: str) -> str:
    existing = (existing or "").strip()
    addition = (addition or "").strip()
    if existing and not existing.endswith(";"):
        existing += ";"
    if addition and not addition.endswith(";"):
        addition += ";"
    return f"{existing}{addition}".strip()


def _is_blank_node(node) -> bool:
    if isinstance(node, NavigableString):
        return not str(node).strip()
    if isinstance(node, Tag) and node.name == "br":
        return True
    return False


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value or "").strip().lower()
