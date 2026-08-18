from src.agents.rag_agent import llm


def generate_sql(question: str):

    prompt = f"""
You are a PostgreSQL SQL expert.

Generate only SQL.
Do not provide explanation.

Database schema:

Table: customers

Columns:
- customer_id (varchar) PRIMARY KEY
- full_name (varchar)
- email (varchar)
- mobile (varchar)
- dob (date)
- kyc_status (varchar)
- created_at (timestamp)


Table: credit_cards

Columns:
- card_id (varchar) PRIMARY KEY
- customer_id (varchar)
- card_variant (varchar)
- credit_limit (numeric)
- available_limit (numeric)
- cash_limit (numeric)
- outstanding_amt (numeric)
- statement_date (integer)
- due_date (integer)
- min_due (numeric)
- reward_points (integer)
- status (varchar)
- issued_date (date)
- created_at (timestamp)


Table: card_transactions

Columns:
- txn_id (uuid) PRIMARY KEY
- card_id (varchar)
- txn_date (date)
- posting_date (date)
- txn_type (varchar)
- amount (numeric)
- original_currency (varchar)
- original_amount (numeric)
- merchant_name (varchar)
- category_code (varchar)
- category_name (varchar)
- is_international (boolean)
- is_emi (boolean)
- emi_months (integer)
- reward_pts_earned (integer)
- status (varchar)
- created_at (timestamp)


Table: billing_statements

Columns:
- statement_id (uuid) PRIMARY KEY
- card_id (varchar)
- billing_month (varchar)
- start_date (date)
- end_date (date)
- due_date (date)
- opening_balance (numeric)
- total_purchases (numeric)
- total_payments (numeric)
- total_fees (numeric)
- total_refunds (numeric)
- closing_balance (numeric)
- min_amount_due (numeric)
- reward_pts_earned (integer)
- generated_at (timestamp)


Table: reward_transactions

Columns:
- reward_txn_id (uuid) PRIMARY KEY
- card_id (varchar)
- txn_date (date)
- points_earned (integer)
- points_redeemed (integer)
- points_expired (integer)
- description (varchar)
- expiry_date (date)
- created_at (timestamp)


Rules:
- Generate only PostgreSQL SELECT queries.
- Use JOINs when information is required from multiple tables.
- Do not modify, insert, update, or delete data.
- Use txn_date for transaction date filtering.
- Use billing_month for statement based queries.


User question:
{question}

Generate SQL:
"""

    response = llm.invoke(prompt)

    sql_query = response.content

    sql_query = sql_query.replace("```sql", "")
    sql_query = sql_query.replace("```", "")

    return sql_query.strip()
