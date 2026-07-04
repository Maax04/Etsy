from __future__ import annotations

import base64
import hashlib
import os
import secrets
from pathlib import Path
from urllib.parse import urlencode

from backend.core.db import connect, now_iso
from backend.integrations.http import IntegrationError, request_json, request_multipart


class EtsyClient:
    api_base = "https://api.etsy.com/v3/application"
    oauth_url = "https://www.etsy.com/oauth/connect"
    token_url = "https://api.etsy.com/v3/public/oauth/token"

    def __init__(self) -> None:
        self.client_id = os.environ.get("ETSY_CLIENT_ID", "")
        self.client_secret = os.environ.get("ETSY_CLIENT_SECRET", "")
        self.redirect_uri = os.environ.get("ETSY_REDIRECT_URI", "")
        self.shop_id = os.environ.get("ETSY_SHOP_ID", "")

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.redirect_uri and self.shop_id)

    def api_key_header(self) -> str:
        return f"{self.client_id}:{self.client_secret}"

    def start_oauth(self) -> str:
        if not (self.client_id and self.redirect_uri):
            raise IntegrationError("ETSY_CLIENT_ID and ETSY_REDIRECT_URI are required")
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode("ascii").rstrip("=")
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).decode("ascii").rstrip("=")
        state = secrets.token_urlsafe(32)
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO oauth_states (provider, state, code_verifier, created_at, used_at)
                VALUES ('etsy', ?, ?, ?, '')
                """,
                (state, verifier, now_iso()),
            )
        scopes = os.environ.get("ETSY_SCOPES", "shops_r listings_r listings_w transactions_r")
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self.client_id,
                "redirect_uri": self.redirect_uri,
                "scope": scopes,
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
        return f"{self.oauth_url}?{query}"

    def complete_oauth(self, code: str, state: str) -> dict:
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM oauth_states WHERE provider = 'etsy' AND state = ? AND used_at = ''",
                (state,),
            ).fetchone()
            if not row:
                raise IntegrationError("Invalid or already-used Etsy OAuth state")
            response = request_json(
                "POST",
                self.token_url,
                form={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "redirect_uri": self.redirect_uri,
                    "code": code,
                    "code_verifier": row["code_verifier"],
                },
                timeout=60,
            )
            conn.execute("UPDATE oauth_states SET used_at = ? WHERE id = ?", (now_iso(), row["id"]))
            conn.execute(
                """
                INSERT INTO integration_tokens (provider, access_token, refresh_token, expires_in, updated_at)
                VALUES ('etsy', ?, ?, ?, ?)
                ON CONFLICT(provider) DO UPDATE SET
                    access_token = excluded.access_token,
                    refresh_token = excluded.refresh_token,
                    expires_in = excluded.expires_in,
                    updated_at = excluded.updated_at
                """,
                (
                    response.get("access_token", ""),
                    response.get("refresh_token", ""),
                    int(response.get("expires_in", 0)),
                    now_iso(),
                ),
            )
        return response

    def access_token(self) -> str:
        with connect() as conn:
            row = conn.execute("SELECT access_token FROM integration_tokens WHERE provider = 'etsy'").fetchone()
        if not row or not row["access_token"]:
            raise IntegrationError("Etsy OAuth is not connected")
        return row["access_token"]

    def headers(self) -> dict[str, str]:
        return {
            "x-api-key": self.api_key_header(),
            "Authorization": f"Bearer {self.access_token()}",
        }

    def create_draft_listing(self, product: dict) -> str:
        if not self.configured:
            raise IntegrationError("Etsy env vars are not fully configured")
        taxonomy_id = int(os.environ.get("ETSY_TAXONOMY_ID", "1"))
        shipping_profile_id = os.environ.get("ETSY_SHIPPING_PROFILE_ID", "")
        payload = {
            "quantity": int(os.environ.get("ETSY_DEFAULT_QUANTITY", "999")),
            "title": product["listing_title"] or product["title"],
            "description": product["listing_description"],
            "price": f"{int(product['price_cents']) / 100:.2f}",
            "who_made": os.environ.get("ETSY_WHO_MADE", "i_did"),
            "when_made": os.environ.get("ETSY_WHEN_MADE", "made_to_order"),
            "taxonomy_id": taxonomy_id,
            "is_supply": False,
            "should_auto_renew": True,
            "state": "draft",
            "tags": [tag.strip() for tag in (product["tags"] or "").split(",") if tag.strip()][:13],
            "materials": [part.strip() for part in (product["materials"] or "").split(",") if part.strip()][:13],
        }
        if shipping_profile_id:
            payload["shipping_profile_id"] = int(shipping_profile_id)
        response = request_json(
            "POST",
            f"{self.api_base}/shops/{self.shop_id}/listings",
            headers=self.headers(),
            data=payload,
            timeout=90,
        )
        listing_id = response.get("listing_id") or response.get("listing_id".upper()) or response.get("id")
        if not listing_id:
            raise IntegrationError("Etsy draft listing response did not include a listing id")
        return str(listing_id)

    def upload_listing_image(self, listing_id: str, image_path: str) -> dict:
        path = Path(image_path)
        if not path.exists():
            raise IntegrationError(f"Image file not found: {image_path}")
        return request_multipart(
            "POST",
            f"{self.api_base}/shops/{self.shop_id}/listings/{listing_id}/images",
            headers=self.headers(),
            fields={"rank": "1"},
            files={"image": path},
            timeout=120,
        )

    def publish_listing(self, listing_id: str) -> dict:
        return request_json(
            "PATCH",
            f"{self.api_base}/shops/{self.shop_id}/listings/{listing_id}",
            headers=self.headers(),
            data={"state": "active"},
            timeout=60,
        )
