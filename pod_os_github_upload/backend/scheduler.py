from __future__ import annotations

import os
import threading
import time

from backend.agents import AgentRegistry


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


def start_embedded_scheduler(registry: AgentRegistry) -> None:
    enabled = os.environ.get("POD_OS_ENABLE_EMBEDDED_WORKER", "false").lower() == "true"
    if not enabled:
        return
    interval = max(60, int(os.environ.get("POD_OS_WORKER_INTERVAL_SECONDS", "1800")))
    agents = [agent.strip() for agent in os.environ.get("POD_OS_WORKER_AGENTS", ",".join(DEFAULT_AGENTS)).split(",") if agent.strip()]

    def loop() -> None:
        print(f"Embedded POD OS scheduler running every {interval}s for agents: {', '.join(agents)}")
        while True:
            for agent in agents:
                try:
                    result = registry.run(agent)
                    print(f"{agent}: {result}")
                except Exception as exc:
                    print(f"{agent} failed: {exc}")
            time.sleep(interval)

    thread = threading.Thread(target=loop, name="pod-os-scheduler", daemon=True)
    thread.start()
