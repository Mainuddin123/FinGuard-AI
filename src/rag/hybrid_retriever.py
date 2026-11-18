
import hashlib
import logging
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

from src.rag.query_rewriter import (
    rewrite_query,
    clear_query_rewrite_cache,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

POLICY_DIR = PROJECT_ROOT / "data" / "policies"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

COLLECTION_NAME = "finguard_policies"
EMBEDDING_MODEL = "models/gemini-embedding-001"

CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

DEFAULT_DENSE_K = 8
DEFAULT_SPARSE_K = 8
DEFAULT_TOP_N = 8
RRF_K = 60


def tokenize(text: str) -> list[str]:
    """Tokenize text for BM25 retrieval."""

    if not isinstance(text, str):
        return []

    return re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())


def _validate_positive_integer(name: str, value: Any) -> None:
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value <= 0
    ):
        raise ValueError(f"{name} must be a positive integer.")


@lru_cache(maxsize=1)
def get_sparse_index() -> tuple[BM25Okapi, list[Document]]:
    """
    Build a cached BM25 index using the same chunking
    configuration as the ChromaDB ingestion pipeline.
    """

    if not POLICY_DIR.exists():
        raise RuntimeError(
            f"Policy directory not found: {POLICY_DIR}"
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    documents: list[Document] = []

    for file_path in sorted(POLICY_DIR.glob("*.txt")):
        try:
            text = file_path.read_text(
                encoding="utf-8"
            ).strip()

            if not text:
                logger.warning(
                    "Skipping empty policy file: %s",
                    file_path.name,
                )
                continue

            chunks = splitter.split_text(text)

            for chunk_index, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": file_path.name,
                            "chunk": chunk_index,
                        },
                    )
                )

        except OSError:
            logger.exception(
                "Could not read policy file: %s",
                file_path.name,
            )

    if not documents:
        raise RuntimeError(
            "No readable policy chunks found."
        )

    tokenized_corpus = [
        tokenize(document.page_content)
        for document in documents
    ]

    if not any(tokenized_corpus):
        raise RuntimeError(
            "Policy documents contain no searchable tokens."
        )

    bm25_index = BM25Okapi(tokenized_corpus)

    logger.info(
        "BM25 index created with %d policy chunks.",
        len(documents),
    )

    return bm25_index, documents


def sparse_search(
    query: str,
    k: int = DEFAULT_SPARSE_K,
) -> list[Document]:
    """Retrieve the top-k policy chunks using BM25."""

    _validate_positive_integer("k", k)

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    bm25_index, documents = get_sparse_index()

    scores = bm25_index.get_scores(query_tokens)

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda index: float(scores[index]),
        reverse=True,
    )

    results = []

    for index in ranked_indices:
        if len(results) >= k:
            break

        # Do not return documents with zero or negative scores.
        if not math.isfinite(float(scores[index])):
            continue

        if scores[index] <= 0:
            continue

        results.append(documents[index])

    return results


@lru_cache(maxsize=1)
def get_dense_store() -> Chroma:
    """Connect to the existing persistent ChromaDB collection."""

    if not CHROMA_DIR.exists():
        raise RuntimeError(
            f"ChromaDB directory not found: {CHROMA_DIR}"
        )

    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        task_type="RETRIEVAL_QUERY",
    )

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )

    collection_data = vector_store.get(limit=1)

    if not collection_data.get("ids"):
        raise RuntimeError(
            "ChromaDB collection is empty. "
            "Run policy ingestion first."
        )

    return vector_store


