from __future__ import annotations

import os
import time

from backend.agents import AgentRegistry
from backend.core.db import init_db


DEFAULT_AGENTS = [
    "market_research",
    "product_strategy",
    "prompt_engineering",
    "image_generation",
    "mockup",
    "listing",
    "order",
    "customer_service",
    "analytics",
]


def main() -> None:
    init_db()
    registry = AgentRegistry()
    registry.seed_agents()
    interval = max(60, int(os.environ.get("POD_OS_WORKER_INTERVAL_SECONDS", "900")))
    agents = [agent.strip() for agent in os.environ.get("POD_OS_WORKER_AGENTS", ",".join(DEFAULT_AGENTS)).split(",") if agent.strip()]
    print(f"POD OS worker running every {interval}s for agents: {', '.join(agents)}")
    while True:
        for agent in agents:
            try:
                result = registry.run(agent)
                print(f"{agent}: {result}")
            except Exception as exc:
                print(f"{agent} failed: {exc}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
