"""Agent contract + the reusable registry the planner orchestrates over."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..llm.base import LLMProvider
from ..memory.base import Memory


@dataclass
class Context:
    """The shared 'blackboard' passed between agents during one run."""
    account_id: str
    goal: str
    memory: Memory
    llm: LLMProvider
    config: dict[str, Any]
    bb: dict[str, Any] = field(default_factory=dict)   # blackboard: agents read/write here
    needs: list[str] = field(default_factory=list)     # missing-info tags-> triggers re-plan
    trace: list[str] = field(default_factory=list)     # human-readable reasoning trace


class Agent(ABC):
    name: str = "agent"
    description: str = ""
    inputs: list[str] = []
    outputs: list[str] = []

    @abstractmethod
    def run(self, ctx: Context) -> None:
        ...
REGISTRY: dict[str, Agent] = {}


def register(agent: Agent) -> Agent:
    REGISTRY[agent.name] = agent
    return agent


def registry_manifest() -> list[dict]:
    """What the planner sees: the catalogue of available capabilities."""
    return [
        {"name": a.name, "description": a.description, "inputs": a.inputs, "outputs": a.outputs}
        for a in REGISTRY.values()
    ]
