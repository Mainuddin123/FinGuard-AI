
import logging
import re
from functools import lru_cache

from src.llm import llm

logger = logging.getLogger(__name__)


@lru_cache(maxsize=256)
def _rewrite_cached(query: str) -> str:
    """Rewrite and cache normalized policy queries."""

    prompt = f"""
You are a search-query rewriting assistant for a
financial transaction investigation policy knowledge base.

Rewrite the following question into a concise search query.

Rules:
1. Preserve the original meaning.
2. Preserve important financial and policy terminology.
3. Do not answer the question.
4. Do not invent facts.
5. Return only the rewritten query.

Question:
{query}
"""

    response = llm.invoke(prompt)
    content = response.content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))

        content = " ".join(parts)

    if not isinstance(content, str):
        raise ValueError("Invalid query rewriting response.")

    rewritten = re.sub(r"\s+", " ", content).strip()

    return rewritten or query


def rewrite_query(query: str) -> str:
    """Rewrite a query with safe fallback to the original query."""

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    normalized_query = re.sub(
        r"\s+",
        " ",
        query,
    ).strip()

    try:
        return _rewrite_cached(normalized_query)

    except Exception:
        logger.exception(
            "Query rewriting failed. Using original query."
        )
        return normalized_query


def clear_query_rewrite_cache() -> None:
    """Clear cached rewritten queries."""

    _rewrite_cached.cache_clear()
