
import math
from typing import Any


def analyze_transaction(
    transaction: dict[str, Any],
) -> dict[str, Any]:
    """
    Analyze a transaction using explainable, rule-based signals.

    This is a preliminary heuristic engine, not a trained
    fraud detection model or confirmed fraud classification.
    """

    required_fields = [
        "transactionType",
        "amount",
        "oldBalInitiator",
        "newBalInitiator",
        "oldBalRecipient",
        "newBalRecipient",
    ]

    # 1. Input validation
    if not isinstance(transaction, dict):
        raise TypeError("Transaction must be a dictionary.")

    missing_fields = [
        field
        for field in required_fields
        if field not in transaction
    ]

    if missing_fields:
        raise ValueError(
            f"Missing transaction fields: {missing_fields}"
        )

    transaction_type = str(
        transaction["transactionType"]
    ).strip().upper()

    if not transaction_type:
        raise ValueError("Transaction type cannot be empty.")

    # 2. Numeric conversion
    numeric_fields = {
        "amount": transaction["amount"],
        "oldBalInitiator": transaction["oldBalInitiator"],
        "newBalInitiator": transaction["newBalInitiator"],
        "oldBalRecipient": transaction["oldBalRecipient"],
        "newBalRecipient": transaction["newBalRecipient"],
    }

    values = {}

    for field, raw_value in numeric_fields.items():
        if isinstance(raw_value, bool):
            raise ValueError(
                f"{field} must be numeric, not boolean."
            )

        try:
            values[field] = float(raw_value)
        except (TypeError, ValueError):
            raise ValueError(
                f"{field} must contain a valid numeric value."
            ) from None

    # 3. Reject NaN and infinity
    if not all(
        math.isfinite(value)
        for value in values.values()
    ):
        raise ValueError(
            "Transaction contains invalid numeric values."
        )

    amount = values["amount"]
    old_sender = values["oldBalInitiator"]
    new_sender = values["newBalInitiator"]
    old_recipient = values["oldBalRecipient"]
    new_recipient = values["newBalRecipient"]

    if amount < 0:
        raise ValueError(
            "Transaction amount cannot be negative."
        )

    # 4. Initialize investigation signals
    signals = []
    risk_score = 0

    # 5. Transaction type signal
    if transaction_type == "TRANSFER":
        risk_score += 25

        signals.append({
            "signal": "TRANSFER_TRANSACTION",
            "description": (
                "Transaction type is TRANSFER. "
                "This is a dataset-derived heuristic signal, "
                "not proof of suspicious activity."
            ),
            "points": 25,
        })

    # 6. Negative sender balance
    if new_sender < 0:
        risk_score += 15

        signals.append({
            "signal": "NEGATIVE_SENDER_BALANCE",
            "description": (
                "The sender's updated balance is negative."
            ),
            "points": 15,
        })

    # 7. Sender balance did not decrease
    if amount > 0 and new_sender >= old_sender:
        risk_score += 20

        signals.append({
            "signal": "UNEXPECTED_SENDER_BALANCE",
            "description": (
                "The sender's balance did not decrease "
                "despite a positive transaction amount."
            ),
            "points": 20,
        })

    # 8. Recipient balance did not increase
    if amount > 0 and new_recipient <= old_recipient:
        risk_score += 10

        signals.append({
            "signal": "UNEXPECTED_RECIPIENT_BALANCE",
            "description": (
                "The recipient's balance did not increase "
                "despite a positive transaction amount."
            ),
            "points": 10,
        })

    # 9. Cap risk score
    risk_score = min(risk_score, 100)

    # 10. Risk categorization
    if risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # 11. Investigation result
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "signals": signals,
        "requires_review": risk_level != "LOW",
        "decision": (
            "REQUIRES_INVESTIGATION"
            if risk_level != "LOW"
            else "NO_RULE_TRIGGERED"
        ),
        "disclaimer": (
            "Preliminary heuristic assessment based on "
            "configured rules. Not a confirmed fraud "
            "classification or probability."
        ),
    }
