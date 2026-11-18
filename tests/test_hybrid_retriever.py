
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from src.rag.hybrid_retriever import (
    hybrid_retrieve,
    reciprocal_rank_fusion,
    clear_retrieval_caches,
)


def make_document(
    content: str,
    source: str = "demo_policy.txt",
) -> Document:
    return Document(
        page_content=content,
        metadata={"source": source},
    )


# --------------------------------------------------
# Reciprocal Rank Fusion tests
# --------------------------------------------------

def test_rrf_combines_ranked_documents():
    doc1 = make_document("Human review is required.")
    doc2 = make_document(
        "Suspicious transfers require investigation."
    )

    results = reciprocal_rank_fusion(
        [
            [doc1, doc2],
            [doc2, doc1],
        ]
    )

    assert len(results) == 2
    assert results[0]["rrf_score"] > 0
    assert results[1]["rrf_score"] > 0


def test_rrf_deduplicates_documents():
    document = make_document("Human review is required.")

    results = reciprocal_rank_fusion(
        [
            [document, document],
            [document],
        ]
    )

    assert len(results) == 1


def test_rrf_combines_duplicate_scores():
    document = make_document("Human review is required.")

    results = reciprocal_rank_fusion(
        [
            [document],
            [document],
        ]
    )

    expected_score = (1 / 61) + (1 / 61)

    assert len(results) == 1
    assert results[0]["rrf_score"] == pytest.approx(
        expected_score
    )


def test_rrf_rejects_invalid_k():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([], k=0)


def test_rrf_rejects_boolean_k():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([], k=True)


def test_rrf_rejects_mismatched_weights():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion(
            [[], []],
            weights=[1.0],
        )


def test_rrf_rejects_non_list_result_lists():
    with pytest.raises(TypeError):
        reciprocal_rank_fusion("invalid")


def test_rrf_rejects_non_list_inner_results():
    with pytest.raises(TypeError):
        reciprocal_rank_fusion(
            ["invalid"]
        )


@pytest.mark.parametrize(
    "weights",
    [
        [-1.0],
        [float("nan")],
        [float("inf")],
        [float("-inf")],
        [True],
    ],
)
def test_rrf_rejects_invalid_weights(weights):
    with pytest.raises(ValueError):
        reciprocal_rank_fusion(
            [[]],
            weights=weights,
        )


def test_rrf_rejects_non_list_weights():
    with pytest.raises(TypeError):
        reciprocal_rank_fusion(
            [[]],
            weights=(1.0,),
        )


def test_rrf_ignores_invalid_document_entries():
    valid_document = make_document(
        "Human review is required."
    )

    results = reciprocal_rank_fusion(
        [
            [None, valid_document]
        ]
    )

    assert len(results) == 1
    assert results[0]["content"] == (
        "Human review is required."
    )


# --------------------------------------------------
# Hybrid retrieval validation tests
# --------------------------------------------------

def test_hybrid_retrieve_rejects_empty_query():
    with pytest.raises(ValueError):
        hybrid_retrieve("", rewrite=False)


def test_hybrid_retrieve_rejects_whitespace_query():
    with pytest.raises(ValueError):
        hybrid_retrieve("   ", rewrite=False)


@pytest.mark.parametrize(
    "parameter,value",
    [
        ("dense_k", 0),
        ("dense_k", -1),
        ("sparse_k", 0),
        ("sparse_k", -1),
        ("top_n", 0),
        ("top_n", -1),
    ],
)
def test_hybrid_retrieve_rejects_invalid_parameters(
    parameter,
    value,
):
    with pytest.raises(ValueError):
        hybrid_retrieve(
            "transaction policy",
            rewrite=False,
            **{parameter: value},
        )


def test_hybrid_retrieve_rejects_boolean_k():
    with pytest.raises(ValueError):
        hybrid_retrieve(
            "transaction policy",
            dense_k=True,
            rewrite=False,
        )


def test_hybrid_retrieve_rejects_invalid_rewrite_type():
    with pytest.raises(ValueError):
        hybrid_retrieve(
            "transaction policy",
            rewrite="yes",
        )


# --------------------------------------------------
# Dense and sparse retrieval fallback tests
# --------------------------------------------------

@patch("src.rag.hybrid_retriever.sparse_search")
@patch("src.rag.hybrid_retriever.get_dense_store")
def test_sparse_retrieval_works_when_dense_fails(
    mock_dense_store,
    mock_sparse_search,
):
    mock_dense_store.side_effect = RuntimeError(
        "Dense database unavailable"
    )

    mock_sparse_search.return_value = [
        make_document(
            "Suspicious transfers require review."
        )
    ]

    results = hybrid_retrieve(
        "suspicious transfers",
        rewrite=False,
    )

    assert len(results) == 1
    assert results[0]["source"] == "demo_policy.txt"

    mock_sparse_search.assert_called_once_with(
        "suspicious transfers",
        k=8,
    )


@patch("src.rag.hybrid_retriever.sparse_search")
@patch("src.rag.hybrid_retriever.get_dense_store")
def test_dense_retrieval_works_when_sparse_fails(
    mock_dense_store,
    mock_sparse_search,
):
    mock_store = MagicMock()

    mock_store.similarity_search.return_value = [
        make_document("Human review is required.")
    ]

    mock_dense_store.return_value = mock_store

    mock_sparse_search.side_effect = RuntimeError(
        "BM25 index unavailable"
    )

    results = hybrid_retrieve(
        "human review",
        rewrite=False,
    )

    assert len(results) == 1
    assert results[0]["source"] == "demo_policy.txt"

    mock_store.similarity_search.assert_called_once_with(
        "human review",
        k=8,
    )


@patch("src.rag.hybrid_retriever.sparse_search")
@patch("src.rag.hybrid_retriever.get_dense_store")
def test_both_retrievers_fail(
    mock_dense_store,
    mock_sparse_search,
):
    mock_dense_store.side_effect = RuntimeError(
        "ChromaDB unavailable"
    )

    mock_sparse_search.side_effect = RuntimeError(
        "BM25 unavailable"
    )

    with pytest.raises(RuntimeError):
        hybrid_retrieve(
            "transaction investigation",
            rewrite=False,
        )


@patch("src.rag.hybrid_retriever.sparse_search")
@patch("src.rag.hybrid_retriever.get_dense_store")
def test_both_retrievers_return_empty_results(
    mock_dense_store,
    mock_sparse_search,
):
    mock_store = MagicMock()

    mock_store.similarity_search.return_value = []

    mock_dense_store.return_value = mock_store
    mock_sparse_search.return_value = []

    with pytest.raises(RuntimeError):
        hybrid_retrieve(
            "transaction investigation",
            rewrite=False,
        )


# --------------------------------------------------
# Cache management tests
# --------------------------------------------------

@patch("src.rag.hybrid_retriever.clear_query_rewrite_cache")
@patch("src.rag.hybrid_retriever.get_dense_store")
@patch("src.rag.hybrid_retriever.get_sparse_index")
def test_clear_retrieval_caches(
    mock_sparse_index,
    mock_dense_store,
    mock_query_cache,
):
    clear_retrieval_caches()

    mock_sparse_index.cache_clear.assert_called_once()
    mock_dense_store.cache_clear.assert_called_once()
    mock_query_cache.assert_called_once()
