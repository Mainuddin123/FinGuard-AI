
from unittest.mock import MagicMock, patch

import pytest

from src.rag.reranker import (
    PolicyReranker,
    safe_rerank,
)


@pytest.fixture
def sample_documents():
    return [
        {
            "content": "High-risk transactions require human review.",
            "source": "demo_policy.txt",
            "rrf_score": 0.03,
        },
        {
            "content": "Suspicious transactions must be investigated.",
            "source": "demo_policy.txt",
            "rrf_score": 0.02,
        },
    ]


def test_reranker_rejects_empty_query(sample_documents):
    with pytest.raises(ValueError):
        PolicyReranker().rerank(
            "",
            sample_documents,
        )


def test_reranker_rejects_invalid_top_n(sample_documents):
    with pytest.raises(ValueError):
        PolicyReranker().rerank(
            "transaction investigation",
            sample_documents,
            top_n=0,
        )


def test_reranker_rejects_invalid_document():
    with pytest.raises(ValueError):
        PolicyReranker().rerank(
            "transaction investigation",
            [{"content": ""}],
        )


def test_reranker_rejects_invalid_rrf_score():
    with pytest.raises(ValueError):
        PolicyReranker().rerank(
            "transaction investigation",
            [{
                "content": "Example policy.",
                "rrf_score": float("nan"),
            }],
        )


@patch("src.rag.reranker.get_ranker")
def test_successful_reranking(
    mock_get_ranker,
    sample_documents,
):
    mock_ranker = MagicMock()

    mock_ranker.rerank.return_value = [
        {
            "text": "High-risk transactions require human review.",
            "score": 0.85,
            "meta": {
                "source": "demo_policy.txt",
                "rrf_score": 0.03,
            },
        }
    ]

    mock_get_ranker.return_value = mock_ranker

    results = PolicyReranker().rerank(
        "high-risk transaction",
        sample_documents,
        top_n=1,
    )

    assert len(results) == 1
    assert results[0]["rerank_score"] == 0.85
    assert results[0]["rerank_status"] == "reranked"


@patch("src.rag.reranker.get_ranker")
def test_safe_rerank_fallback(
    mock_get_ranker,
    sample_documents,
):
    mock_ranker = MagicMock()

    mock_ranker.rerank.side_effect = RuntimeError(
        "FlashRank unavailable"
    )

    mock_get_ranker.return_value = mock_ranker

    results = safe_rerank(
        "high-risk transaction",
        sample_documents,
        top_n=1,
    )

    assert len(results) == 1
    assert results[0]["rerank_status"] == "fallback"
    assert results[0]["rerank_score"] is None


def test_safe_rerank_does_not_fallback_for_invalid_input():
    with pytest.raises(ValueError):
        safe_rerank(
            "",
            [{"content": "Example policy.", "rrf_score": 0.02}],
        )


def test_empty_documents_return_empty_list():
    assert safe_rerank(
        "transaction investigation",
        [],
    ) == []
