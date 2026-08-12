from fastapi import FastAPI

from src.api.v1.routes.ingestion import router as ingestion_router

app = FastAPI(title="Credit Card Spend Summarizer")

app.include_router(ingestion_router)

@app.get("/health")
def health():
    return {"status": "healthy"}
