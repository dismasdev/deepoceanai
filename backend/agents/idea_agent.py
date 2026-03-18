from __future__ import annotations

import os
from typing import Any


class IdeaAgent:
    """Expands a user idea into a structured concept."""

    async def run(self, user_input: str) -> str:
        cleaned = user_input.strip()
        if not cleaned:
            return "No idea was provided. Ask the user for a short concept to expand."

        # DeepOcean/Gradient integration point:
        # Set ENABLE_GRADIENT_AGENT=true and GRADIENT_MODEL_ACCESS_KEY to use a real model.
        if os.getenv("ENABLE_GRADIENT_AGENT", "false").lower() == "true":
            gradient_output = await self._run_with_gradient(cleaned)
            if gradient_output:
                return gradient_output

        # Deterministic low-latency fallback for local MVP.
        return (
            f"Concept: {cleaned}\n"
            f"Target users: Teams and solo builders who need structured brainstorming quickly.\n"
            f"Value proposition: Turn rough thoughts into concrete opportunities and focused execution steps.\n"
            f"Differentiators: Voice-first workflow, multi-agent reasoning, and immediate action planning.\n"
            f"Risks: Scope creep, unclear success metrics, and integration complexity.\n"
            f"Validation: Test with 5 pilot users, measure idea clarity and plan completion rate."
        )

    async def _run_with_gradient(self, user_input: str) -> str | None:
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
                            "You are Idea Agent. Expand user ideas into concise, practical structured concepts."
                        ),
                    },
                    {"role": "user", "content": user_input},
                ],
                stream=False,
            )
            return response.choices[0].message.content
        except Exception:
            return None
