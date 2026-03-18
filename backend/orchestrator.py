from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncGenerator

from backend.agents.idea_agent import IdeaAgent
from backend.agents.planner_agent import PlannerAgent


@dataclass(slots=True)
class OrchestrationResult:
    idea: str
    plan: str


class BrainstormOrchestrator:
    """Coordinates Idea Agent -> Planner Agent with streaming support."""

    def __init__(self) -> None:
        self.idea_agent = IdeaAgent()
        self.planner_agent = PlannerAgent()

    async def run(self, user_text: str) -> OrchestrationResult:
        idea = await self.idea_agent.run(user_text)
        plan = await self.planner_agent.run(idea)
        return OrchestrationResult(idea=idea, plan=plan)

    async def stream(self, user_text: str) -> AsyncGenerator[dict, None]:
        yield {"event": "status", "message": "Expanding your idea...", "done": False}
        idea = await self.idea_agent.run(user_text)
        for chunk in self._chunk_text(idea, chunk_size=180):
            yield {"event": "idea_chunk", "chunk": chunk, "done": False}

        yield {"event": "status", "message": "Building your execution plan...", "done": False}
        plan = await self.planner_agent.run(idea)
        for chunk in self._chunk_text(plan, chunk_size=180):
            yield {"event": "plan_chunk", "chunk": chunk, "done": False}

        yield {
            "event": "final",
            "idea": idea,
            "plan": plan,
            "done": True,
        }

    def _chunk_text(self, text: str, chunk_size: int) -> list[str]:
        if not text:
            return []
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
