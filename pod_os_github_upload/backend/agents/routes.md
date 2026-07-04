# Agent Routes

The MVP uses a central standard-library HTTP router in `backend/main.py`:

- `POST /api/agents/run`
- `POST /api/products/approve`
- `POST /api/products/reject`
- `POST /api/products/publish-etsy-stub`
- `POST /api/orders/approve-reply`
- `POST /api/settings/agent`

When moving to FastAPI, split these route handlers into each agent folder while preserving the same backend approval gates.
