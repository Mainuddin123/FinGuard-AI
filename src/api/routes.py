
import logging
import uuid

from fastapi import APIRouter, HTTPException, Path

from src.api.schemas import (
    InvestigationRequest,
    HumanDecisionRequest,
    InvestigationResponse,
)
from src.database.db import (
    get_investigation_case,
    get_transaction,
)
from src.workflow.graph import (
    run_investigation,
    resume_investigation,
    get_investigation_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["FinGuard AI"],
)


def _build_response(
    thread_id: str,
    snapshot: dict,
) -> InvestigationResponse:

    if not isinstance(snapshot, dict):
        raise HTTPException(
            status_code=500,
            detail="Invalid investigation checkpoint.",
        )

    values = snapshot.get("values", {})

    transaction_id = values.get("transaction_id")

    if transaction_id is None:
        raise HTTPException(
            status_code=500,
            detail="Investigation checkpoint has no transaction ID.",
        )

    waiting = bool(snapshot.get("is_interrupted", False))
    error = values.get("error") or None

    if waiting:
        status = "PENDING_HUMAN_REVIEW"
    elif error:
        status = "FAILED"
    else:
        status = "COMPLETED"

    return InvestigationResponse(
        thread_id=thread_id,
        status=status,
        transaction_id=transaction_id,
        risk_analysis=values.get("risk_analysis"),
        case_id=values.get("case_id"),
        human_review_required=waiting,
        report=values.get("report"),
        error=error,
    )


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "FinGuard AI",
    }


@router.post(
    "/investigations",
    response_model=InvestigationResponse,
)
def start_investigation(request: InvestigationRequest):

    transaction = get_transaction(request.transaction_id)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found.",
        )

    thread_id = str(uuid.uuid4())

    try:
        run_investigation(
            request.transaction_id,
            thread_id,
        )

        snapshot = get_investigation_status(thread_id)

        return _build_response(thread_id, snapshot)

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Investigation workflow failed.")

        raise HTTPException(
            status_code=500,
            detail="Investigation workflow failed.",
        ) from exc


@router.get(
    "/investigations/{thread_id}",
    response_model=InvestigationResponse,
)
def get_investigation(thread_id: str):

    if not thread_id.strip():
        raise HTTPException(
            status_code=400,
            detail="Thread ID cannot be empty.",
        )

    try:
        snapshot = get_investigation_status(thread_id)
        values = snapshot.get("values", {})

        if not values or values.get("transaction_id") is None:
            raise HTTPException(
                status_code=404,
                detail="Investigation thread not found.",
            )

        return _build_response(thread_id, snapshot)

    except HTTPException:
        raise

    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=404,
            detail="Investigation thread not found.",
        ) from exc

    except Exception as exc:
        logger.exception("Could not retrieve investigation.")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve investigation.",
        ) from exc


@router.post(
    "/investigations/decision",
    response_model=InvestigationResponse,
)
def submit_human_decision(request: HumanDecisionRequest):

    try:
        current_snapshot = get_investigation_status(
            request.thread_id
        )

        current_values = current_snapshot.get("values", {})

        if (
            not current_values
            or current_values.get("transaction_id") is None
        ):
            raise HTTPException(
                status_code=404,
                detail="Investigation thread not found.",
            )

        if not current_snapshot.get("is_interrupted", False):
            raise HTTPException(
                status_code=409,
                detail="Investigation is not waiting for human review.",
            )

        resume_investigation(
            request.thread_id,
            request.decision,
        )

        updated_snapshot = get_investigation_status(
            request.thread_id
        )

        if updated_snapshot.get("is_interrupted", False):
            raise HTTPException(
                status_code=409,
                detail="Workflow is still waiting for human review.",
            )

        return _build_response(
            request.thread_id,
            updated_snapshot,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Could not resume investigation.")

        raise HTTPException(
            status_code=500,
            detail="Could not resume investigation.",
        ) from exc


@router.get("/cases/{case_id}")
def get_case(
    case_id: int = Path(gt=0),
):

    try:
        case = get_investigation_case(case_id)

        if case is None:
            raise HTTPException(
                status_code=404,
                detail="Investigation case not found.",
            )

        return case

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Could not retrieve investigation case.")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve investigation case.",
        ) from exc


@router.get("/transactions/{transaction_id}")
def get_transaction_by_id(
    transaction_id: int = Path(gt=0),
):

    try:
        transaction = get_transaction(transaction_id)

        if transaction is None:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found.",
            )

        return transaction

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Could not retrieve transaction.")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve transaction.",
        ) from exc
