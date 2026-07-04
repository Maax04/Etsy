# Render Setup

This is the MVP deployment shape for two private users.

## Services

Use `render.yaml` to create one Render web service:

- `pod-os-web`
- Docker runtime
- persistent disk mounted at `/app/data`
- embedded scheduler enabled with `POD_OS_ENABLE_EMBEDDED_WORKER=true`

The app currently uses SQLite. Do not split web and worker into separate Render services until PostgreSQL support is added, because separate services cannot safely share the same SQLite file.

## Required Environment Variables

Set these in Render:

```text
POD_OS_ADMIN_USERNAME
POD_OS_ADMIN_PASSWORD
POD_OS_OPERATOR_USERNAME
POD_OS_OPERATOR_PASSWORD
POD_OS_SESSION_SECRET
OPENAI_API_KEY
ETSY_CLIENT_ID
ETSY_CLIENT_SECRET
ETSY_REDIRECT_URI
ETSY_SHOP_ID
PRINTIFY_API_TOKEN
PRINTIFY_SHOP_ID
```

Set `ETSY_REDIRECT_URI` to:

```text
https://YOUR-RENDER-SERVICE.onrender.com/oauth/etsy/callback
```

That exact URL must also be registered in your Etsy developer app.

## Printify Product Mapping

Printify product creation needs catalog IDs. Start with one product type and set:

```text
PRINTIFY_BLUEPRINT_ID
PRINTIFY_PRINT_PROVIDER_ID
PRINTIFY_VARIANT_IDS
```

Later, add per-type overrides:

```text
PRINTIFY_BLUEPRINT_ID_T_SHIRT
PRINTIFY_PRINT_PROVIDER_ID_T_SHIRT
PRINTIFY_VARIANT_IDS_T_SHIRT
PRINTIFY_BLUEPRINT_ID_MUG
PRINTIFY_PRINT_PROVIDER_ID_MUG
PRINTIFY_VARIANT_IDS_MUG
```

## Etsy First-Time Connection

1. Deploy the app.
2. Log in as owner.
3. Go to Integrations.
4. Click `Connect Etsy`.
5. Approve the requested scopes.
6. Return to the dashboard and confirm Etsy shows `Ready`.

## Automation Boundary

The scheduler can automate:

- research rows
- product ideas
- prompts
- image generation
- mockups
- listings
- orders
- draft replies
- analytics

Manual approval remains required for:

- publishing listings
- customer messages
- refunds
- complaints
- custom orders
- products flagged for IP/trademark/celebrity risk

## Next Production Upgrade

Move from SQLite to Render Postgres before adding multiple web instances, separate workers, or heavier order polling.
