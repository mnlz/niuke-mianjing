"""Small client for the WeChat material and draft APIs."""

import json
from pathlib import Path
from typing import Dict, List, Optional

import requests

from niuke_mianjing_backend.config import settings


WECHAT_API_BASE = "https://api.weixin.qq.com/cgi-bin"


def get_token(appid: Optional[str] = None, secret: Optional[str] = None) -> str:
    appid = appid or settings.WECHAT_APP_ID
    secret = secret or settings.WECHAT_APP_SECRET
    if not appid or not secret:
        raise ValueError("请先在 .env 配置 WECHAT_APP_ID 和 WECHAT_APP_SECRET")

    response = requests.get(
        f"{WECHAT_API_BASE}/token",
        params={"grant_type": "client_credential", "appid": appid, "secret": secret},
        timeout=15,
    )
    data = response.json()
    if "access_token" not in data:
        raise ValueError(f"获取微信 access_token 失败：{data}")
    return data["access_token"]


def upload_cover(token: str, image_path: str) -> str:
    suffix = Path(image_path).suffix.lower()
    mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else "image/webp" if suffix == ".webp" else "image/png"
    with open(image_path, "rb") as image_file:
        response = requests.post(
            f"{WECHAT_API_BASE}/material/add_material",
            params={"access_token": token, "type": "image"},
            files={"media": (Path(image_path).name, image_file, mime)},
            timeout=30,
        )
    data = response.json()
    if "media_id" not in data:
        raise ValueError(f"上传微信封面失败：{data}")
    return data["media_id"]


def push_draft(
    token: str,
    title: str,
    html_content: str,
    cover_media_id: str,
    author: str,
    digest: Optional[str] = None,
    content_source_url: Optional[str] = None,
) -> Dict:
    article = {
        "title": title[:64],
        "author": author[:8],
        "content": html_content,
        "thumb_media_id": cover_media_id,
        "show_cover_pic": 0,
    }
    if digest:
        article["digest"] = digest[:120]
    if content_source_url:
        article["content_source_url"] = content_source_url

    response = requests.post(
        f"{WECHAT_API_BASE}/draft/add",
        params={"access_token": token},
        data=json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=30,
    )
    data = response.json()
    if "media_id" not in data:
        raise ValueError(f"创建微信草稿失败：{data}")
    return data


def push_newspic_draft(
    token: str,
    title: str,
    content: str,
    image_media_ids: List[str],
    need_open_comment: int = 1,
    only_fans_can_comment: int = 0,
) -> Dict:
    if not image_media_ids:
        raise ValueError("At least one card image is required")

    article = {
        "article_type": "newspic",
        "title": title[:64],
        "content": content,
        "need_open_comment": need_open_comment,
        "only_fans_can_comment": only_fans_can_comment,
        "image_info": {"image_list": [{"image_media_id": media_id} for media_id in image_media_ids]},
        "cover_info": {
            "crop_percent_list": [{"ratio": "1_1", "x1": "0", "y1": "0", "x2": "1", "y2": "1"}],
        },
    }

    response = requests.post(
        f"{WECHAT_API_BASE}/draft/add",
        params={"access_token": token},
        data=json.dumps({"articles": [article]}, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=60,
    )
    data = response.json()
    if "media_id" not in data:
        raise ValueError(f"Create WeChat newspic draft failed: {data}")
    return data
