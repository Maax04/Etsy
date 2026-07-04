from __future__ import annotations

import hashlib
import hmac
import secrets
from http import cookies

from .config import ADMIN_PASSWORD, ADMIN_USERNAME, OPERATOR_PASSWORD, OPERATOR_USERNAME, SESSION_SECRET
from .db import connect, now_iso


COOKIE_NAME = "pod_os_session"


def password_ok(username: str, password: str) -> bool:
    owner_ok = hmac.compare_digest(username, ADMIN_USERNAME) and hmac.compare_digest(password, ADMIN_PASSWORD)
    operator_ok = bool(OPERATOR_USERNAME and OPERATOR_PASSWORD) and hmac.compare_digest(username, OPERATOR_USERNAME) and hmac.compare_digest(password, OPERATOR_PASSWORD)
    return owner_ok or operator_ok


def create_session(username: str) -> str:
    raw = secrets.token_urlsafe(32)
    token = hashlib.sha256((raw + SESSION_SECRET).encode("utf-8")).hexdigest()
    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions (token, created_at, username) VALUES (?, ?, ?)",
            (token, now_iso(), username),
        )
    return token


def parse_cookie(header: str | None) -> str:
    if not header:
        return ""
    jar = cookies.SimpleCookie()
    jar.load(header)
    morsel = jar.get(COOKIE_NAME)
    return morsel.value if morsel else ""


def session_user(token: str) -> str:
    if not token:
        return ""
    with connect() as conn:
        row = conn.execute("SELECT username FROM sessions WHERE token = ?", (token,)).fetchone()
    return row["username"] if row else ""
