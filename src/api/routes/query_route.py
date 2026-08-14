from fastapi import APIRouter

from src.api.services.query_service import process_query

router = APIRouter(prefix="/api/v1/advisor")


@router.post("/")
def query(request: dict):
    return process_query(request)
