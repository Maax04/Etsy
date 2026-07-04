# AI Print-on-Demand Operating System

Agent-based local-first MVP for AI-assisted Etsy + Printify print-on-demand operations.

This repo follows the attached `AI Print-on-Demand Operating System.pdf` brief:

- modular agents
- SQLite MVP database
- future PostgreSQL/Docker/GitHub readiness
- authentication
- scheduling settings
- logs, notifications and history
- approval queue
- Etsy, Printify and OpenAI integration layer
- customer-service drafts that are never sent automatically
- AI artwork disclosure
- restricted IP guardrails

## Run Locally

```powershell
cd C:\Users\Max\Documents\Codex\2026-07-04\okay-so-we-can-use-github\pod_os
$env:PYTHONPATH='.'
& 'C:\Users\Max\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' backend\main.py
```

Open:

```text
http://127.0.0.1:8787
```

If `8787` is already in use:

```powershell
$env:PYTHONPATH='.'
$env:POD_OS_PORT='8791'
& 'C:\Users\Max\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' backend\main.py
```

Default local login:

```text
admin / admin
```

Set `POD_OS_ADMIN_PASSWORD` before using the app for anything real.

## Environment Variables

Copy `.env.example` and set values in your shell or deployment environment.

Secrets must never be hardcoded. The app now includes real API-shaped clients for Etsy, Printify and OpenAI Images. If credentials are missing, the dashboard shows setup status and agents fall back to local placeholders where safe.

## MVP Workflow

1. Run Market Research Agent.
2. Run Product Strategy Agent.
3. Run Prompt Engineering Agent.
4. Run Image Generation Agent.
5. Run Mockup Agent.
6. Run Listing Agent.
7. Review the Approval Queue.
8. Approve or reject products.
9. Create Etsy drafts and Printify products when integrations are configured.
10. Publish Etsy only after manual approval and draft creation.
11. Pull stub orders.
12. Draft customer replies for approval.
13. Refresh analytics.

The `Run Core Pipeline` button executes the research-to-listing path.

## Project Structure

```text
pod_os/
  AGENTS.md
  Dockerfile
  docker-compose.yml
  README.md
  .env.example
  backend/
    main.py
    scheduler.py
    agents/
      registry.py
    core/
      auth.py
      assets.py
      config.py
      constants.py
      db.py
      safety.py
    integrations/
      etsy.py
      openai_images.py
      printify.py
  frontend/
    index.html
    login.html
    app.js
    styles.css
  docs/
    schema.md
  data/
    pod_os.sqlite3
    assets/
    exports/
```

## Integration Notes

Integration code lives in `backend/integrations/`.

- Etsy: OAuth, draft listing, image upload, manual publish gate.
- Printify: image upload and product creation.
- OpenAI Images: prompt-to-image generation.
- Orders and mockup automation are still local/offline placeholders.

Keep approval checks in the backend, not just the frontend.

## Render

See [docs/render-setup.md](docs/render-setup.md).

## Security Notes

- Environment variables for secrets.
- Session-based local authentication.
- Future role support can be added around the session user and route authorization.
- Customer replies are approved locally only in this MVP.
- Refunds, complaints and custom orders require human review.
