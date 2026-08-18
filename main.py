from fastapi import FastAPI
from src.api.v1.routes.upload_route import router as upload_router
from src.api.v1.routes.query_route import router as query_router

app = FastAPI(title="Credit Card Spend Summarizer")


@app.get("/")
def root():
    return {"message": "Credit Card Spend Summarizer API is running"}


app.include_router(upload_router)
app.include_router(query_router)

#uv run uvicorn main:app --reload
#uv run streamlit run src/streamlit/app.py


##uv add fastapi uvicorn streamlit python-multipart python-dotenv pydantic pydantic-settings langchain langchain-core langchain-community langchain-openai langchain-postgres langgraph openai psycopg[binary] pgvector sqlalchemy cohere docling pypdf tiktoken
# uv add presidio-analyzer presidio-anonymizer transformers torch
