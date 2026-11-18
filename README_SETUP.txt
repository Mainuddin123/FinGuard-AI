Copy the included src/api folder into your existing FinGuard AI project.

Run from the project root with the virtual environment activated:
    uvicorn src.api.main:app --reload

Open:
    http://127.0.0.1:8000/docs

Flow:
1. POST /api/v1/investigations with {"transaction_id": 1}
2. Save the returned thread_id if human review is required.
3. POST /api/v1/investigations/decision with
   {"thread_id": "<returned-thread-id>", "decision": "APPROVED"}
4. GET /api/v1/cases/{case_id}

This assumes src.workflow.graph exports run_investigation and
resume_investigation. It is for local development; add authentication,
authorization, rate limiting, and persistent checkpoint storage before
public deployment.
