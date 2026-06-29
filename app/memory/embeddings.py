
from __future__ import annotations

import hashlib
import os
import re
from abc import ABC, abstractmethod

import numpy as np

DIM = 256
_WORD = re.compile(r"[a-z0-9]+")


class EmbeddingProvider(ABC):
    dim: int = DIM
    name: str = "base"

    @abstractmethod
    def embed(self, text: str) -> np.ndarray:
        ...

    def embed_many(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self.embed(t) for t in texts])


class HashEmbeddings(EmbeddingProvider):
    """Deterministic hashed bag-of-features: words + character trigrams.

    Captures lexical AND sub-word similarity (renew / renewal / renewing collide
    on shared trigrams) — meaningfully better recall than exact keyword overlap,
    with zero heavy dependencies. The architecture (embed -> cosine) is identical
    to a transformer pipeline, so swapping in real embeddings is one env var.
    """

    name = "hash-local"

    def __init__(self, dim: int = DIM) -> None:
        self.dim = dim

    def _features(self, text: str):
        for w in _WORD.findall(text.lower()):
            yield w
            if len(w) > 3:
                padded = f"#{w}#"
                for i in range(len(padded) - 2):
                    yield padded[i : i + 3]

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        for feat in self._features(text or ""):
            h = int(hashlib.md5(feat.encode()).hexdigest(), 16)
            vec[h % self.dim] += 1.0 if (h >> 8) & 1 else -1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec


class GeminiEmbeddings(EmbeddingProvider):
    """Real transformer embeddings via Google text-embedding-004 (opt-in)."""

    name = "gemini-text-004"

    def __init__(self) -> None:
        from google import genai

        self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.dim = 768
        self._model = "text-embedding-004"

    def embed(self, text: str) -> np.ndarray:
        r = self._client.models.embed_content(model=self._model, contents=text or " ")
        if not r.embeddings:
            return np.zeros(self.dim, dtype=np.float32)
        v = np.asarray(r.embeddings[0].values, dtype=np.float32)
        n = np.linalg.norm(v)
        return v / n if n > 0 else v


def get_embedder() -> EmbeddingProvider:
    if os.environ.get("EMBED_PROVIDER", "").lower() == "gemini" and os.environ.get("GEMINI_API_KEY"):
        try:
            return GeminiEmbeddings()
        except Exception as exc:  # pragma: no cover - depends on env
            print(f"[embeddings] Gemini unavailable ({exc}); using local hash embedder.")
    return HashEmbeddings()
