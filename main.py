from fastapi import FastAPI
from src.api.v1.routes.upload_route import router as upload_router
from src.api.v1.routes.query_route import router as query_router

app = FastAPI(title="Credit Card Spend Summarizer")


@app.get("/")
def root():
    return {"message": "Credit Card Spend Summarizer API is running"}


app.include_router(upload_router)
app.include_router(query_router)
