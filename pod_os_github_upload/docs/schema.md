# Database Schema

SQLite is used for the MVP. The schema is intentionally compatible with a later PostgreSQL migration.

## agents

Agent metadata, enablement, schedule labels, intervals, last run and JSON settings.

## research_opportunities

Market research rows with niche, product type, seasonality, keywords, price range, competition score, demand score, profit score and opportunity score.

## products

Product lifecycle state:

`Research -> Idea -> Prompt -> Artwork -> Mockup -> Listing -> Approved -> Rejected -> Published`

Stores strategy fields, prompt fields, artwork/mockup paths, listing fields, pricing, profit, AI disclosure, approvals, Etsy IDs and Printify IDs.

## image_versions

Provider, prompt, asset path, creation date and version note for generated artwork history.

## orders

Marketplace order ID, product, customer, message, issue type, production status, shipping status, tracking, revenue, profit, draft reply and manual review flags.

## analytics_snapshots

Revenue, profit, AOV, order counts, best/worst seller placeholders, top keywords, best prompt and ROI.

## logs

Every agent action with timestamp, agent ID, action, entity, details, success and execution time.

## notifications

Dashboard notifications, with future email/Discord support.

## sessions

Local session tokens for MVP authentication.
