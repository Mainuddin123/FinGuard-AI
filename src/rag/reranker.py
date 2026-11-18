
import logging
import math
from functools import lru_cache
from typing import Any

from flashrank import Ranker, RerankRequest

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_ranker() -> Ranker:
    """Load the FlashRank model once per process."""

    return Ranker(
        model_name="ms-marco-MiniLM-L-12-v2"
    )


def normalize_finite_score(
    value: Any,
    field_name: str,
) -> float:
    """
    Convert a numeric score to a finite Python float.

    Supports numeric types that implement float conversion,
    while rejecting booleans, invalid values, NaN and infinity.
    """

    if isinstance(value, bool):
        raise ValueError(
            f"{field_name} must be a numeric score, not boolean."
        )

    try:
        normalized = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(
            f"{field_name} must be a valid numeric score."
        ) from exc

    if not math.isfinite(normalized):
        raise ValueError(
            f"{field_name} must be finite."
        )

    return normalized


def validate_rerank_inputs(
    query: str,
    documents: list[dict[str, Any]],
    top_n: int,
) -> None:
    """Validate reranker inputs before execution."""

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    if (
        isinstance(top_n, bool)
        or not isinstance(top_n, int)
        or top_n < 1
    ):
        raise ValueError(
            "top_n must be a positive integer."
        )

    if not isinstance(documents, list):
        raise TypeError(
            "documents must be a list."
        )

    for document in documents:

        if not isinstance(document, dict):
            raise ValueError(
                "Each document must be a dictionary."
            )

        content = document.get("content")

        if (
            not isinstance(content, str)
            or not content.strip()
        ):
            raise ValueError(
                "Every document must contain non-empty content."
            )

        normalize_finite_score(
            document.get("rrf_score", 0.0),
            "Document rrf_score",
        )


class PolicyReranker:
    """Rerank retrieved policy documents by query relevance."""

    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_n: int = 4,
    ) -> list[dict[str, Any]]:

        validate_rerank_inputs(
            query,
            documents,
            top_n,
        )

        if not documents:
            return []

        passages = []

        for index, document in enumerate(documents):

            passages.append({
                "id": index,
                "text": document["content"],
                "meta": {
                    "source": document.get(
                        "source",
                        "unknown",
                    ),
                    "rrf_score": normalize_finite_score(
                        document.get("rrf_score", 0.0),
                        "Document rrf_score",
                    ),
                    "relevance_score": document.get(
                        "relevance_score"
                    ),
                },
            })

        request = RerankRequest(
            query=query.strip(),
            passages=passages,
        )

        results = get_ranker().rerank(request)

        if not isinstance(results, list):
            raise RuntimeError(
                "FlashRank returned an invalid result."
            )

        reranked = []

        for result in results[:top_n]:

            if not isinstance(result, dict):
                raise RuntimeError(
                    "FlashRank returned an invalid passage."
                )

            metadata = result.get("meta") or {}

            if not isinstance(metadata, dict):
                raise RuntimeError(
                    "FlashRank returned invalid metadata."
                )

            content = result.get("text")
            score = result.get("score")

            if (
                not isinstance(content, str)
                or not content.strip()
            ):
                raise RuntimeError(
                    "FlashRank result is missing passage text."
                )

            try:
                normalized_score = normalize_finite_score(
                    score,
                    "FlashRank score",
                )
            except ValueError as exc:
                raise RuntimeError(
                    "FlashRank returned an invalid score."
                ) from exc

            metadata_rrf_score = normalize_finite_score(
                metadata.get("rrf_score", 0.0),
                "FlashRank metadata rrf_score",
            )

            reranked.append({
                "content": content,
                "source": metadata.get(
                    "source",
                    "unknown",
                ),
                "rerank_score": normalized_score,
                "rrf_score": metadata_rrf_score,
                "relevance_score": metadata.get(
                    "relevance_score"
                ),
                "rerank_status": "reranked",
            })

        return reranked


def safe_rerank(
    query: str,
    documents: list[dict[str, Any]],
    top_n: int = 4,
) -> list[dict[str, Any]]:
    """
    Use RRF-ranked documents if FlashRank execution fails.

    Invalid input is rejected instead of silently falling back.
    """

    validate_rerank_inputs(
        query,
        documents,
        top_n,
    )

    if not documents:
        return []

    try:
        return PolicyReranker().rerank(
            query=query,
            documents=documents,
            top_n=top_n,
        )

    except Exception:
        logger.exception(
            "Policy reranking failed. "
            "Using RRF-ranked fallback results."
        )

        fallback_results = []

        for document in documents[:top_n]:

            fallback = dict(document)

            fallback["rerank_score"] = None
            fallback["rerank_status"] = "fallback"

            fallback_results.append(fallback)

        return fallback_results
