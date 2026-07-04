from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from .config import DB_PATH, ensure_dirs


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def rowdict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def rowsdict(rows: list[sqlite3.Row]) -> list[dict]:
    return [rowdict(row) for row in rows if row is not None]


def log(conn: sqlite3.Connection, agent_id: str, action: str, entity_type: str, entity_id: object = "", details: str = "", success: int = 1) -> None:
    conn.execute(
        """
        INSERT INTO logs (created_at, agent_id, action, entity_type, entity_id, details, success)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (now_iso(), agent_id, action, entity_type, str(entity_id), details, success),
    )


def notify(conn: sqlite3.Connection, level: str, title: str, message: str) -> None:
    conn.execute(
        "INSERT INTO notifications (created_at, level, title, message, read_at) VALUES (?, ?, ?, ?, '')",
        (now_iso(), level, title, message),
    )


def init_db() -> None:
    ensure_dirs()
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                summary TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                schedule_label TEXT NOT NULL DEFAULT 'Manual',
                interval_minutes INTEGER NOT NULL DEFAULT 1440,
                last_run_at TEXT NOT NULL DEFAULT '',
                next_run_at TEXT NOT NULL DEFAULT '',
                settings_json TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS research_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                niche TEXT NOT NULL,
                product_type TEXT NOT NULL,
                seasonality TEXT NOT NULL DEFAULT '',
                keywords TEXT NOT NULL DEFAULT '',
                price_range TEXT NOT NULL DEFAULT '',
                competition_score INTEGER NOT NULL DEFAULT 50,
                demand_score INTEGER NOT NULL DEFAULT 50,
                profit_score INTEGER NOT NULL DEFAULT 50,
                opportunity_score INTEGER NOT NULL DEFAULT 50,
                notes TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'manual_or_stub'
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Idea',
                title TEXT NOT NULL,
                niche TEXT NOT NULL,
                product_type TEXT NOT NULL,
                reason TEXT NOT NULL DEFAULT '',
                keywords TEXT NOT NULL DEFAULT '',
                safety_notes TEXT NOT NULL DEFAULT '',
                prompt TEXT NOT NULL DEFAULT '',
                style TEXT NOT NULL DEFAULT '',
                colour_palette TEXT NOT NULL DEFAULT '',
                aspect_ratio TEXT NOT NULL DEFAULT '',
                product_suitability TEXT NOT NULL DEFAULT '',
                artwork_path TEXT NOT NULL DEFAULT '',
                mockup_path TEXT NOT NULL DEFAULT '',
                listing_title TEXT NOT NULL DEFAULT '',
                listing_description TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '',
                materials TEXT NOT NULL DEFAULT '',
                price_cents INTEGER NOT NULL DEFAULT 0,
                estimated_profit_cents INTEGER NOT NULL DEFAULT 0,
                alt_text TEXT NOT NULL DEFAULT '',
                ai_disclosure TEXT NOT NULL DEFAULT '',
                approved_at TEXT NOT NULL DEFAULT '',
                rejected_at TEXT NOT NULL DEFAULT '',
                rejection_reason TEXT NOT NULL DEFAULT '',
                etsy_draft_id TEXT NOT NULL DEFAULT '',
                etsy_listing_id TEXT NOT NULL DEFAULT '',
                printify_product_id TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS image_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                provider TEXT NOT NULL,
                prompt_used TEXT NOT NULL,
                asset_path TEXT NOT NULL,
                version_note TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                marketplace TEXT NOT NULL DEFAULT 'etsy',
                marketplace_order_id TEXT NOT NULL,
                product_id INTEGER,
                customer_name TEXT NOT NULL DEFAULT '',
                customer_message TEXT NOT NULL DEFAULT '',
                issue_type TEXT NOT NULL DEFAULT 'general',
                production_status TEXT NOT NULL DEFAULT 'pending',
                shipping_status TEXT NOT NULL DEFAULT '',
                tracking TEXT NOT NULL DEFAULT '',
                revenue_cents INTEGER NOT NULL DEFAULT 0,
                profit_cents INTEGER NOT NULL DEFAULT 0,
                draft_reply TEXT NOT NULL DEFAULT '',
                reply_approved_at TEXT NOT NULL DEFAULT '',
                manual_review_required INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS analytics_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                revenue_cents INTEGER NOT NULL,
                profit_cents INTEGER NOT NULL,
                average_order_value_cents INTEGER NOT NULL,
                pending_orders INTEGER NOT NULL,
                completed_orders INTEGER NOT NULL,
                cancelled_orders INTEGER NOT NULL,
                best_seller TEXT NOT NULL DEFAULT '',
                worst_seller TEXT NOT NULL DEFAULT '',
                top_keywords TEXT NOT NULL DEFAULT '',
                best_prompt TEXT NOT NULL DEFAULT '',
                roi_percent REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                success INTEGER NOT NULL DEFAULT 1,
                execution_ms INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                level TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                read_at TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                username TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS oauth_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                state TEXT NOT NULL,
                code_verifier TEXT NOT NULL,
                created_at TEXT NOT NULL,
                used_at TEXT NOT NULL DEFAULT ''
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_oauth_states_provider_state
            ON oauth_states(provider, state);

            CREATE TABLE IF NOT EXISTS integration_tokens (
                provider TEXT PRIMARY KEY,
                access_token TEXT NOT NULL DEFAULT '',
                refresh_token TEXT NOT NULL DEFAULT '',
                expires_in INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );
            """
        )
