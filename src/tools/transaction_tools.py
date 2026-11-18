from langchain_core.tools import tool

from src.database.db import get_transaction
from src.risk.engine import analyze_transaction


@tool
def investigate_transaction(transaction_id: int) -> dict:
    """Retrieve a stored transaction and analyze its risk."""

    if transaction_id <= 0:
        return {
            "success": False,
            "error": "Transaction ID must be positive."
        }

    transaction = get_transaction(transaction_id)

    if transaction is None:
        return {
            "success": False,
            "error": f"Transaction {transaction_id} not found."
        }

    # Map database fields to risk engine fields
    risk_input = {
        "step": transaction["step"],
        "transactionType": transaction["transaction_type"],
        "amount": transaction["amount"],
        "initiator": transaction["initiator"],
        "oldBalInitiator": transaction["old_balance_initiator"],
        "newBalInitiator": transaction["new_balance_initiator"],
        "recipient": transaction["recipient"],
        "oldBalRecipient": transaction["old_balance_recipient"],
        "newBalRecipient": transaction["new_balance_recipient"],
    }

    risk_result = analyze_transaction(risk_input)

    return {
        "success": True,
        "transaction_id": transaction_id,
        "transaction": risk_input,
        "risk_analysis": risk_result,
    }