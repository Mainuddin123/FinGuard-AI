
from src.database.db import get_connection
from src.workflow.graph import (
    run_investigation,
    resume_investigation,
)


def main():
    with get_connection() as conn:
        row = conn.execute("""
            SELECT id
            FROM transactions
            WHERE transaction_type = 'TRANSFER'
            ORDER BY id
            LIMIT 1
        """).fetchone()

    if row is None:
        print("No TRANSFER transaction found.")
        return

    transaction_id = row["id"]
    thread_id = f"finguard-test-{transaction_id}"

    print(f"\nTransaction ID: {transaction_id}")
    print("Starting investigation...\n")

    result = run_investigation(
        transaction_id=transaction_id,
        thread_id=thread_id,
    )

    if "__interrupt__" in result:
        print("\n========== HUMAN REVIEW ==========")

        for item in result["__interrupt__"]:
            print(item.value)

        decision = input(
            "\nEnter APPROVED, REJECTED, or ESCALATED: "
        ).strip().upper()

        if decision not in {"APPROVED", "REJECTED", "ESCALATED"}:
            print("Invalid decision. Investigation remains paused.")
            return

        print("\nResuming workflow...")

        result = resume_investigation(
            thread_id=thread_id,
            decision=decision,
        )

    print("\n========== FINAL RESULT ==========")
    print("Transaction ID:", result.get("transaction_id"))
    print("Risk analysis:", result.get("risk_analysis"))
    print("Case result:", result.get("case_result"))
    print("Human decision:", result.get("human_decision"))

    print("\n========== INVESTIGATION REPORT ==========")
    print(result.get("report", "No report generated."))

    if result.get("error"):
        print("\nWorkflow warning:", result["error"])

    print("\nWorkflow completed.")


if __name__ == "__main__":
    main()
