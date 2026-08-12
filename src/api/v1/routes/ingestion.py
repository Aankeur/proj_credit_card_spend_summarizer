from fastapi import APIRouter
from src.api.v1.services.ingestion_service import run_ingestion

router = APIRouter(prefix="/api/v1", tags=["ingestion"])

@router.post("/ingest")
def ingest():
    return run_ingestion()
