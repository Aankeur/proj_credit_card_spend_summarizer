from fastapi import APIRouter

from src.api.v1.services.query_service import process_query

router = APIRouter(prefix="/api/v1/spend-summary")


@router.post("/")
def query(request: dict):
    return process_query(request)