def reciprocal_rank_fusion(
    result_lists: list[list[Document]],
    weights: list[float] | None = None,
    k: int = RRF_K,
) -> list[dict[str, Any]]:
    """Combine ranked retrieval results using RRF."""

    if not isinstance(result_lists, list):
        raise TypeError("result_lists must be a list.")

    _validate_positive_integer("RRF k", k)

    if weights is None:
        weights = [1.0] * len(result_lists)

    if not isinstance(weights, list):
        raise TypeError("weights must be a list.")

    if len(weights) != len(result_lists):
        raise ValueError(
            "Number of weights must match result lists."
        )

    for weight in weights:
        if (
            isinstance(weight, bool)
            or not isinstance(weight, (int, float))
            or not math.isfinite(weight)
            or weight < 0
        ):
            raise ValueError(
                "Weights must be finite, non-negative numbers."
            )

    fused_scores: dict[str, dict[str, Any]] = {}

    for result_list, weight in zip(result_lists, weights):

        if not isinstance(result_list, list):
            raise TypeError(
                "Each retrieval result must be a list."
            )

        seen_in_list: set[str] = set()

        for rank, document in enumerate(result_list, start=1):

            if not isinstance(document, Document):
                continue

            content = document.page_content

            if not isinstance(content, str) or not content.strip():
                continue

            source = str(
                document.metadata.get("source", "unknown")
            )

            identity = hashlib.sha256(
                f"{source}|{content}".encode("utf-8")
            ).hexdigest()

            if identity in seen_in_list:
                continue

            seen_in_list.add(identity)

            if identity not in fused_scores:
                fused_scores[identity] = {
                    "content": content,
                    "source": source,
                    "rrf_score": 0.0,
                }

            fused_scores[identity]["rrf_score"] += (
                float(weight) / (k + rank)
            )

    return sorted(
        fused_scores.values(),
        key=lambda item: item["rrf_score"],
        reverse=True,
    )


def hybrid_retrieve(
    query: str,
    dense_k: int = DEFAULT_DENSE_K,
    sparse_k: int = DEFAULT_SPARSE_K,
    rewrite: bool = True,
    top_n: int = DEFAULT_TOP_N,
) -> list[dict[str, Any]]:
    """
    Dense + sparse retrieval followed by RRF.

    Either retrieval method can continue independently
    if the other method fails.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    _validate_positive_integer("dense_k", dense_k)
    _validate_positive_integer("sparse_k", sparse_k)
    _validate_positive_integer("top_n", top_n)

    if not isinstance(rewrite, bool):
        raise ValueError("rewrite must be a boolean.")

    search_query = query.strip()

    if rewrite:
        search_query = rewrite_query(search_query)

    if not isinstance(search_query, str) or not search_query.strip():
        raise RuntimeError(
            "Query rewriting returned an invalid query."
        )

    retrieval_results: list[list[Document]] = []

    # Dense retrieval
    try:
        dense_store = get_dense_store()

        dense_results = dense_store.similarity_search(
            search_query,
            k=dense_k,
        )

        if not isinstance(dense_results, list):
            raise TypeError(
                "Dense retrieval returned an invalid result."
            )

        retrieval_results.append(dense_results)

        logger.info(
            "Dense retrieval returned %d documents.",
            len(dense_results),
        )

    except Exception:
        logger.exception("Dense retrieval failed.")

    # Sparse retrieval
    try:
        sparse_results = sparse_search(
            search_query,
            k=sparse_k,
        )

        retrieval_results.append(sparse_results)

        logger.info(
            "Sparse retrieval returned %d documents.",
            len(sparse_results),
        )

    except Exception:
        logger.exception("Sparse retrieval failed.")

    if not retrieval_results or not any(retrieval_results):
        raise RuntimeError(
            "Dense and sparse retrieval returned no policy documents."
        )

    # Assign equal weights to the available retrieval methods.
    fused_results = reciprocal_rank_fusion(
        retrieval_results,
        weights=[1.0] * len(retrieval_results),
    )

    if not fused_results:
        raise RuntimeError(
            "No policy documents available after RRF."
        )

    return fused_results[:top_n]


def clear_retrieval_caches() -> None:
    """Clear cached retrieval indexes and rewritten queries."""

    get_sparse_index.cache_clear()
    get_dense_store.cache_clear()
    clear_query_rewrite_cache()

    logger.info(
        "Retrieval caches cleared successfully."
    )
