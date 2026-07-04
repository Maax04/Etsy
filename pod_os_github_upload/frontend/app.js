const state = {};
const corePipeline = [
  "market_research",
  "product_strategy",
  "prompt_engineering",
  "image_generation",
  "mockup",
  "listing",
  "analytics"
];

async function getState() {
  const response = await fetch("/api/state");
  if (response.status === 401) {
    location.href = "/login";
    return;
  }
  Object.assign(state, await response.json());
  render();
}

async function post(path, body = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const payload = await response.json();
  if (!response.ok || payload.ok === false) throw new Error(payload.error || "Request failed");
  await getState();
  return payload;
}

function money(cents) {
  return new Intl.NumberFormat("en-GB", { style: "currency", currency: "GBP" }).format((cents || 0) / 100);
}

function node(tag, attrs = {}, text = "") {
  const el = document.createElement(tag);
  Object.entries(attrs).forEach(([key, value]) => {
    if (key === "class") el.className = value;
    else el.setAttribute(key, value);
  });
  if (text) el.textContent = text;
  return el;
}

function button(label, className, fn, disabled = false) {
  const btn = node("button", { class: className, type: "button" }, label);
  btn.disabled = disabled;
  btn.addEventListener("click", async () => {
    try {
      btn.disabled = true;
      await fn();
    } catch (error) {
      alert(error.message);
      btn.disabled = false;
    }
  });
  return btn;
}

function render() {
  renderOverview();
  renderAgents();
  renderResearch();
  renderProducts();
  renderApproval();
  renderOrders();
  renderAnalytics();
  renderIntegrations();
  renderSettings();
  renderNotifications();
  renderLogs();
}

function renderOverview() {
  const root = document.getElementById("overview");
  const products = state.products || [];
  const orders = state.orders || [];
  const published = products.filter((p) => p.status === "Published").length;
  const waiting = products.filter((p) => p.status === "Listing").length;
  const revenue = orders.reduce((sum, order) => sum + order.revenue_cents, 0);
  const profit = orders.reduce((sum, order) => sum + order.profit_cents, 0);
  root.replaceChildren(
    metric("Products", products.length),
    metric("Waiting Approval", waiting),
    metric("Published", published),
    metric("Revenue", money(revenue)),
    metric("Profit", money(profit)),
    metric("Agents", (state.agents || []).length)
  );
}

function metric(label, value) {
  const card = node("div", { class: "metric" });
  card.append(node("strong", {}, String(value)));
  card.append(node("span", {}, label));
  return card;
}

function renderAgents() {
  const root = document.getElementById("agent-grid");
  root.replaceChildren();
  (state.agents || []).forEach((agent) => {
    const card = node("article", { class: "agent-card" });
    card.append(node("span", { class: "pill" }, agent.enabled ? "Enabled" : "Paused"));
    card.append(node("h3", {}, agent.name));
    card.append(node("p", {}, agent.summary));
    card.append(node("p", { class: "muted" }, `Schedule: ${agent.schedule_label} - interval ${agent.interval_minutes}m`));
    card.append(node("p", { class: "muted" }, `Last run: ${agent.last_run_at || "never"}`));
    const actions = node("div", { class: "actions" });
    actions.append(button("Run", "button primary", () => post("/api/agents/run", { agent_id: agent.id })));
    card.append(actions);
    root.append(card);
  });
}

function renderResearch() {
  const table = document.getElementById("research-table");
  table.replaceChildren();
  table.append(row(["Niche", "Product", "Keywords", "Competition", "Demand", "Profit", "Opportunity"], "th"));
  (state.research || []).forEach((item) => {
    table.append(row([
      item.niche,
      item.product_type,
      item.keywords,
      item.competition_score,
      item.demand_score,
      item.profit_score,
      item.opportunity_score
    ]));
  });
}

function row(cells, tag = "td") {
  const tr = document.createElement("tr");
  cells.forEach((cell) => tr.append(node(tag, {}, String(cell ?? ""))));
  return tr;
}

