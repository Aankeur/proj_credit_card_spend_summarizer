"""
Guardrails layer for Agentic RAG API.

Provides:

1. Input guard
   - Toxic language detection

2. Output guard
   - PII detection and masking
   - Customer ID masking


Public API:

    guard_input(query: str)
    guard_output(response: str)

    GuardrailViolation
"""

import os
import re

from dotenv import load_dotenv


load_dotenv(override=True)


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

PII_ENTITIES = [
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "PERSON",
    "CREDIT_CARD",
    "US_SSN",
    "IBAN_CODE",
    "IP_ADDRESS",
]


TOXICITY_THRESHOLD = float(
    os.getenv(
        "GUARDRAIL_TOXICITY_THRESHOLD",
        "0.5",
    )
)


CUSTOMER_ID_RE = re.compile(
    r"\b\d{6,}\b"
)


# -------------------------------------------------------------------
# Exception
# -------------------------------------------------------------------

class GuardrailViolation(Exception):
    """
    Raised when an input guard blocks a request.
    """

    def __init__(
        self,
        guard: str,
        message: str,
    ):

        self.guard = guard
        self.message = message

        super().__init__(
            f"[{guard}] {message}"
        )


# -------------------------------------------------------------------
# Lazy loaded objects
# -------------------------------------------------------------------

_analyzer = None
_anonymizer = None
_toxicity_pipeline = None



def _get_analyzer():

    global _analyzer

    if _analyzer is None:

        from presidio_analyzer import AnalyzerEngine

        _analyzer = AnalyzerEngine()

    return _analyzer



def _get_anonymizer():

    global _anonymizer

    if _anonymizer is None:

        from presidio_anonymizer import AnonymizerEngine

        _anonymizer = AnonymizerEngine()

    return _anonymizer



def _get_toxicity_pipeline():

    global _toxicity_pipeline

    if _toxicity_pipeline is None:

        from transformers import pipeline


        _toxicity_pipeline = pipeline(
            "text-classification",
            model="unitary/toxic-bert",
            top_k=None,
        )


    return _toxicity_pipeline



# -------------------------------------------------------------------
# Input guard
# -------------------------------------------------------------------

def guard_input(query: str) -> None:
    """
    Validate user query.

    Raises:
        GuardrailViolation
    """

    if not query:
        return


    try:

        classifier = _get_toxicity_pipeline()

        result = classifier(query)


        scores = result[0]


        for item in scores:

            label = item["label"].lower()
            score = item["score"]


            if (
                label == "toxic"
                and score >= TOXICITY_THRESHOLD
            ):

                raise GuardrailViolation(
                    "toxic_language",
                    "Your message was flagged as abusive or toxic and cannot be processed.",
                )


    except GuardrailViolation:
        raise


    except Exception as exc:

        # Do not break application if toxicity
        # model is unavailable

        print(
            "Toxicity guard error:",
            str(exc),
        )



# -------------------------------------------------------------------
# Output guard
# -------------------------------------------------------------------

def guard_output(response: str) -> str:
    """
    Remove PII from generated answer.

    Returns:
        cleaned response
    """

    if not response:
        return response


    # Mask customer/account IDs
    response = CUSTOMER_ID_RE.sub(
        "<CUSTOMER_ID>",
        response,
    )


    try:

        analyzer = _get_analyzer()


        results = analyzer.analyze(
            text=response,
            language="en",
            entities=PII_ENTITIES,
        )


        if not results:
            return response

        anonymizer = _get_anonymizer()

        anonymized = anonymizer.anonymize(
            text=response,
            analyzer_results=results,
        )

        return anonymized.text

    except Exception as exc:

        print(
            "PII guard error:",
            str(exc),
        )


        return response