import streamlit as st
import requests

st.title("Credit Card Spend Summarizer")

if st.button("Run Ingestion"):

    response = requests.post(
        "http://localhost:8000/api/v1/ingest"
    )

    st.json(response.json())
