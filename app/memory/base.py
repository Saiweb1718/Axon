from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..models import Evidence, Feedback, Interaction


class Memory(ABC):
    @abstractmethod
    def remember(self, item: Interaction) -> None:
        ...

    @abstractmethod
    def recall(self, query: str, account_id: Optional[str] = None, k: int = 6) -> list[Evidence]:
        ...

    @abstractmethod
    def improve(self, feedback: Feedback) -> None:
        ...

    @abstractmethod
    def forget(self, ref: str) -> None:
        ...

    # --- read helpers used by agents ---
    @abstractmethod
    def interactions(self, account_id: str) -> list[Interaction]:
        ...

    @abstractmethod
    def rejected_actions(self, account_id: str) -> list[str]:
        ...

    def recall_decisions(self, query: str, k: int = 3) -> list[dict]:
        """Recall how a human handled *similar* past situations (case memory)."""
        return []

    def graph_export(self, account_id: Optional[str] = None) -> dict:
        """Export the knowledge graph (nodes/edges) for inspection/visualisation."""
        return {"nodes": [], "edges": []}
