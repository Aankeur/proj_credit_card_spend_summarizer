from src.agents.rag_agent import llm


def generate_sql(
    question: str,
    chat_history: list = None,
):

    history_text = ""

    if chat_history:
        for message in chat_history[-5:]:
            history_text += f"{message['role']}: " f"{message['content']}\n"

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

String matching rules:
- PostgreSQL string comparisons are case-sensitive.
- For varchar/text columns, always use ILIKE or LOWER() for comparisons.
- Do not assume the case of stored values.
- For fields like status, category_name, merchant_name, card_variant, and customer names, use case-insensitive matching.
- Do not use SQL parameters like $1, $2, etc.
- Use the provided customer context value directly in the query.

Date and value normalization rules:
- Understand user-provided dates/months in natural language and convert them to the format stored in the database.
- Use the schema information to determine the expected format of date-related fields.
- Examples:
  - "March 2026" can map to "2026-03" if the database stores month values in YYYY-MM format.
  - "1 March 2026" can map to "2026-03-01" or "01-03-2026" if the database stores full dates.
- Do not compare formatted user input directly if conversion is required.

When generating SQL:
- Only include filters for values that are required to answer the database portion of the question.
- Do not convert every named entity in the user question into a SQL WHERE condition.
- Distinguish between:
  1. Contextual product information used for explanation or knowledge lookup.
  2. Identifiers required to retrieve customer-specific records.
- If the question contains multiple entities, use only entities that map to the requested database information.


Never generate static text values.
Never create columns with hardcoded explanations.
Only select columns that exist in database schema.

Conversation history:
{history_text}

User question:
{question}

Generate SQL:
"""

    response = llm.invoke(prompt)

    sql_query = response.content

    sql_query = sql_query.replace("```sql", "")
    sql_query = sql_query.replace("```", "")

    return sql_query.strip()
