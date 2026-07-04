from __future__ import annotations

import base64
import os
from pathlib import Path

from backend.integrations.http import IntegrationError, request_json


class PrintifyClient:
    base_url = "https://api.printify.com/v1"

    def __init__(self) -> None:
        self.token = os.environ.get("PRINTIFY_API_TOKEN", "")
        self.shop_id = os.environ.get("PRINTIFY_SHOP_ID", "")
        self.user_agent = os.environ.get("POD_OS_USER_AGENT", "AI-POD-OS/0.1")

    @property
    def configured(self) -> bool:
        return bool(self.token and self.shop_id)

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": self.user_agent,
        }

    def list_shops(self) -> dict:
        if not self.token:
            raise IntegrationError("PRINTIFY_API_TOKEN is not configured")
        return request_json("GET", f"{self.base_url}/shops.json", headers=self.headers())

    def upload_image(self, path: str) -> str:
        if not self.configured:
            raise IntegrationError("PRINTIFY_API_TOKEN and PRINTIFY_SHOP_ID are required")
        image_path = Path(path)
        if not image_path.exists():
            raise IntegrationError(f"Artwork file not found: {path}")
        payload = {
            "file_name": image_path.name,
            "contents": base64.b64encode(image_path.read_bytes()).decode("ascii"),
        }
        response = request_json("POST", f"{self.base_url}/uploads/images.json", headers=self.headers(), data=payload, timeout=120)
        image_id = response.get("id")
        if not image_id:
            raise IntegrationError("Printify upload response did not include an image id")
        return str(image_id)

    def create_product(self, product: dict, image_id: str) -> str:
        if not self.configured:
            raise IntegrationError("PRINTIFY_API_TOKEN and PRINTIFY_SHOP_ID are required")
        blueprint_id = int(os.environ.get(f"PRINTIFY_BLUEPRINT_ID_{slug(product['product_type'])}", os.environ.get("PRINTIFY_BLUEPRINT_ID", "0")))
        provider_id = int(os.environ.get(f"PRINTIFY_PRINT_PROVIDER_ID_{slug(product['product_type'])}", os.environ.get("PRINTIFY_PRINT_PROVIDER_ID", "0")))
        variant_ids = [
            int(value.strip())
            for value in os.environ.get(f"PRINTIFY_VARIANT_IDS_{slug(product['product_type'])}", os.environ.get("PRINTIFY_VARIANT_IDS", "")).split(",")
            if value.strip()
        ]
        if not blueprint_id or not provider_id or not variant_ids:
            raise IntegrationError("Printify blueprint/provider/variant env vars are required for product creation")
        payload = {
            "title": product["listing_title"] or product["title"],
            "description": product["listing_description"],
            "blueprint_id": blueprint_id,
            "print_provider_id": provider_id,
            "variants": [
                {
                    "id": variant_id,
                    "price": int(product["price_cents"]),
                    "is_enabled": True,
                }
                for variant_id in variant_ids
            ],
            "print_areas": [
                {
                    "variant_ids": variant_ids,
                    "placeholders": [
                        {
                            "position": os.environ.get("PRINTIFY_PLACEHOLDER_POSITION", "front"),
                            "images": [
                                {
                                    "id": image_id,
                                    "x": 0.5,
                                    "y": 0.5,
                                    "scale": 1,
                                    "angle": 0,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        response = request_json("POST", f"{self.base_url}/shops/{self.shop_id}/products.json", headers=self.headers(), data=payload, timeout=120)
        product_id = response.get("id")
        if not product_id:
            raise IntegrationError("Printify create product response did not include a product id")
        return str(product_id)


def slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.upper()).strip("_")
