from __future__ import annotations

import json
import random
import time
from collections import Counter

from backend.core.assets import write_placeholder_svg
from backend.core.constants import AGENTS, AI_DISCLOSURE
from backend.core.db import connect, log, notify, now_iso, rowdict, rowsdict
from backend.core.safety import blocked_terms, safety_note
from backend.integrations.etsy import EtsyClient
from backend.integrations.http import IntegrationError
from backend.integrations.openai_images import OpenAIImagesClient
from backend.integrations.printify import PrintifyClient


class AgentRegistry:
    def seed_agents(self) -> None:
        with connect() as conn:
            for agent in AGENTS:
                conn.execute(
                    """
                    INSERT INTO agents (id, name, summary, schedule_label, settings_json)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET name = excluded.name, summary = excluded.summary
                    """,
                    (agent["id"], agent["name"], agent["summary"], agent["default_schedule"], "{}"),
                )

    def run(self, agent_id: str) -> dict:
        handlers = {
            "market_research": self.run_market_research,
            "product_strategy": self.run_product_strategy,
            "prompt_engineering": self.run_prompt_engineering,
            "image_generation": self.run_image_generation,
            "mockup": self.run_mockup,
            "listing": self.run_listing,
            "analytics": self.run_analytics,
            "order": self.run_order_stub,
            "customer_service": self.run_customer_service,
            "approval_queue": self.run_approval_queue,
            "etsy": self.run_etsy_stub,
            "printify": self.run_printify_stub,
        }
        if agent_id not in handlers:
            raise ValueError("Unknown agent")
        started = time.perf_counter()
        result = handlers[agent_id]()
        elapsed = int((time.perf_counter() - started) * 1000)
        with connect() as conn:
            conn.execute("UPDATE agents SET last_run_at = ?, next_run_at = ? WHERE id = ?", (now_iso(), "", agent_id))
            conn.execute("UPDATE logs SET execution_ms = ? WHERE id = (SELECT MAX(id) FROM logs WHERE agent_id = ?)", (elapsed, agent_id))
        return result

    def run_market_research(self) -> dict:
        samples = [
            ("quiet luxury nursery wall art", "framed print", "spring baby gifting", "neutral nursery, new baby gift, minimalist animals", "22-42", 34, 78, 72),
            ("retro hiking poster", "poster", "summer travel", "national park inspired, outdoor decor, adventure gift", "18-34", 48, 81, 67),
            ("funny accountant mug", "mug", "tax season", "accountant gift, office mug, tax humor", "14-22", 57, 74, 64),
            ("pet memorial portrait", "canvas", "year round", "pet loss gift, custom pet art, sympathy gift", "38-85", 62, 83, 76),
            ("minimalist engineer shirt", "t-shirt", "graduation", "engineer gift, STEM shirt, clean typography", "20-32", 51, 69, 61),
        ]
        inserted = 0
        with connect() as conn:
            for niche, product_type, seasonality, keywords, price_range, comp, demand, profit in samples:
                existing = conn.execute(
                    "SELECT id FROM research_opportunities WHERE niche = ? AND product_type = ?",
                    (niche, product_type),
                ).fetchone()
                score = int((100 - comp) * 0.25 + demand * 0.45 + profit * 0.30)
                if existing:
                    continue
                conn.execute(
                    """
                    INSERT INTO research_opportunities (
                        created_at, updated_at, niche, product_type, seasonality, keywords, price_range,
                        competition_score, demand_score, profit_score, opportunity_score, notes, source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        now_iso(),
                        now_iso(),
                        niche,
                        product_type,
                        seasonality,
                        keywords,
                        price_range,
                        comp,
                        demand,
                        profit,
                        score,
                        "Stubbed research result. Replace with compliant official data sources and manual research inputs.",
                        "stub_research",
                    ),
                )
                inserted += 1
            log(conn, "market_research", "run_research", "research", "", f"Inserted {inserted} opportunities.")
        return {"inserted": inserted}

    def run_product_strategy(self) -> dict:
        created = 0
        with connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM research_opportunities
                WHERE opportunity_score >= 60
                ORDER BY opportunity_score DESC
                LIMIT 8
                """
            ).fetchall()
            for row in rows:
                exists = conn.execute(
                    "SELECT id FROM products WHERE niche = ? AND product_type = ?",
                    (row["niche"], row["product_type"]),
                ).fetchone()
                if exists:
                    continue
                title = row["niche"].title()
                reason = (
                    f"Opportunity score {row['opportunity_score']} with demand {row['demand_score']}, "
                    f"competition {row['competition_score']} and profit {row['profit_score']}."
                )
                conn.execute(
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
                        row["niche"],
                        row["product_type"],
                        reason,
                        row["keywords"],
                        safety_note(row["niche"], row["keywords"]),
                    ),
                )
                created += 1
            log(conn, "product_strategy", "create_product_ideas", "product", "", f"Created {created} product ideas.")
        return {"created": created}

    def run_prompt_engineering(self) -> dict:
        updated = 0
        with connect() as conn:
            products = conn.execute("SELECT * FROM products WHERE status IN ('Idea', 'Prompt') AND prompt = ''").fetchall()
            for product in products:
                prompt = (
                    f"Create an original {product['product_type']} design for '{product['niche']}'. "
                    f"Buyer keywords: {product['keywords']}. Use a polished, commercial Etsy style. "
                    "Avoid brands, celebrities, logos, trademarked phrases, sports clubs and copyrighted characters."
                )
                style = "editorial clean commercial illustration"
                palette = random.choice(["sage, charcoal, warm white", "indigo, cream, terracotta", "forest green, bone, muted gold"])
                aspect = "4:5" if product["product_type"] in {"poster", "framed print", "wall art", "canvas"} else "1:1"
                suitability = f"Prepared for {product['product_type']} print-on-demand production."
                conn.execute(
                    """
                    UPDATE products
                    SET prompt = ?, style = ?, colour_palette = ?, aspect_ratio = ?,
                        product_suitability = ?, status = 'Prompt', updated_at = ?
                    WHERE id = ?
                    """,
                    (prompt, style, palette, aspect, suitability, now_iso(), product["id"]),
                )
                updated += 1
            log(conn, "prompt_engineering", "generate_prompts", "product", "", f"Updated {updated} prompts.")
        return {"updated": updated}

    def run_image_generation(self) -> dict:
        created = 0
        provider = OpenAIImagesClient()
        with connect() as conn:
            products = conn.execute("SELECT * FROM products WHERE prompt <> '' AND artwork_path = ''").fetchall()
            for product in products:
                if provider.configured:
                    path = provider.generate(product_id=product["id"], prompt=product["prompt"], aspect_ratio=product["aspect_ratio"])
                    provider_name = f"openai:{provider.model}"
                    version_note = "Generated through OpenAI Images API."
                else:
                    path = write_placeholder_svg(product["id"], "manual_artwork_placeholder", product["title"], product["prompt"])
                    provider_name = "manual_placeholder"
                    version_note = "Offline placeholder because OPENAI_API_KEY is not configured."
                conn.execute(
                    "UPDATE products SET artwork_path = ?, status = 'Artwork', updated_at = ? WHERE id = ?",
                    (path, now_iso(), product["id"]),
                )
                conn.execute(
                    """
                    INSERT INTO image_versions (product_id, created_at, provider, prompt_used, asset_path, version_note)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (product["id"], now_iso(), provider_name, product["prompt"], path, version_note),
                )
                created += 1
            action = "generate_openai_images" if provider.configured else "create_manual_placeholders"
            log(conn, "image_generation", action, "image", "", f"Created {created} images.")
        return {"created": created}

    def run_mockup(self) -> dict:
        created = 0
        with connect() as conn:
            products = conn.execute("SELECT * FROM products WHERE artwork_path <> '' AND mockup_path = ''").fetchall()
            for product in products:
                path = write_placeholder_svg(product["id"], "mockup_placeholder", f"{product['title']} Mockup", product["product_type"])
                conn.execute(
                    "UPDATE products SET mockup_path = ?, status = 'Mockup', updated_at = ? WHERE id = ?",
                    (path, now_iso(), product["id"]),
                )
                created += 1
            log(conn, "mockup", "create_mockups", "mockup", "", f"Created {created} mockups.")
        return {"created": created}

    def run_listing(self) -> dict:
        updated = 0
        with connect() as conn:
            products = conn.execute("SELECT * FROM products WHERE mockup_path <> '' AND listing_title = ''").fetchall()
            for product in products:
                tags = self.tags_for(product["niche"], product["keywords"], product["product_type"])
                listing_title = " | ".join([product["title"], product["product_type"].title(), tags[0], "Gift"])[:140]
                price = self.price_for(product["product_type"])
                profit = int(price * 0.38)
                description = (
                    f"{listing_title}\n\n"
                    f"Original {product['product_type']} design for {product['niche']}.\n\n"
                    f"{AI_DISCLOSURE}\n\n"
                    "Reviewed by a human before publishing. Custom requests, complaints and refunds require manual approval."
                )
                conn.execute(
                    """
                    UPDATE products
                    SET listing_title = ?, listing_description = ?, tags = ?, materials = ?,
                        price_cents = ?, estimated_profit_cents = ?, alt_text = ?,
                        ai_disclosure = ?, status = 'Listing', updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        listing_title,
                        description,
                        ", ".join(tags),
                        self.materials_for(product["product_type"]),
                        price,
                        profit,
                        f"{product['product_type']} mockup for {product['niche']} design.",
                        AI_DISCLOSURE,
                        now_iso(),
                        product["id"],
                    ),
                )
                updated += 1
            log(conn, "listing", "generate_listings", "product", "", f"Updated {updated} listings.")
        return {"updated": updated}

    def approve_product(self, product_id: int) -> dict:
        with connect() as conn:
            product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if not product:
                raise ValueError("Product not found")
            terms = blocked_terms(product["title"], product["niche"], product["keywords"], product["prompt"], product["listing_title"], product["listing_description"])
            if terms:
                raise ValueError("Approval blocked by restricted terms: " + ", ".join(sorted(set(terms))))
            if not product["listing_title"] or not product["mockup_path"]:
                raise ValueError("Product must have artwork, mockup and listing before approval")
            conn.execute(
                "UPDATE products SET status = 'Approved', approved_at = ?, rejected_at = '', rejection_reason = '', updated_at = ? WHERE id = ?",
                (now_iso(), now_iso(), product_id),
            )
            log(conn, "approval_queue", "approve_product", "product", product_id)
            notify(conn, "success", "Product approved", product["title"])
        return {"approved": product_id}

    def reject_product(self, product_id: int, reason: str) -> dict:
        with connect() as conn:
            product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if not product:
                raise ValueError("Product not found")
            conn.execute(
                "UPDATE products SET status = 'Rejected', rejected_at = ?, rejection_reason = ?, updated_at = ? WHERE id = ?",
                (now_iso(), reason, now_iso(), product_id),
            )
            log(conn, "approval_queue", "reject_product", "product", product_id, reason)
        return {"rejected": product_id}

    def run_etsy_stub(self) -> dict:
        drafted = 0
        client = EtsyClient()
        with connect() as conn:
            products = conn.execute("SELECT * FROM products WHERE status = 'Approved' AND etsy_draft_id = ''").fetchall()
            for product in products:
                if client.configured:
                    draft_id = client.create_draft_listing(rowdict(product))
                    image_path = product["mockup_path"] or product["artwork_path"]
                    if image_path:
                        client.upload_listing_image(draft_id, image_path)
                    details = "Created Etsy draft through Etsy Open API."
                else:
                    draft_id = f"etsy-draft-{product['id']}"
                    details = "Created local Etsy draft placeholder because Etsy is not configured."
                conn.execute("UPDATE products SET etsy_draft_id = ?, updated_at = ? WHERE id = ?", (draft_id, now_iso(), product["id"]))
                log(conn, "etsy", "create_draft", "product", product["id"], details)
                drafted += 1
            log(conn, "etsy", "create_drafts", "product", "", f"Created {drafted} Etsy drafts.")
        return {"drafted": drafted}

    def publish_etsy_stub(self, product_id: int) -> dict:
        client = EtsyClient()
        with connect() as conn:
            product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if not product:
                raise ValueError("Product not found")
            if product["status"] != "Approved":
                raise ValueError("Publishing requires Approved status")
            if not product["etsy_draft_id"]:
                raise ValueError("Create Etsy draft before publishing")
            if client.configured and not str(product["etsy_draft_id"]).startswith("etsy-draft-"):
                client.publish_listing(product["etsy_draft_id"])
                listing_id = product["etsy_draft_id"]
                details = "Published through Etsy Open API after manual approval."
            else:
                listing_id = product["etsy_listing_id"] or f"etsy-live-{product_id}"
                details = "Local publish placeholder because Etsy is not configured or draft is local."
            conn.execute(
                "UPDATE products SET etsy_listing_id = ?, status = 'Published', updated_at = ? WHERE id = ?",
                (listing_id, now_iso(), product_id),
            )
            log(conn, "etsy", "publish_manual_gate", "product", product_id, details)
            notify(conn, "success", "Listing published stub", product["title"])
        return {"published": product_id}

    def run_printify_stub(self) -> dict:
        uploaded = 0
        client = PrintifyClient()
        with connect() as conn:
            products = conn.execute("SELECT * FROM products WHERE status = 'Approved' AND printify_product_id = ''").fetchall()
            for product in products:
                if client.configured:
                    image_id = client.upload_image(product["artwork_path"] or product["mockup_path"])
                    pid = client.create_product(rowdict(product), image_id)
                    details = f"Created Printify product via API using upload {image_id}."
                else:
                    pid = f"printify-product-{product['id']}"
                    details = "Created local Printify placeholder because Printify is not configured."
                conn.execute("UPDATE products SET printify_product_id = ?, updated_at = ? WHERE id = ?", (pid, now_iso(), product["id"]))
                log(conn, "printify", "create_product", "product", product["id"], details)
                uploaded += 1
            log(conn, "printify", "create_products", "product", "", f"Created {uploaded} Printify products.")
        return {"uploaded": uploaded}

    def integration_status(self) -> dict:
        etsy = EtsyClient()
        printify = PrintifyClient()
        openai = OpenAIImagesClient()
        with connect() as conn:
            etsy_token = conn.execute("SELECT updated_at FROM integration_tokens WHERE provider = 'etsy'").fetchone()
        return {
            "openai": {
                "configured": openai.configured,
                "model": openai.model,
                "ready": openai.configured,
                "missing": [] if openai.configured else ["OPENAI_API_KEY"],
            },
            "printify": {
                "configured": printify.configured,
                "ready": printify.configured,
                "shop_id": printify.shop_id,
                "missing": [
                    name
                    for name, value in {
                        "PRINTIFY_API_TOKEN": printify.token,
                        "PRINTIFY_SHOP_ID": printify.shop_id,
                    }.items()
                    if not value
                ],
            },
            "etsy": {
                "configured": etsy.configured,
                "oauth_connected": bool(etsy_token),
                "ready": etsy.configured and bool(etsy_token),
                "shop_id": etsy.shop_id,
                "missing": [
                    name
                    for name, value in {
                        "ETSY_CLIENT_ID": etsy.client_id,
                        "ETSY_CLIENT_SECRET": etsy.client_secret,
                        "ETSY_REDIRECT_URI": etsy.redirect_uri,
                        "ETSY_SHOP_ID": etsy.shop_id,
                    }.items()
                    if not value
                ],
                "token_updated_at": etsy_token["updated_at"] if etsy_token else "",
            },
        }

    def run_order_stub(self) -> dict:
        with connect() as conn:
            product = conn.execute("SELECT * FROM products ORDER BY id DESC LIMIT 1").fetchone()
            conn.execute(
                """
                INSERT INTO orders (
                    created_at, updated_at, marketplace_order_id, product_id, customer_name,
                    customer_message, issue_type, production_status, revenue_cents, profit_cents,
                    manual_review_required
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_iso(),
                    now_iso(),
                    f"etsy-order-{random.randint(10000, 99999)}",
                    product["id"] if product else None,
                    "Sample Customer",
                    "Could you confirm when my order will arrive?",
                    "late_delivery",
                    "in_production",
                    2499,
                    850,
                    0,
                ),
            )
            log(conn, "order", "pull_orders_stub", "order", "", "Inserted one sample Etsy order.")
        return {"orders": 1}

    def run_customer_service(self) -> dict:
        drafted = 0
        with connect() as conn:
            orders = conn.execute("SELECT * FROM orders WHERE draft_reply = ''").fetchall()
            for order in orders:
                if order["issue_type"] in {"refund", "complaint", "custom_order"}:
                    reply = f"Hi {order['customer_name']}, thanks for reaching out. I am reviewing this personally and will come back with the right next step shortly."
                    manual = 1
                else:
                    reply = f"Hi {order['customer_name']}, thanks for your message. I have checked the order status and will keep monitoring fulfilment until it is complete."
                    manual = order["manual_review_required"]
                conn.execute(
                    "UPDATE orders SET draft_reply = ?, manual_review_required = ?, updated_at = ? WHERE id = ?",
                    (reply, manual, now_iso(), order["id"]),
                )
                drafted += 1
            log(conn, "customer_service", "draft_replies", "order", "", f"Drafted {drafted} replies. No messages sent.")
        return {"drafted": drafted}

    def approve_reply(self, order_id: int) -> dict:
        with connect() as conn:
            order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not order:
                raise ValueError("Order not found")
            if order["manual_review_required"]:
                raise ValueError("Manual review required before this reply can be approved")
            if not order["draft_reply"]:
                raise ValueError("Draft reply first")
            conn.execute("UPDATE orders SET reply_approved_at = ?, updated_at = ? WHERE id = ?", (now_iso(), now_iso(), order_id))
            log(conn, "customer_service", "approve_reply_local_only", "order", order_id, "Approved locally only; MVP never sends automatically.")
        return {"approved_reply": order_id}

    def run_analytics(self) -> dict:
        with connect() as conn:
            orders = conn.execute("SELECT * FROM orders").fetchall()
            revenue = sum(row["revenue_cents"] for row in orders)
            profit = sum(row["profit_cents"] for row in orders)
            aov = int(revenue / len(orders)) if orders else 0
            pending = sum(1 for row in orders if row["production_status"] not in {"completed", "cancelled"})
            completed = sum(1 for row in orders if row["production_status"] == "completed")
            cancelled = sum(1 for row in orders if row["production_status"] == "cancelled")
            products = conn.execute("SELECT title, keywords, prompt FROM products").fetchall()
            keyword_counts = Counter()
            for product in products:
                keyword_counts.update([part.strip() for part in product["keywords"].split(",") if part.strip()])
            top_keywords = ", ".join([word for word, _ in keyword_counts.most_common(8)])
            best = products[0]["title"] if products else ""
            prompt = products[0]["prompt"][:120] if products and products[0]["prompt"] else ""
            roi = round((profit / max(revenue - profit, 1)) * 100, 2) if revenue else 0
            conn.execute(
                """
                INSERT INTO analytics_snapshots (
                    created_at, revenue_cents, profit_cents, average_order_value_cents,
                    pending_orders, completed_orders, cancelled_orders, best_seller, worst_seller,
                    top_keywords, best_prompt, roi_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (now_iso(), revenue, profit, aov, pending, completed, cancelled, best, "", top_keywords, prompt, roi),
            )
            log(conn, "analytics", "create_snapshot", "analytics", "", f"Revenue {revenue}, profit {profit}.")
        return {"revenue_cents": revenue, "profit_cents": profit}

    def run_approval_queue(self) -> dict:
        with connect() as conn:
            count = conn.execute("SELECT COUNT(*) AS c FROM products WHERE status = 'Listing'").fetchone()["c"]
            log(conn, "approval_queue", "review_queue", "product", "", f"{count} products waiting for approval.")
        return {"waiting": count}

    @staticmethod
    def tags_for(niche: str, keywords: str, product_type: str) -> list[str]:
        parts = [part.strip()[:20] for part in keywords.split(",") if part.strip()]
        tags = parts + [niche[:20], product_type[:20], "gift idea", "etsy gift", "wall decor"]
        unique = []
        for tag in tags:
            if tag and tag.lower() not in [item.lower() for item in unique]:
                unique.append(tag)
        return unique[:13]

    @staticmethod
    def price_for(product_type: str) -> int:
        return {
            "wall art": 1800,
            "framed print": 4200,
            "poster": 2400,
            "t-shirt": 2599,
            "mug": 1599,
            "canvas": 4800,
        }.get(product_type, 2499)

    @staticmethod
    def materials_for(product_type: str) -> str:
        return {
            "wall art": "archival paper, pigment ink",
            "framed print": "wood frame, acrylic glaze, archival paper",
            "poster": "premium poster paper, pigment ink",
            "t-shirt": "cotton blend, water based ink",
            "mug": "ceramic, sublimation ink",
            "canvas": "cotton canvas, stretcher frame, pigment ink",
        }.get(product_type, "print-on-demand materials")