function renderProducts() {
  const counts = Object.fromEntries((state.status_flow || []).map((status) => [status, 0]));
  (state.products || []).forEach((product) => counts[product.status] = (counts[product.status] || 0) + 1);
  const flow = document.getElementById("status-flow");
  flow.replaceChildren();
  (state.status_flow || []).forEach((status) => {
    const cell = node("div", { class: "status-cell" });
    cell.append(node("strong", {}, String(counts[status] || 0)));
    cell.append(node("div", { class: "muted" }, status));
    flow.append(cell);
  });

  const root = document.getElementById("product-grid");
  root.replaceChildren();
  (state.products || []).forEach((product) => {
    const card = node("article", { class: "product-card" });
    const pill = node("span", { class: product.safety_notes.includes("Restricted") ? "pill warn" : "pill" }, product.status);
    card.append(pill);
    card.append(node("h3", {}, product.listing_title || product.title));
    card.append(node("p", {}, `${product.product_type} - ${product.niche}`));
    card.append(node("p", { class: "muted" }, product.reason || product.safety_notes));
    if (product.prompt) card.append(node("pre", {}, product.prompt));
    if (product.listing_description) card.append(node("pre", {}, product.listing_description));
    const meta = node("p", { class: "muted" }, `Price ${money(product.price_cents)} - Profit ${money(product.estimated_profit_cents)} - Tags: ${product.tags || "none"}`);
    card.append(meta);
    root.append(card);
  });
}

function renderApproval() {
  const root = document.getElementById("approval-list");
  root.replaceChildren();
  const candidates = (state.products || []).filter((p) => ["Listing", "Approved", "Rejected"].includes(p.status));
  if (!candidates.length) root.append(node("p", { class: "muted" }, "No products in the approval stage yet."));
  candidates.forEach((product) => {
    const card = node("article", { class: "item-card" });
    card.append(node("h3", {}, product.listing_title || product.title));
    card.append(node("p", {}, product.safety_notes));
    const actions = node("div", { class: "actions" });
    actions.append(button("Approve", "button warn", () => post("/api/products/approve", { id: product.id }), product.status !== "Listing"));
    actions.append(button("Reject", "button danger", () => post("/api/products/reject", { id: product.id, reason: prompt("Reason for rejection?", "Needs human revision.") || "Rejected." }), product.status === "Rejected"));
    actions.append(button("Create Etsy Draft", "button secondary", () => post("/api/agents/run", { agent_id: "etsy" }), product.status !== "Approved"));
    actions.append(button("Create Printify Product", "button secondary", () => post("/api/agents/run", { agent_id: "printify" }), product.status !== "Approved"));
    actions.append(button("Publish Etsy", "button primary", () => post("/api/products/publish-etsy-stub", { id: product.id }), product.status !== "Approved" || !product.etsy_draft_id));
    card.append(actions);
    root.append(card);
  });
}

function renderOrders() {
  const ordersRoot = document.getElementById("orders-list");
  const repliesRoot = document.getElementById("replies-list");
  ordersRoot.replaceChildren();
  repliesRoot.replaceChildren();
  (state.orders || []).forEach((order) => {
    const orderCard = node("article", { class: "item-card" });
    orderCard.append(node("h3", {}, `${order.marketplace_order_id} - ${order.production_status}`));
    orderCard.append(node("p", {}, `${order.customer_name} - ${money(order.revenue_cents)} revenue - ${money(order.profit_cents)} profit`));
    orderCard.append(node("p", { class: "muted" }, order.customer_message));
    ordersRoot.append(orderCard);

    const replyCard = node("article", { class: "item-card" });
    replyCard.append(node("h3", {}, `${order.issue_type} reply`));
    if (order.manual_review_required) replyCard.append(node("span", { class: "pill warn" }, "Manual review required"));
    replyCard.append(node("pre", {}, order.draft_reply || "No draft yet."));
    replyCard.append(button("Approve Reply Locally", "button warn", () => post("/api/orders/approve-reply", { id: order.id }), Boolean(order.reply_approved_at) || Boolean(order.manual_review_required)));
    repliesRoot.append(replyCard);
  });
}

function renderAnalytics() {
  const root = document.getElementById("analytics-grid");
  const a = state.analytics || {};
  root.replaceChildren(
    metric("Revenue", money(a.revenue_cents)),
    metric("Profit", money(a.profit_cents)),
    metric("Average Order Value", money(a.average_order_value_cents)),
    metric("Pending", a.pending_orders || 0),
    metric("Completed", a.completed_orders || 0),
    metric("ROI", `${a.roi_percent || 0}%`),
    metric("Top Keywords", a.top_keywords || "none"),
    metric("Best Prompt", a.best_prompt || "none")
  );
}

