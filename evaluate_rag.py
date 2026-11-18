
import os
import time
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    LLMContextPrecisionWithReference,
    LLMContextRecall,
)

from src.llm import primary_llm
from src.rag.hybrid_retriever import hybrid_retrieve
from src.rag.reranker import safe_rerank


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TOP_K = 4

TEST_CASES = [
    {
        "question": "When should suspicious transfers be investigated?",
        "reference": (
            "A transaction should be reviewed when multiple unusual "
            "signals are present. A single unusual signal should not "
            "automatically establish fraud."
        ),
    },
    {
        "question": "How should missing or inconsistent transaction "
                    "information be treated?",
        "reference": (
            "Missing or inconsistent information must be treated as "
            "unknown rather than proof of fraud."
        ),
    },
    {
        "question": "What should happen when a case has insufficient evidence?",
        "reference": (
            "Cases with insufficient evidence, conflicting signals, "
            "or failed policy retrieval should be escalated for "
            "manual investigation."
        ),
    },
    {
        "question": "Can the system automatically freeze accounts or "
                    "reverse payments?",
        "reference": (
            "The system must not automatically freeze accounts, "
            "reverse payments, or declare a customer guilty of fraud."
        ),
    },
    {
        "question": "What evidence should an investigation report contain?",
        "reference": (
            "Investigation reports must distinguish observed facts, "
            "calculated risk signals, and assumptions. The system "
            "must not invent missing transaction details."
        ),
    },
]


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def extract_contexts(documents):
    """Extract valid text contexts from retrieved documents."""

    if not isinstance(documents, list):
        return []

    contexts = []

    for item in documents:
        if not isinstance(item, dict):
            continue

        content = item.get("content")

        if isinstance(content, str) and content.strip():
            contexts.append(content.strip())

    return contexts


def average(values):
    """Calculate average safely."""

    return sum(values) / len(values) if values else None


# --------------------------------------------------
# MAIN EVALUATION
# --------------------------------------------------

