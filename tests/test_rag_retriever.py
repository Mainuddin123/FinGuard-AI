
from unittest.mock import patch

import pytest

from src.rag.retriever import retrieve_policy_context


def test_empty_query_rejected():
    with pytest.raises(ValueError):
        retrieve_policy_context("")


def test_whitespace_query_rejected():
    with pytest.raises(ValueError):
        retrieve_policy_context("   ")


@pytest.mark.parametrize("k", [0, -1, 11])
def test_invalid_k_rejected(k):
    with pytest.raises(ValueError):
        retrieve_policy_context(
            "transaction investigation",
            k=k,
        )


def test_invalid_k_type_rejected():
    with pytest.raises(TypeError):
        retrieve_policy_context(
            "transaction investigation",
            k="4",
        )


@patch("src.rag.retriever.safe_rerank")
@patch("src.rag.retriever.hybrid_retrieve")
def test_successful_policy_retrieval(
    mock_hybrid,
    mock_rerank,
):
    candidates = [
        {
            "content": "High-risk transactions require human review.",
            "source": "demo_policy.txt",
            "rrf_score": 0.032,
        }
    ]

    expected_results = [
        {
            "content": "High-risk transactions require human review.",
            "source": "demo_policy.txt",
            "rrf_score": 0.032,
            "rerank_score": 0.85,
        }
    ]

    mock_hybrid.return_value = candidates
    mock_rerank.return_value = expected_results

    result = retrieve_policy_context(
        "high-risk transaction",
        k=4,
    )

    assert len(result) == 1

    assert result[0]["content"] == (
        "High-risk transactions require human review."
    )

    assert result[0]["source"] == "demo_policy.txt"
    assert result[0]["rerank_score"] == 0.85

    mock_hybrid.assert_called_once_with(
        query="high-risk transaction",
        dense_k=8,
        sparse_k=8,
        rewrite=True,
        top_n=8,
    )

    mock_rerank.assert_called_once_with(
        query="high-risk transaction",
        documents=candidates,
        top_n=4,
    )


@patch("src.rag.retriever.safe_rerank")
@patch("src.rag.retriever.hybrid_retrieve")
def test_empty_retrieval_results(
    mock_hybrid,
    mock_rerank,
):
    mock_hybrid.return_value = []

    result = retrieve_policy_context(
        "unknown policy query"
    )

    assert result == []

    mock_rerank.assert_not_called()


@patch("src.rag.retriever.safe_rerank")
@patch("src.rag.retriever.hybrid_retrieve")
def test_reranking_empty_results(
    mock_hybrid,
    mock_rerank,
):
    mock_hybrid.return_value = [
        {
            "content": "Example policy passage.",
            "source": "demo_policy.txt",
            "rrf_score": 0.02,
        }
    ]

    mock_rerank.return_value = []

    result = retrieve_policy_context(
        "example policy",
        k=4,
    )

    assert result == []
