from __future__ import annotations

import csv
import json
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from backend.agents import AgentRegistry
from backend.core.auth import COOKIE_NAME, create_session, parse_cookie, password_ok, session_user
from backend.core.config import BASE_DIR, EXPORT_DIR, HOST, PORT
from backend.core.constants import STATUS_FLOW
from backend.core.db import connect, init_db, log, now_iso, rowdict, rowsdict
from backend.integrations.etsy import EtsyClient
from backend.integrations.http import IntegrationError
from backend.scheduler import start_embedded_scheduler


STATIC_DIR = BASE_DIR / "frontend"
registry = AgentRegistry()


class PodOsHandler(BaseHTTPRequestHandler):
    public_paths = {"/login", "/styles.css", "/app.js"}

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self.require_auth(lambda: self.send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8"))
        if parsed.path == "/login":
            return self.send_file(STATIC_DIR / "login.html", "text/html; charset=utf-8")
        if parsed.path == "/app.js":
            return self.send_file(STATIC_DIR / "app.js", "text/javascript; charset=utf-8")
        if parsed.path == "/styles.css":
            return self.send_file(STATIC_DIR / "styles.css", "text/css; charset=utf-8")
        if parsed.path == "/api/state":
            return self.require_auth(self.state)
        if parsed.path == "/api/integrations/etsy/start":
            return self.require_auth(self.start_etsy_oauth)
        if parsed.path == "/oauth/etsy/callback":
            return self.complete_etsy_oauth(parsed.query)
        if parsed.path == "/api/export/products.csv":
            return self.require_auth(self.export_products)
        self.error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/login":
            return self.login()
        routes = {
            "/api/agents/run": self.run_agent,
            "/api/products": self.create_product,
            "/api/products/approve": self.approve_product,
            "/api/products/reject": self.reject_product,
            "/api/products/publish-etsy-stub": self.publish_etsy_stub,
            "/api/orders/approve-reply": self.approve_reply,
            "/api/settings/agent": self.update_agent_settings,
            "/api/notifications/read": self.read_notification,
        }
        handler = routes.get(parsed.path)
        if not handler:
            return self.error(HTTPStatus.NOT_FOUND, "Not found")
        return self.require_auth(handler)

    def state(self) -> None:
        with connect() as conn:
            payload = {
                "user": self.user,
                "status_flow": STATUS_FLOW,
                "agents": rowsdict(conn.execute("SELECT * FROM agents ORDER BY rowid").fetchall()),
                "research": rowsdict(conn.execute("SELECT * FROM research_opportunities ORDER BY opportunity_score DESC, id DESC").fetchall()),
                "products": rowsdict(conn.execute("SELECT * FROM products ORDER BY updated_at DESC, id DESC").fetchall()),
                "orders": rowsdict(conn.execute("SELECT * FROM orders ORDER BY updated_at DESC, id DESC").fetchall()),
                "analytics": rowdict(conn.execute("SELECT * FROM analytics_snapshots ORDER BY id DESC LIMIT 1").fetchone()),
                "logs": rowsdict(conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 180").fetchall()),
                "notifications": rowsdict(conn.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 30").fetchall()),
                "integrations": registry.integration_status(),
            }
        self.json_response(payload)

    def start_etsy_oauth(self) -> None:
        url = EtsyClient().start_oauth()
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", url)
        self.end_headers()

    def complete_etsy_oauth(self, query: str) -> None:
        params = parse_qs(query)
        error = params.get("error", [""])[0]
        if error:
            return self.send_plain(f"Etsy OAuth failed: {error}", HTTPStatus.BAD_REQUEST)
        code = params.get("code", [""])[0]
        state = params.get("state", [""])[0]
        if not code or not state:
            return self.send_plain("Etsy OAuth callback missing code or state.", HTTPStatus.BAD_REQUEST)
        try:
            EtsyClient().complete_oauth(code, state)
        except IntegrationError as exc:
            return self.send_plain(f"Etsy OAuth failed: {exc}", HTTPStatus.BAD_REQUEST)
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", "/#settings")
        self.end_headers()

    def login(self) -> None:
        data = self.read_json()
        username = str(data.get("username", ""))
        password = str(data.get("password", ""))
        if not password_ok(username, password):
            return self.error(HTTPStatus.UNAUTHORIZED, "Invalid username or password")
        token = create_session(username)
        cookie = SimpleCookie()
        cookie[COOKIE_NAME] = token
        cookie[COOKIE_NAME]["path"] = "/"
        cookie[COOKIE_NAME]["httponly"] = True
        cookie[COOKIE_NAME]["samesite"] = "Strict"
        payload = json.dumps({"ok": True}).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Set-Cookie", cookie.output(header="").strip())
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def run_agent(self) -> None:
        data = self.read_json()
        result = registry.run(str(data.get("agent_id", "")))
        self.json_response({"ok": True, "result": result})

    def create_product(self) -> None:
        data = self.read_json()
        title = str(data.get("title", "")).strip()
        niche = str(data.get("niche", "")).strip()
        product_type = str(data.get("product_type", "")).strip()
        if not title or not niche or not product_type:
            raise ValueError("title, niche and product_type are required")
        from backend.core.safety import safety_note

        with connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO products (
                    created_at, updated_at, status, title, niche, product_type, reason,
                    keywords, safety_notes
                ) VALUES (?, ?, 'Idea', ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_iso(),
                    now_iso(),
                    title,
                    niche,
                    product_type,
                    str(data.get("reason", "")),
                    str(data.get("keywords", "")),
                    safety_note(title, niche, str(data.get("keywords", ""))),
                ),
            )
            log(conn, "product_strategy", "manual_create_product", "product", cur.lastrowid)
        self.json_response({"ok": True})

    def approve_product(self) -> None:
        data = self.read_json()
        self.json_response({"ok": True, "result": registry.approve_product(int(data.get("id")))})

    def reject_product(self) -> None:
        data = self.read_json()
        self.json_response({"ok": True, "result": registry.reject_product(int(data.get("id")), str(data.get("reason", "Rejected by reviewer.")))})

    def publish_etsy_stub(self) -> None:
        data = self.read_json()
        self.json_response({"ok": True, "result": registry.publish_etsy_stub(int(data.get("id")))})

    def approve_reply(self) -> None:
        data = self.read_json()
        self.json_response({"ok": True, "result": registry.approve_reply(int(data.get("id")))})

    def update_agent_settings(self) -> None:
        data = self.read_json()
        agent_id = str(data.get("id", ""))
        enabled = 1 if data.get("enabled", True) else 0
        schedule_label = str(data.get("schedule_label", "Manual"))
        interval = max(1, int(data.get("interval_minutes") or 1440))
        with connect() as conn:
            conn.execute(
                "UPDATE agents SET enabled = ?, schedule_label = ?, interval_minutes = ? WHERE id = ?",
                (enabled, schedule_label, interval, agent_id),
            )
            log(conn, agent_id, "update_schedule_settings", "agent", agent_id, schedule_label)
        self.json_response({"ok": True})

    def read_notification(self) -> None:
        data = self.read_json()
        with connect() as conn:
            conn.execute("UPDATE notifications SET read_at = ? WHERE id = ?", (now_iso(), int(data.get("id"))))
        self.json_response({"ok": True})

    def export_products(self) -> None:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = EXPORT_DIR / "products.csv"
        with connect() as conn:
            rows = rowsdict(conn.execute("SELECT * FROM products ORDER BY id").fetchall())
            log(conn, "listing", "export_products_csv", "export", path.name)
        fields = [
            "id",
            "status",
            "title",
            "niche",
            "product_type",
            "reason",
            "keywords",
            "prompt",
            "style",
            "colour_palette",
            "aspect_ratio",
            "product_suitability",
            "artwork_path",
            "mockup_path",
            "listing_title",
            "listing_description",
            "tags",
            "materials",
            "price_cents",
            "estimated_profit_cents",
            "alt_text",
            "ai_disclosure",
            "etsy_draft_id",
            "etsy_listing_id",
            "printify_product_id",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        payload = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="products.csv"')
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def require_auth(self, callback):
        token = parse_cookie(self.headers.get("Cookie"))
        self.user = session_user(token)
        if not self.user:
            if self.path.startswith("/api/"):
                return self.error(HTTPStatus.UNAUTHORIZED, "Login required")
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/login")
            self.end_headers()
            return None
        try:
            return callback()
        except (ValueError, IntegrationError) as exc:
            return self.error(HTTPStatus.BAD_REQUEST, str(exc))

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def json_response(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(data, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_file(self, path: Path, content_type: str) -> None:
        payload = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_plain(self, message: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = message.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def error(self, status: HTTPStatus, message: str) -> None:
        self.json_response({"ok": False, "error": message}, status)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    init_db()
    registry.seed_agents()
    start_embedded_scheduler(registry)
    server = ThreadingHTTPServer((HOST, PORT), PodOsHandler)
    print(f"AI POD OS running at http://{HOST}:{PORT}")
    print("Default local login: admin / admin. Change POD_OS_ADMIN_PASSWORD before real use.")
    server.serve_forever()


if __name__ == "__main__":
    main()
