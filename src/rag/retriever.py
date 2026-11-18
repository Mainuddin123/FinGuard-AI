
import logging
from typing import Any

from src.rag.hybrid_retriever import hybrid_retrieve
from src.rag.reranker import safe_rerank

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 4
MAX_TOP_K = 10


def retrieve_policy_context(
    query: str,
    k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """
    Complete policy retrieval pipeline:

    Query rewriting
        -> Dense + sparse retrieval
        -> Reciprocal Rank Fusion
        -> FlashRank reranking
        -> Top-k policy evidence
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Policy query must be a non-empty string.")

    if isinstance(k, bool) or not isinstance(k, int):
        raise TypeError("k must be an integer.")

    if not 1 <= k <= MAX_TOP_K:
        raise ValueError(
            f"k must be between 1 and {MAX_TOP_K}."
        )

    # Retrieve a larger candidate set before reranking.
    candidates = hybrid_retrieve(
        query=query.strip(),
        dense_k=8,
        sparse_k=8,
        rewrite=True,
        top_n=8,
    )

    if not candidates:
        return []

    # Rerank candidates and select the final top-k.
    results = safe_rerank(
        query=query.strip(),
        documents=candidates,
        top_n=k,
    )

    return results
