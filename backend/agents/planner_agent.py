from __future__ import annotations

import os
from typing import Any


class PlannerAgent:
    """Builds a practical plan from an expanded idea."""

    async def run(self, expanded_idea: str) -> str:
        cleaned = expanded_idea.strip()
        if not cleaned:
            return "No expanded idea available. Generate idea details before planning."

        # DeepOcean/Gradient integration point for real model-based planning.
        if os.getenv("ENABLE_GRADIENT_AGENT", "false").lower() == "true":
            gradient_output = await self._run_with_gradient(cleaned)
            if gradient_output:
                return gradient_output

        return (
            "1. Define the problem statement and success metric in one sentence.\n"
            "2. Identify target users and interview at least five people this week.\n"
            "3. Build an MVP workflow with audio input, idea expansion, and plan output.\n"
            "4. Run a pilot with real users and track completion time and satisfaction.\n"
            "5. Prioritize top issues, iterate in weekly cycles, and publish a roadmap."
        )

    async def _run_with_gradient(self, expanded_idea: str) -> str | None:
        try:
            from gradient import AsyncGradient

            client = AsyncGradient(
                inference_endpoint=os.getenv("GRADIENT_INFERENCE_ENDPOINT", "https://inference.do-ai.run"),
                model_access_key=os.getenv("GRADIENT_MODEL_ACCESS_KEY"),
            )
            model = os.getenv("GRADIENT_MODEL_ID", "openai-gpt-oss-120b")
            response: Any = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are Planner Agent. Create short, actionable, ordered steps from an idea."
                        ),
                    },
                    {"role": "user", "content": expanded_idea},
                ],
                stream=False,
            )
            return response.choices[0].message.content
        except Exception:
            return None
