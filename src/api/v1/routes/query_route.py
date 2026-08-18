from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.api.v1.services.query_service import (
    process_query,
    process_query_stream,
)


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

    return process_query(request)



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