def main():

    print("\n========== FINGUARD AI RAG EVALUATION ==========\n")

    if not os.getenv("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY missing from .env")

    evaluator_llm = LangchainLLMWrapper(primary_llm)

    evaluation_rows = []
    method_labels = []

    retrieval_times = []
    reranking_times = []
    total_times = []

    retrieval_failures = 0
    rerank_fallbacks = 0

    for index, case in enumerate(TEST_CASES, start=1):

        question = case["question"]

        print(f"\n[{index}/{len(TEST_CASES)}] {question}")

        # ------------------------------------------
        # 1. HYBRID RETRIEVAL
        # ------------------------------------------

        retrieval_start = time.perf_counter()

        try:
            retrieved = hybrid_retrieve(question)

        except Exception:
            retrieval_failures += 1
            logger.exception("Hybrid retrieval failed: %s", question)
            continue

        retrieval_latency = time.perf_counter() - retrieval_start

        if not retrieved:
            retrieval_failures += 1
            logger.warning("No documents retrieved for: %s", question)
            continue

        # Fair baseline: use the same top K as reranking.
        baseline_documents = retrieved[:TOP_K]
        baseline_contexts = extract_contexts(baseline_documents)

        if not baseline_contexts:
            retrieval_failures += 1
            logger.warning("No valid baseline contexts: %s", question)
            continue

        # ------------------------------------------
        # 2. FLASHRANK RERANKING
        # ------------------------------------------

        rerank_start = time.perf_counter()

        reranked = safe_rerank(
            query=question,
            documents=retrieved,
            top_n=TOP_K,
        )

        rerank_latency = time.perf_counter() - rerank_start

        reranked_contexts = extract_contexts(reranked)

        if not reranked_contexts:
            logger.warning(
                "No valid reranked contexts. Using baseline contexts."
            )
            reranked_contexts = baseline_contexts

        if any(
            item.get("rerank_status") == "fallback"
            for item in reranked
            if isinstance(item, dict)
        ):
            rerank_fallbacks += 1

        total_latency = retrieval_latency + rerank_latency

        # ------------------------------------------
        # 3. BUILD EVALUATION DATASET
        # ------------------------------------------

        common_reference = case["reference"]

        evaluation_rows.append({
            "user_input": question,
            "retrieved_contexts": baseline_contexts,
            "reference": common_reference,
        })
        method_labels.append("RRF_Baseline")

        evaluation_rows.append({
            "user_input": question,
            "retrieved_contexts": reranked_contexts,
            "reference": common_reference,
        })
        method_labels.append("RRF_FlashRank")

        retrieval_times.append(retrieval_latency)
        reranking_times.append(rerank_latency)
        total_times.append(total_latency)

        print(f"Baseline contexts: {len(baseline_contexts)}")
        print(f"Reranked contexts: {len(reranked_contexts)}")
        print(f"Retrieval latency: {retrieval_latency:.3f}s")
        print(f"Reranking latency: {rerank_latency:.3f}s")
        print(f"Total latency: {total_latency:.3f}s")

    # ----------------------------------------------
    # 4. VALIDATE DATASET
    # ----------------------------------------------

    if not evaluation_rows:
        raise RuntimeError("No valid evaluation samples available.")

    print("\nEvaluation samples:", len(evaluation_rows))
    print("Original questions evaluated:", len(total_times))

    dataset = EvaluationDataset.from_list(evaluation_rows)

    # ----------------------------------------------
    # 5. RAGAS METRICS
    # ----------------------------------------------

    metrics = [
    LLMContextPrecisionWithReference(llm=evaluator_llm),
    LLMContextRecall(llm=evaluator_llm),
    ]

    print("\nRunning RAGAS evaluation...")
    print("This step requires Gemini API calls.\n")

    results = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=evaluator_llm,
        raise_exceptions=False,
        show_progress=True,
    )

    scores = results.to_pandas()

    if len(scores) != len(method_labels):
        raise RuntimeError(
            "Evaluation result count does not match input dataset."
        )

    scores.insert(0, "method", method_labels)

    # ----------------------------------------------
    # 6. SAVE EVALUATION RESULTS
    # ----------------------------------------------

    report_path = OUTPUT_DIR / "rag_evaluation.csv"

    scores.to_csv(
        report_path,
        index=False,
    )

    # ----------------------------------------------
    # 7. LATENCY REPORT
    # ----------------------------------------------

    latency_report = {
        "evaluated_questions": len(total_times),
        "evaluation_rows": len(evaluation_rows),
        "retrieval_failures": retrieval_failures,
        "rerank_fallbacks": rerank_fallbacks,
        "top_k": TOP_K,
        "average_retrieval_latency_seconds": average(retrieval_times),
        "average_reranking_latency_seconds": average(reranking_times),
        "average_total_latency_seconds": average(total_times),
        "maximum_total_latency_seconds": max(total_times),
        "minimum_total_latency_seconds": min(total_times),
    }

    latency_path = OUTPUT_DIR / "rag_latency.json"

    latency_path.write_text(
        json.dumps(latency_report, indent=4),
        encoding="utf-8",
    )

    # ----------------------------------------------
    # 8. AGGREGATE METRIC SUMMARY
    # ----------------------------------------------

    metric_columns = [
        "context_precision_with_reference",
        "context_recall",
    ]

    summary = {}

    for method in scores["method"].unique():

        method_scores = scores[
            scores["method"] == method
        ]

        summary[method] = {}

        for metric in metric_columns:

            if metric in method_scores.columns:
                values = method_scores[metric]

                summary[method][metric] = (
                    float(values.mean())
                    if values.notna().any()
                    else None
                )

    summary_path = OUTPUT_DIR / "rag_evaluation_summary.json"

    summary_path.write_text(
        json.dumps(summary, indent=4),
        encoding="utf-8",
    )

    # ----------------------------------------------
    # 9. DISPLAY RESULTS
    # ----------------------------------------------

    print("\n========== RAGAS RESULTS ==========\n")
    print(scores.to_string(index=False))

    print("\n========== COMPARISON SUMMARY ==========\n")
    print(json.dumps(summary, indent=4))

    print("\n========== LATENCY REPORT ==========\n")
    print(json.dumps(latency_report, indent=4))

    print("\n========== GENERATED REPORTS ==========")
    print(f"Evaluation CSV: {report_path}")
    print(f"Latency JSON: {latency_path}")
    print(f"Summary JSON: {summary_path}")

    print("\nRAG evaluation completed.")


if __name__ == "__main__":
    main()