function renderIntegrations() {
  const root = document.getElementById("integrations-grid");
  const integrations = state.integrations || {};
  root.replaceChildren();
  [
    ["openai", "OpenAI Images", "Generates real artwork files from approved prompts."],
    ["printify", "Printify", "Uploads artwork and creates print-on-demand products."],
    ["etsy", "Etsy", "Creates draft listings, uploads images, and publishes after approval."]
  ].forEach(([key, title, description]) => {
    const info = integrations[key] || {};
    const card = node("article", { class: "agent-card" });
    card.append(node("span", { class: info.ready ? "pill" : "pill warn" }, info.ready ? "Ready" : "Setup needed"));
    card.append(node("h3", {}, title));
    card.append(node("p", {}, description));
    if (info.model) card.append(node("p", { class: "muted" }, `Model: ${info.model}`));
    if (info.shop_id) card.append(node("p", { class: "muted" }, `Shop ID: ${info.shop_id}`));
    if (info.token_updated_at) card.append(node("p", { class: "muted" }, `OAuth connected: ${info.token_updated_at}`));
    if (info.missing && info.missing.length) {
      card.append(node("pre", {}, `Missing env vars:\n${info.missing.join("\n")}`));
    }
    const actions = node("div", { class: "actions" });
    if (key === "etsy") {
      actions.append(node("a", { class: "button primary", href: "/api/integrations/etsy/start" }, "Connect Etsy"));
    }
    card.append(actions);
    root.append(card);
  });
}

function renderSettings() {
  const root = document.getElementById("settings-list");
  root.replaceChildren();
  (state.agents || []).forEach((agent) => {
    const card = node("article", { class: "item-card" });
    card.append(node("h3", {}, agent.name));
    const form = node("form", { class: "inline-form" });
    const schedule = node("input", { name: "schedule_label", value: agent.schedule_label });
    const interval = node("input", { name: "interval_minutes", type: "number", min: "1", value: agent.interval_minutes });
    const enabled = node("select", { name: "enabled" });
    enabled.append(node("option", { value: "true" }, "enabled"));
    enabled.append(node("option", { value: "false" }, "paused"));
    enabled.value = agent.enabled ? "true" : "false";
    form.append(schedule, interval, enabled, button("Save", "button secondary", async () => {
      await post("/api/settings/agent", {
        id: agent.id,
        schedule_label: schedule.value,
        interval_minutes: interval.value,
        enabled: enabled.value === "true"
      });
    }));
    card.append(form);
    root.append(card);
  });
}

function renderNotifications() {
  const root = document.getElementById("notifications-list");
  root.replaceChildren();
  (state.notifications || []).forEach((item) => {
    const card = node("article", { class: "item-card" });
    card.append(node("span", { class: item.level === "success" ? "pill" : "pill warn" }, item.level));
    card.append(node("h3", {}, item.title));
    card.append(node("p", {}, item.message));
    root.append(card);
  });
}

function renderLogs() {
  const root = document.getElementById("logs-list");
  root.replaceChildren();
  (state.logs || []).forEach((log) => {
    const line = node("div", { class: "log-row" });
    line.append(node("strong", {}, `${log.agent_id}: ${log.action}`));
    line.append(document.createTextNode(` - ${log.entity_type} ${log.entity_id} - ${log.created_at} - ${log.execution_ms}ms`));
    if (log.details) line.append(node("div", {}, log.details));
    root.append(line);
  });
}

document.addEventListener("click", async (event) => {
  const target = event.target.closest("[data-run-agent]");
  if (!target) return;
  try {
    target.disabled = true;
    await post("/api/agents/run", { agent_id: target.dataset.runAgent });
  } catch (error) {
    alert(error.message);
    target.disabled = false;
  }
});

document.getElementById("run-core").addEventListener("click", async (event) => {
  const btn = event.currentTarget;
  btn.disabled = true;
  try {
    for (const agent_id of corePipeline) {
      await post("/api/agents/run", { agent_id });
    }
  } catch (error) {
    alert(error.message);
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("manual-product").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    await post("/api/products", Object.fromEntries(new FormData(form).entries()));
    form.reset();
  } catch (error) {
    alert(error.message);
  }
});

document.getElementById("theme-toggle").addEventListener("click", () => {
  document.documentElement.classList.toggle("dark");
  localStorage.setItem("pod_os_theme", document.documentElement.classList.contains("dark") ? "dark" : "light");
});

if (localStorage.getItem("pod_os_theme") === "dark") document.documentElement.classList.add("dark");
getState();
