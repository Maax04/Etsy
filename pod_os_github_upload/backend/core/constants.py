AGENTS = [
    {
        "id": "market_research",
        "name": "Market Research Agent",
        "summary": "Finds niches, products, seasonal opportunities, keywords, demand, competition and profit potential.",
        "default_schedule": "Every morning",
    },
    {
        "id": "product_strategy",
        "name": "Product Strategy Agent",
        "summary": "Turns research into product ideas with recommendation reasons.",
        "default_schedule": "After research",
    },
    {
        "id": "prompt_engineering",
        "name": "Prompt Engineering Agent",
        "summary": "Creates high-quality image prompts, styles, palettes, aspect ratios and suitability notes.",
        "default_schedule": "On new idea",
    },
    {
        "id": "image_generation",
        "name": "Image Generation Agent",
        "summary": "Stores manual/generated artwork with provider-pluggable version history.",
        "default_schedule": "Manual",
    },
    {
        "id": "mockup",
        "name": "Mockup Agent",
        "summary": "Creates and stores mockups for framed prints, posters, mugs and t-shirts.",
        "default_schedule": "After artwork",
    },
    {
        "id": "listing",
        "name": "Listing Agent",
        "summary": "Generates SEO title, description, tags, materials, price, profit estimate, alt text and AI disclosure.",
        "default_schedule": "After mockup",
    },
    {
        "id": "approval_queue",
        "name": "Approval Queue",
        "summary": "Human gate for approval, rejection and publishing readiness.",
        "default_schedule": "Manual",
    },
    {
        "id": "etsy",
        "name": "Etsy Integration Agent",
        "summary": "Official Etsy Open API placeholder for authentication, drafts, inventory, pricing, images and publishing.",
        "default_schedule": "Manual",
    },
    {
        "id": "printify",
        "name": "Printify Agent",
        "summary": "Official Printify API placeholder for product creation, artwork upload, variants, pricing and fulfilment.",
        "default_schedule": "Manual",
    },
    {
        "id": "order",
        "name": "Order Agent",
        "summary": "Retrieves orders, production status, shipping, tracking, revenue and profit.",
        "default_schedule": "Regular polling or webhook",
    },
    {
        "id": "customer_service",
        "name": "Customer Service Agent",
        "summary": "Drafts replies for late delivery, replacements, refunds, general enquiries and custom orders.",
        "default_schedule": "On customer message",
    },
    {
        "id": "analytics",
        "name": "Analytics Agent",
        "summary": "Reports revenue, profit, conversion, best/worst sellers, niches, keywords, prompts and ROI.",
        "default_schedule": "Every night",
    },
]

STATUS_FLOW = [
    "Research",
    "Idea",
    "Prompt",
    "Artwork",
    "Mockup",
    "Listing",
    "Approved",
    "Rejected",
    "Published",
]

PRODUCT_TYPES = ["wall art", "framed print", "poster", "t-shirt", "mug", "canvas"]

FORBIDDEN_TERMS = [
    "disney",
    "marvel",
    "nike",
    "star wars",
    "harry potter",
    "pokemon",
    "barbie",
    "taylor swift",
    "beyonce",
    "celebrity",
    "premier league",
    "arsenal",
    "chelsea",
    "liverpool",
    "manchester united",
    "tottenham",
    "football club",
    "logo",
    "trademark",
]

AI_DISCLOSURE = (
    "AI-assisted artwork disclosure: this design was created with human-directed AI tools, "
    "then reviewed, edited and prepared for print by the shop owner."
)
