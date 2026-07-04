from __future__ import annotations

import base64
import os
from pathlib import Path

from backend.core.config import ASSET_DIR
from backend.integrations.http import IntegrationError, request_json


class OpenAIImagesClient:
    base_url = "https://api.openai.com/v1/images/generations"

    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.model = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def generate(self, *, product_id: int, prompt: str, aspect_ratio: str) -> str:
        if not self.configured:
            raise IntegrationError("OPENAI_API_KEY is not configured")
        size = self.size_for(aspect_ratio)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "quality": os.environ.get("OPENAI_IMAGE_QUALITY", "medium"),
            "n": 1,
        }
        response = request_json(
            "POST",
            self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            data=payload,
            timeout=180,
        )
        try:
            b64 = response["data"][0]["b64_json"]
        except (KeyError, IndexError) as exc:
            raise IntegrationError("OpenAI image response did not include b64_json") from exc
        folder = ASSET_DIR / str(product_id)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "openai_generated_artwork.png"
        path.write_bytes(base64.b64decode(b64))
        return str(path)

    @staticmethod
    def size_for(aspect_ratio: str) -> str:
        if aspect_ratio in {"4:5", "2:3", "portrait"}:
            return "1024x1536"
        if aspect_ratio in {"3:2", "landscape"}:
            return "1536x1024"
        return "1024x1024"
