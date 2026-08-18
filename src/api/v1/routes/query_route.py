from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.api.v1.services.query_service import (
    process_query,
    process_query_stream,
)
from src.core.guardrails import GuardrailViolation, guard_input

router = APIRouter(
    prefix="/api/v1/spend-summary",
    tags=["Spend Summary"],
)


@router.post("/")
def query(request: dict):
    """
    Normal non-streaming query.

    Endpoint:
    POST /api/v1/spend-summary/
    """

    try:
        # input guardrail before LangGraph execution
        guard_input(request["question"])

        response = process_query(request)

    except GuardrailViolation as violation:
        raise HTTPException(
            status_code=400,
            detail={
                "guardrail": violation.guard,
                "message": violation.message,
            },
        )

    return response



@router.post("/stream")
async def query_stream(request: dict):
    """
    Streaming query.

    Endpoint:
    POST /api/v1/spend-summary/stream
    """

    return StreamingResponse(
        process_query_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )