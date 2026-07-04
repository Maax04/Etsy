# AI POD OS Agents

The application is designed around independent agents. Each agent has:

- a registry entry
- a dashboard page/card
- settings and schedule fields
- server-side logs
- success/failure history
- a replaceable service boundary

## 1. Market Research Agent

Researches trending niches, product types, seasonal opportunities, keywords, price ranges, competition, demand and profit potential. The MVP uses compliant stub/manual research data and stores it in `research_opportunities`.

## 2. Product Strategy Agent

Turns high-scoring research rows into product ideas. Stores title, niche, product type, keywords and reason for recommendation.

## 3. Prompt Engineering Agent

Creates prompts, style, colour palette, aspect ratio and product suitability notes for wall art, framed prints, t-shirts, mugs and canvases.

## 4. Image Generation Agent

Creates manual placeholder assets in the MVP. The provider boundary is intentionally pluggable so OpenAI Images, local generation, or another approved provider can be swapped in later.

## 5. Mockup Agent

Creates product mockup placeholders for framed prints, posters, mugs and t-shirts. Replace this with real mockup generation later.

## 6. Listing Agent

Generates SEO title, description, 13 Etsy tags, materials, price suggestion, profit estimate, alt text and AI disclosure text. All fields are stored and should remain editable.

## 7. Approval Queue

Human gate for every product. Approval is blocked when obvious restricted IP, celebrity, logo, trademark or brand terms are detected.

## 8. Etsy Integration Agent

Official Etsy Open API placeholder. MVP creates local draft IDs only. Publishing requires manual approval and a draft ID.

## 9. Printify Agent

Official Printify API placeholder. MVP creates local product IDs only after product approval.

## 10. Order Agent

Official marketplace order retrieval placeholder. MVP inserts sample orders with production status, revenue and profit.

## 11. Customer Service Agent

Drafts replies but never sends them. Refunds, complaints and custom orders require human review.

## 12. Analytics Agent

Creates revenue, profit, AOV, order status, keyword, prompt and ROI snapshots.

## Safety Rules

- No automated Etsy publishing before approval.
- No automatic customer messaging.
- AI disclosure is added where appropriate.
- Restricted brands, copyrighted characters, celebrities, logos, football clubs and trademark terms are blocked or flagged.
- Use official APIs only. Do not scrape Etsy in a way that violates its terms.
