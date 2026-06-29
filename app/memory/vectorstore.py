from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np


@dataclass
class VectorStore:
    dim: int
    refs: list[str] = field(default_factory=list)
    meta: list[dict] = field(default_factory=list)
    _mat: Optional[np.ndarray] = None

    def add(self, ref: str, vec: np.ndarray, meta: dict) -> None:
        self.refs.append(ref)
        self.meta.append(meta)
        row = vec.reshape(1, -1).astype(np.float32)
        self._mat = row if self._mat is None else np.vstack([self._mat, row])

    def delete(self, ref: str) -> None:
        keep = [i for i, r in enumerate(self.refs) if r != ref]
        self.refs = [self.refs[i] for i in keep]
        self.meta = [self.meta[i] for i in keep]
        self._mat = self._mat[keep] if (self._mat is not None and keep) else None

    def search(
        self, vec: np.ndarray, k: int = 6, where: Optional[Callable[[dict], bool]] = None
    ) -> list[tuple[float, dict]]:
        if self._mat is None or not self.refs:
            return []
        sims = self._mat @ vec.astype(np.float32)
        out: list[tuple[float, dict]] = []
        for i in np.argsort(-sims):
            m = self.meta[int(i)]
            if where and not where(m):
                continue
            out.append((float(sims[int(i)]), m))
            if len(out) >= k:
                break
        return out
