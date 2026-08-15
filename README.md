# Credit Card Spend Summarizer

## Overview

The **Credit Card Spend Summarizer** is an AI-powered application that generates
customer-friendly credit card spend summaries for a given account and billing
month.

The application combines:

- PostgreSQL transactional data
- A document-based Knowledge Base
- Docling-based document extraction
- Text/table/image processing
- OpenAI embeddings
- PostgreSQL + pgvector for semantic retrieval
- FastAPI for backend APIs
- LLM-based reasoning and response generation

The Knowledge Base contains business rules related to credit card products,
spend categories, billing cycles, rewards, fees, credit limits, and customer
scenarios.

The objective is to combine **structured customer transaction data** with
**retrieved business knowledge** to generate accurate and contextualized
credit card spend summaries.

---

# Project Goal

Given a:

- Credit Card Account ID
- Billing Month

the application should:

1. Retrieve the customer's credit card and transaction information from
   PostgreSQL.
2. Retrieve relevant business rules from the Knowledge Base.
3. Perform semantic retrieval using vector embeddings.
4. Use the retrieved context together with the customer's transactional
   information.
5. Generate a meaningful spend summary using an LLM.

The generated response should be understandable to the customer while
following the business rules defined in the Knowledge Base.

