"""ChromaDB-backed vector store for semantic email search (RAG)."""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.services.ai.embeddings import get_embedder

logger = get_logger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    _HAS_CHROMA = True
except Exception:  # pragma: no cover
    _HAS_CHROMA = False


class VectorStore:
    """Thin async wrapper over a persistent ChromaDB collection."""

    def __init__(self, collection_name: str = "emails") -> None:
        self.collection_name = collection_name
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self._client = None
        self._collection = None

    def _ensure(self) -> None:
        if self._client is not None:
            return
        if not _HAS_CHROMA:
            logger.warning("chromadb_unavailable_fallback_to_inmemory")
            self._client = None
            return
        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def upsert(self, *, doc_id: str, text: str, metadata: dict[str, Any]) -> None:
        self._ensure()
        if not text.strip():
            return
        if self._collection is None:
            # In-memory fallback for dev/test environments without chromadb.
            await self._mem_upsert(doc_id, text, metadata)
            return

        embedder = get_embedder()
        vectors = await embedder.embed([text])
        self._collection.upsert(
            ids=[doc_id],
            documents=[text],
            embeddings=vectors,
            metadatas=[metadata],
        )

    async def _mem_upsert(self, doc_id: str, text: str, metadata: dict[str, Any]) -> None:
        if not hasattr(self, "_mem"):
            self._mem: dict[str, dict[str, Any]] = {}
        self._mem[doc_id] = {"text": text, "metadata": metadata}

    async def search(
        self,
        query: str,
        *,
        k: int = 5,
        filter_: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        self._ensure()
        embedder = get_embedder()
        vectors = await embedder.embed([query])
        if self._collection is None:
            return await self._mem_search(query, vectors[0], k, filter_)
        res = self._collection.query(
            query_embeddings=vectors,
            n_results=k,
            where=filter_,
        )
        items: list[dict[str, Any]] = []
        for i, doc_id in enumerate(res.get("ids", [[]])[0]):
            items.append(
                {
                    "id": doc_id,
                    "document": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i] if res.get("metadatas") else {},
                    "score": 1 - (res["distances"][0][i] if res.get("distances") else 0),
                }
            )
        return items

    async def _mem_search(
        self, query: str, qvec: list[float], k: int, filter_: dict[str, Any] | None
    ) -> list[dict[str, Any]]:
        if not hasattr(self, "_mem"):
            return []
        embedder = get_embedder()
        # Naive cosine over only matching docs (good enough for dev fallback)
        results: list[tuple[float, str, dict[str, Any]]] = []
        for doc_id, payload in self._mem.items():
            meta = payload["metadata"]
            if filter_ and not all(meta.get(k_) == v for k_, v in filter_.items()):
                continue
            doc_vec = (await embedder.embed([payload["text"]]))[0]
            score = _cosine(qvec, doc_vec)
            results.append((score, payload["text"], {"id": doc_id, **meta}))
        results.sort(key=lambda x: x[0], reverse=True)
        return [
            {"id": meta["id"], "document": text, "metadata": meta, "score": score}
            for score, text, meta in results[:k]
        ]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    num = sum(x * y for x, y in zip(a, b))
    den = (sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)
    return num / den if den else 0.0


_singleton: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _singleton
    if _singleton is None:
        _singleton = VectorStore()
    return _singleton
