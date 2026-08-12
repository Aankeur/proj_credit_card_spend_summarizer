import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()


DATABASE_URL = os.getenv("PG_DATABASE_URL")


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


def get_db_conn():
    return SessionLocal()

## run this: 
# uv add fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv streamlit requests langchain_core langchain_openai docling