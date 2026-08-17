import requests
import streamlit as st

# CONFIG

API_BASE_URL = "http://localhost:8000"
QUERY_ENDPOINT = f"{API_BASE_URL}/api/v1/spend-summary/"


# PAGE CONFIG

st.set_page_config(
    page_title="Credit Card Spend Assistant",
    page_icon="💳",
    layout="wide",
)


# CUSTOM CSS

st.markdown(
    """
    <style>

    /* Main page */
    .stApp {
        background: linear-gradient(
            180deg,
            #eef6ff 0%,
            #ffffff 45%,
            #ffffff 100%
        );
    }

    /* Remove default top padding */
    .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }

    /* Header */
    .app-title {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        color: #1f2937;
    }

    .app-subtitle {
        text-align: center;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }

    /* Search box container */
    .search-container {
        background: linear-gradient(
            90deg,
            #dbeafe,
            #bfdbfe
        );
        padding: 8px;
        border-radius: 18px;
        box-shadow: 0 5px 18px rgba(37, 99, 235, 0.20);
        margin-bottom: 1.5rem;
    }

    /* Suggestion section */
    .suggestion-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #374151;
        margin-top: 1rem;
        margin-bottom: 0.8rem;
    }

    /* Chat response */
    .assistant-card {
        background: white;
        border-radius: 14px;
        padding: 20px;
        margin: 10px 0 20px 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.06);
    }

    .assistant-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 10px;
    }

    /* Metric cards */
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .metric-label {
        font-size: 0.85rem;
        color: #6b7280;
    }

    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #111827;
    }

    /* Hide Streamlit menu/footer */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# SESSION STATE

if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_suggestions" not in st.session_state:
    st.session_state.show_suggestions = True


# HEADER

st.markdown(
    '<div class="app-title">💳 Credit Card Spend Assistant</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="app-subtitle">'
    "Your personal credit card spending assistant"
    "</div>",
    unsafe_allow_html=True,
)


# CARD CONTEXT

# col1, col2 = st.columns([1, 1])

# with col1:
#     card_id = st.selectbox(
#         "💳 Card",
#         [
#             "CC-881001 — NorthStar Gold",
#             "CC-882001 — NorthStar Platinum",
#             "CC-883001 — NorthStar Classic",
#         ],
#     )

# with col2:
#     billing_month = st.selectbox(
#         "📅 Billing Month",
#         [
#             "March 2026",
#             "February 2026",
#             "January 2026",
#         ],
#     )


card_id = ""
billing_month = ""

# SUGGESTED QUESTIONS

# if st.session_state.show_suggestions:

#     st.markdown(
#         '<div class="suggestion-title">📈 Suggested questions</div>',
#         unsafe_allow_html=True,
#     )

# col1, col2, col3, col4 = st.columns(4)

# with col1:
#     if st.button(
#         "📊 Monthly Spend",
#         use_container_width=True,
#     ):
#         st.session_state.selected_question = (
#             f"Summarise my spending for {billing_month} "
#             f"on card {card_id.split(' — ')[0]}"
#         )
#         st.session_state.show_suggestions = False
#         st.rerun()

# with col2:
#     if st.button(
#         "🏆 Top Category",
#         use_container_width=True,
#     ):
#         st.session_state.selected_question = (
#             "What did I spend the most on this month?"
#         )
#         st.session_state.show_suggestions = False
#         st.rerun()

# with col3:
#     if st.button(
#         "🌍 International Spend",
#         use_container_width=True,
#     ):
#         st.session_state.selected_question = (
#             "How much did I spend internationally this billing cycle?"
#         )
#         st.session_state.show_suggestions = False
#         st.rerun()

# with col4:
#     if st.button(
#         "🎁 Reward Points",
#         use_container_width=True,
#     ):
#         st.session_state.selected_question = (
#             "How many reward points did I earn this month?"
#         )
#         st.session_state.show_suggestions = False
#         st.rerun()

# col1, col2, col3, col4 = st.columns(4)

# with col1:
#     if st.button(
#         "📈 Compare Last Month",
#         use_container_width=True,
#     ):
#         st.session_state.selected_question = (
#             "Compare my spending this month with last month."
#         )
#         st.session_state.show_suggestions = False
#         st.rerun()

# with col2:
#     if st.button(
#         "💳 Fee Waiver",
#         use_container_width=True,
#     ):
#         st.session_state.selected_question = (
#             "Am I on track to meet my annual fee waiver threshold?"
#         )
#         st.session_state.show_suggestions = False
#         st.rerun()

# with col3:
#     if st.button(
#         "🛍️ Top Merchants",
#         use_container_width=True,
#     ):
#         st.session_state.selected_question = (
#             "Show me my top spending merchants this month."
#         )
#         st.session_state.show_suggestions = False
#         st.rerun()

# with col4:
#     if st.button(
#         "💰 Largest Purchase",
#         use_container_width=True,
#     ):
#         st.session_state.selected_question = (
#             "What was my largest purchase this month?"
#         )
#         st.session_state.show_suggestions = False
#         st.rerun()


# CHAT HISTORY

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# QUESTION INPUT

default_question = st.session_state.pop(
    "selected_question",
    None,
)

prompt = st.chat_input("What would you like to know about your spending?")


# If a suggestion was selected
if default_question:
    prompt = default_question


# PROCESS QUESTION

# PROCESS QUESTION

if prompt:

    card_number = card_id.split(" — ")[0]

    # Save user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    # Immediately show user message
    with st.chat_message("user"):
        st.markdown(prompt)

    try:

        payload = {
            "question": prompt,
        }

        response = requests.post(QUERY_ENDPOINT, json=payload, timeout=120)

        if response.status_code == 200:

            api_response = response.json()

            response_text = api_response.get("response", "No response received.")

        else:

            response_text = f"API Error: {response.status_code}"

    except requests.exceptions.ConnectionError:

        response_text = "Unable to connect to FastAPI backend."

    except requests.exceptions.Timeout:

        response_text = "Request timed out. Please try again."

    except Exception as exc:

        response_text = f"Error: {exc}"

    # Save assistant message
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_text,
        }
    )

    # Show assistant response
    with st.chat_message("assistant"):
        st.markdown(response_text)

    st.session_state.show_suggestions = True

    st.rerun()
    # st.session_state.messages.append(
    #     {
    #         "role": "assistant",
    #         "content": response_text,
    #     }
    # )

    # st.session_state.show_suggestions = True


# ADMIN / DEVELOPMENT SECTION

with st.expander("⚙️ Developer / Admin"):

    st.caption(
        "Knowledge Base ingestion is an administrative operation "
        "and is kept separate from the customer chat experience."
    )

    if st.button(
        "Run Knowledge Base Ingestion",
        type="secondary",
    ):

        try:

            response = requests.post(
                f"{API_BASE_URL}/api/v1/ingest",
                timeout=300,
            )

            if response.status_code == 200:

                st.success("Knowledge Base ingestion completed.")

                st.json(response.json())

            else:

                st.error(f"Ingestion failed: " f"{response.status_code}")

                st.text(response.text)

        except requests.exceptions.ConnectionError:

            st.error(
                "Could not connect to FastAPI. "
                "Start the backend with:\n\n"
                "uv run uvicorn src.main:app --reload"
            )

        except requests.exceptions.Timeout:

            st.error("Ingestion timed out.")

        except Exception as exc:

            st.error(f"Unexpected error: {exc}")
