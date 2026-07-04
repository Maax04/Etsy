from __future__ import annotations

import re
from pathlib import Path

from .config import ASSET_DIR


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")[:48] or "asset"


def write_placeholder_svg(product_id: int, label: str, title: str, prompt: str = "") -> str:
    folder = ASSET_DIR / str(product_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{safe_slug(label)}.svg"
    clean_title = escape_xml(title[:44])
    clean_prompt = escape_xml((prompt or "Manual generation placeholder")[:92])
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="1000" viewBox="0 0 1400 1000">
  <rect width="1400" height="1000" fill="#f7f4ee"/>
  <rect x="90" y="90" width="1220" height="820" rx="22" fill="#fff" stroke="#20272b" stroke-width="8"/>
  <circle cx="335" cy="385" r="118" fill="#2c7a73"/>
  <rect x="520" y="312" width="460" height="160" rx="18" fill="#c7553e"/>
  <path d="M285 680 C420 520 590 520 730 680 S1040 840 1145 610" fill="none" stroke="#2d5d84" stroke-width="42" stroke-linecap="round"/>
  <text x="700" y="220" text-anchor="middle" font-family="Arial, sans-serif" font-size="58" font-weight="700" fill="#20272b">{clean_title}</text>
  <text x="700" y="810" text-anchor="middle" font-family="Arial, sans-serif" font-size="30" fill="#5d686d">{clean_prompt}</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")
    return str(path)


def escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
