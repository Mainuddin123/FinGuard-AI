from langgraph.graph import StateGraph, START, END
import sqlite3
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from src.workflow.state import InvestigationState
from src.workflow.nodes import (
    investigate_node,
    retrieve_policy_node,
    decision_node,
    create_case_node,
    human_review_node,
    generate_report_node,
    record_decision_node,
)


ALLOWED_DECISIONS = {"APPROVED", "REJECTED", "ESCALATED"}


def route_after_investigation(state):
    if state.get("error") and not state.get("risk_analysis"):
        return "report"

    return "retrieve_policy"


def route_after_decision(state):
    if state.get("requires_review", True):
        return "create_case"

    return "report"


builder = StateGraph(InvestigationState)

builder.add_node("investigate", investigate_node)
builder.add_node("retrieve_policy", retrieve_policy_node)
builder.add_node("decision", decision_node)
builder.add_node("create_case", create_case_node)
builder.add_node("human_review", human_review_node)
builder.add_node("generate_report", generate_report_node)
builder.add_node("record_decision", record_decision_node)

builder.add_edge(START, "investigate")

builder.add_conditional_edges(
    "investigate",
    route_after_investigation,
    {
        "retrieve_policy": "retrieve_policy",
        "report": "generate_report",
    },
)

builder.add_edge("retrieve_policy", "decision")

builder.add_conditional_edges(
    "decision",
    route_after_decision,
    {
        "create_case": "create_case",
        "report": "generate_report",
    },
)

builder.add_edge("create_case", "human_review")
builder.add_edge("human_review", "generate_report")
builder.add_edge("generate_report", "record_decision")
builder.add_edge("record_decision", END)

# Persistent SQLite checkpoint storage
PROJECT_ROOT = Path(__file__).resolve().parents[2]

CHECKPOINT_DB_PATH = (
    PROJECT_ROOT / "data" / "finguard_checkpoints.sqlite"
)

CHECKPOINT_DB_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

checkpoint_connection = sqlite3.connect(
    str(CHECKPOINT_DB_PATH),
    check_same_thread=False
)

checkpointer = SqliteSaver(checkpoint_connection)

workflow = builder.compile(checkpointer=checkpointer)

def run_investigation(transaction_id: int, thread_id: str):
    if transaction_id <= 0:
        raise ValueError("transaction_id must be positive.")

    if not thread_id or not thread_id.strip():
        raise ValueError("thread_id is required.")

    config = {
        "configurable": {
            "thread_id": thread_id.strip()
        }
    }

    return workflow.invoke(
        {"transaction_id": transaction_id},
        config=config,
    )


def resume_investigation(thread_id: str, decision: str):
    if not thread_id or not thread_id.strip():
        raise ValueError("thread_id is required.")

    decision = decision.strip().upper()

    if decision not in ALLOWED_DECISIONS:
        raise ValueError(
            "Decision must be APPROVED, REJECTED, or ESCALATED."
        )

    config = {
        "configurable": {
            "thread_id": thread_id.strip()
        }
    }

    return workflow.invoke(
        Command(resume={"decision": decision}),
        config=config,
    )


def get_investigation_status(thread_id: str):
    if not thread_id or not thread_id.strip():
        raise ValueError("thread_id is required.")

    config = {
        "configurable": {
            "thread_id": thread_id.strip()
        }
    }

    snapshot = workflow.get_state(config)

    return {
        "thread_id": thread_id,
        "values": snapshot.values,
        "next": list(snapshot.next),
        "is_interrupted": bool(snapshot.tasks)
        and any(
            getattr(task, "interrupts", ())
            for task in snapshot.tasks
        ),
    }