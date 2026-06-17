"""Tests for vector store (in-memory fallback when chromadb is unavailable)."""

from __future__ import annotations

import pytest

from app.services.vector.store import VectorStore


@pytest.mark.asyncio
async def test_upsert_and_search() -> None:
    vs = VectorStore(collection_name="test_emails")
    await vs.upsert(
        doc_id="e1",
        text="Microsoft interview invitation for software engineer role",
        metadata={"user_id": "u1", "category": "interview_calls"},
    )
    await vs.upsert(
        doc_id="e2",
        text="HDFC bank statement for the month of May",
        metadata={"user_id": "u1", "category": "banking"},
    )
    results = await vs.search("job interview", k=2, filter_={"user_id": "u1"})
    assert len(results) >= 1
    assert any("Microsoft" in r["document"] for r in results)


@pytest.mark.asyncio
async def test_search_with_filter() -> None:
    vs = VectorStore(collection_name="test_emails2")
    await vs.upsert(
        doc_id="a",
        text="Bank statement HDFC",
        metadata={"user_id": "u1", "category": "banking"},
    )
    await vs.upsert(
        doc_id="b",
        text="Microsoft interview invitation",
        metadata={"user_id": "u1", "category": "interview_calls"},
    )
    res = await vs.search("bank", k=5, filter_={"category": "banking"})
    assert all(r["metadata"].get("category") == "banking" for r in res)
