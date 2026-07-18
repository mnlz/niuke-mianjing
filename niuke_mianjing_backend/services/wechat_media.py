import base64
import random
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional

import requests
from PIL import Image, ImageDraw


TARGET_COVER_SIZE = (900, 500)


def generate_cover(output_path: str, theme: str = "auto", markdown_content: str = "") -> str:
    palette = _pick_palette(theme, markdown_content)
    img = Image.new("RGB", TARGET_COVER_SIZE, palette["background"])
    draw = ImageDraw.Draw(img)

    for _ in range(140):
        x, y = random.randint(0, TARGET_COVER_SIZE[0]), random.randint(0, TARGET_COVER_SIZE[1])
        b = random.randint(120, 255)
        draw.point((x, y), fill=(max(0, b - 60), max(0, b - 30), b))

    overlay = Image.new("RGBA", TARGET_COVER_SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([120, 80, 580, 420], fill=palette["glow_primary"])
    od.ellipse([430, 20, 820, 360], fill=palette["glow_secondary"])

    if palette["kind"] == "programming":
        for x in range(40, TARGET_COVER_SIZE[0], 42):
            for y in range(-20, TARGET_COVER_SIZE[1] + 20, 38):
                if random.random() > 0.55:
                    od.text((x, y), random.choice(["0", "1", "{ }", "</>"]), fill=(52, 211, 153, 55))
    else:
        nodes = [(random.randint(140, 760), random.randint(90, 410)) for _ in range(18)]
        for idx, (x, y) in enumerate(nodes):
            for nx, ny in nodes[idx + 1 : idx + 4]:
                od.line((x, y, nx, ny), fill=palette["line"])
            od.ellipse([x - 4, y - 4, x + 4, y + 4], fill=palette["node"])

    final_img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    final_img.save(output_path, "PNG")
    return output_path


def resize_cover_base64(image_base64: str) -> str:
    raw = base64.b64decode(image_base64)
    img = Image.open(BytesIO(raw)).convert("RGB")
    src_w, src_h = img.size
    target_ratio = TARGET_COVER_SIZE[0] / TARGET_COVER_SIZE[1]
    src_ratio = src_w / src_h

    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        left = (src_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        top = (src_h - new_h) // 2
        img = img.crop((0, top, src_w, top + new_h))

    img = img.resize(TARGET_COVER_SIZE, Image.Resampling.LANCZOS)
    output = BytesIO()
    img.save(output, "PNG")
    return base64.b64encode(output.getvalue()).decode("utf-8")


def image_url_to_base64(image_url: str) -> str:
    if image_url.startswith("data:image"):
        _, encoded = image_url.split(",", 1)
        return encoded

    response = requests.get(image_url, timeout=60)
    if response.status_code >= 400:
        raise ValueError(f"下载封面图失败：HTTP {response.status_code}")
    return base64.b64encode(response.content).decode("utf-8")


def write_base64_image(image_base64: str, output_path: str):
    Path(output_path).write_bytes(base64.b64decode(image_base64))


def normalize_base64_image(image_base64: str) -> str:
    value = image_base64.strip()
    if value.startswith("data:"):
        _, _, value = value.partition(",")
    base64.b64decode(value, validate=True)
    return value


def cover_suffix(mime: Optional[str]) -> str:
    suffixes = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    return suffixes.get((mime or "").lower(), ".png")


def _pick_palette(theme: str, markdown_content: str) -> Dict:
    text = f"{theme} {markdown_content}".lower()
    if any(keyword in text for keyword in ["code", "java", "python", "前端", "后端", "编程", "程序"]):
        return {
            "kind": "programming",
            "background": "#071512",
            "glow_primary": (34, 197, 94, 42),
            "glow_secondary": (20, 184, 166, 34),
            "line": (74, 222, 128, 70),
            "node": (134, 239, 172, 150),
        }
    if any(keyword in text for keyword in ["ai", "大模型", "算法", "机器学习"]):
        return {
            "kind": "ai",
            "background": "#160f08",
            "glow_primary": (249, 115, 22, 46),
            "glow_secondary": (251, 191, 36, 34),
            "line": (251, 146, 60, 75),
            "node": (253, 186, 116, 160),
        }
    return {
        "kind": "tech",
        "background": "#0a0a1a",
        "glow_primary": (100, 140, 255, 42),
        "glow_secondary": (34, 211, 238, 28),
        "line": (125, 211, 252, 70),
        "node": (191, 219, 254, 150),
    }
