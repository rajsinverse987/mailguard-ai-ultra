"""Embedding generation (OpenAI primary, sentence-transformers fallback, hash fallback)."""

from __future__ import annotations

import hashlib
import math
from functools import lru_cache

import httpx

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Embedder:
    def __init__(self) -> None:
        self.model = settings.openai_embedding_model
        self._local = None
        self._local_failed = False

    async def embed(self, texts: list[str]) -> list[list[float]]:
        texts = [t[:8000] for t in texts if t]
        if not texts:
            return []
        if settings.openai_api_key:
            return await self._embed_openai(texts)
        if not self._local_failed:
            try:
                return await self._embed_local(texts)
            except Exception as exc:  # noqa: BLE001
                logger.warning("local_embed_failed_using_hash_fallback", error=str(exc))
                self._local_failed = True
        return [_hash_embed(t, settings.embedding_dim) for t in texts]

    async def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": texts}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            return [item["embedding"] for item in data["data"]]

    async def _embed_local(self, texts: list[str]) -> list[list[float]]:
        if self._local is None:
            from sentence_transformers import SentenceTransformer

            self._local = SentenceTransformer("all-MiniLM-L6-v2")
        vecs = self._local.encode(texts, normalize_embeddings=True).tolist()
        return vecs


def _hash_embed(text: str, dim: int) -> list[float]:
    """Deterministic fallback embedding (good enough for cosine similarity on keyword overlap).

    This is NOT suitable for production semantic search but keeps the system
    fully functional when no embedding model is available (e.g., tests, offline).
    """
    vec = [0.0] * dim
    tokens = text.lower().split()
    for tok in tokens:
        h = hashlib.sha256(tok.encode("utf-8")).digest()
        for i in range(0, len(h), 4):
            idx = int.from_bytes(h[i : i + 4], "big") % dim
            vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    return Embedder()
