from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("POD_OS_DATA_DIR", BASE_DIR / "data"))
ASSET_DIR = Path(os.environ.get("POD_OS_ASSET_DIR", DATA_DIR / "assets"))
EXPORT_DIR = Path(os.environ.get("POD_OS_EXPORT_DIR", DATA_DIR / "exports"))
DB_PATH = Path(os.environ.get("POD_OS_DATABASE", DATA_DIR / "pod_os.sqlite3"))
HOST = os.environ.get("POD_OS_HOST", "127.0.0.1")
PORT = int(os.environ.get("POD_OS_PORT", "8787"))
SESSION_SECRET = os.environ.get("POD_OS_SESSION_SECRET", "local-dev-change-me")
ADMIN_USERNAME = os.environ.get("POD_OS_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("POD_OS_ADMIN_PASSWORD", "admin")
OPERATOR_USERNAME = os.environ.get("POD_OS_OPERATOR_USERNAME", "")
OPERATOR_PASSWORD = os.environ.get("POD_OS_OPERATOR_PASSWORD", "")


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
