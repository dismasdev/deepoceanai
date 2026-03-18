from __future__ import annotations

import logging

from gradient_adk import entrypoint

from backend.orchestrator import BrainstormOrchestrator

logger = logging.getLogger(__name__)


@entrypoint
async def main(input: dict, context: dict) -> dict:
    """ADK entrypoint for Gradient agent run/deploy workflows."""
    prompt = (input or {}).get("prompt", "").strip()
    logger.info("Received ADK request")

    orchestrator = BrainstormOrchestrator()
    result = await orchestrator.run(prompt)

    return {
        "idea": result.idea,
        "plan": result.plan,
        "response": f"Idea:\n{result.idea}\n\nPlan:\n{result.plan}",
        "streaming_enabled": True,
    }
