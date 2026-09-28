import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()


# ---------------------------------------------------------
# LEGAL DOCUMENT INSTRUCTIONS
# ---------------------------------------------------------

SYSTEM_INSTRUCTIONS = """
You are LegalEase, an AI assistant that creates
professional legal document drafts.

IMPORTANT RULES:

1. Create a professional legal DOCUMENT DRAFT.
2. Do not invent facts that the user did not provide.
3. Do not invent names, addresses, dates, amounts,
   laws, courts or registration numbers.
4. If important information is missing, use a placeholder
   such as [ADDRESS TO BE ADDED].
5. Use professional and clear legal language.
6. Organize the document using:
   - Document title
   - Introduction
   - Numbered sections
   - Terms and conditions
   - Responsibilities
   - Termination
   - Governing law placeholder if needed
   - Signature section
7. Use the user's information exactly where appropriate.
8. Do not return Markdown code fences.
9. Do not say that the document is guaranteed to be
   legally valid everywhere.
10. Add this notice at the end:

Review Notice:
This AI-generated draft should be reviewed for applicable
local law before signing or use.
"""


class GeminiDocumentGenerator:

    def __init__(self):

        # -------------------------------------------------
        # API KEY
        # -------------------------------------------------

        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Please add your Gemini API key to the .env file."
            )

        # -------------------------------------------------
        # PRIMARY MODEL
        # -------------------------------------------------

        self.primary_model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash"
        )

        # -------------------------------------------------
        # FALLBACK MODELS
        # -------------------------------------------------

        self.fallback_models = [
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash"
        ]

        # Remove duplicate model names
        self.models = list(
            dict.fromkeys(
                [self.primary_model] + self.fallback_models
            )
        )

        # -------------------------------------------------
        # GEMINI CLIENT
        # -------------------------------------------------

        self.client = genai.Client(
            api_key=self.api_key
        )

        # This will contain the model that finally worked
        self.model = self.primary_model

    # -----------------------------------------------------
    # BUILD PROMPT
    # -----------------------------------------------------

    def build_prompt(
        self,
        document_type,
        parties,
        terms,
        effective_date
    ):

        prompt = f"""
{SYSTEM_INSTRUCTIONS}

Create a:

{document_type}

PARTIES:
{parties}

TERMS AND CONDITIONS:
{terms}

EFFECTIVE DATE:
{effective_date}

Generate the complete legal document draft.

Return only the document text.
"""

        return prompt

    # -----------------------------------------------------
    # CHECK WHETHER ERROR IS RETRYABLE
    # -----------------------------------------------------

    def is_retryable_error(self, error):

        error_text = str(error).upper()

        retryable_errors = [
            "503",
            "UNAVAILABLE",
            "429",
            "RESOURCE_EXHAUSTED",
            "500",
            "INTERNAL",
            "TIMEOUT",
            "DEADLINE"
        ]

        return any(
            item in error_text
            for item in retryable_errors
        )

    # -----------------------------------------------------
    # GENERATE DOCUMENT
    # -----------------------------------------------------

    def generate_document(
        self,
        document_type,
        parties,
        terms,
        effective_date
    ):

        prompt = self.build_prompt(
            document_type=document_type,
            parties=parties,
            terms=terms,
            effective_date=effective_date
        )

        last_error = None

        # -------------------------------------------------
        # TRY EACH MODEL
        # -------------------------------------------------

        for model_index, model_name in enumerate(self.models):

            # Try each model up to 3 times
            for attempt in range(3):

                try:

                    print(
                        f"Trying Gemini model: "
                        f"{model_name} "
                        f"(attempt {attempt + 1}/3)"
                    )

                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )

                    generated_text = getattr(
                        response,
                        "text",
                        None
                    )

                    if not generated_text:
                        raise RuntimeError(
                            "Gemini returned an empty response."
                        )

                    # -------------------------------------------------
                    # SUCCESS
                    # -------------------------------------------------

                    self.model = model_name

                    print(
                        f"Document generated successfully "
                        f"using {model_name}"
                    )

                    return generated_text.strip()

                except Exception as error:

                    last_error = error

                    print(
                        f"Gemini error with {model_name}: "
                        f"{error}"
                    )

                    # -------------------------------------------------
                    # NON-RETRYABLE ERROR
                    # -------------------------------------------------

                    if not self.is_retryable_error(error):

                        raise RuntimeError(
                            f"Gemini request failed: {error}"
                        )

                    # -------------------------------------------------
                    # EXPONENTIAL BACKOFF
                    # -------------------------------------------------

                    if attempt < 2:

                        wait_time = 2 ** attempt

                        print(
                            f"Retrying in "
                            f"{wait_time} seconds..."
                        )

                        time.sleep(wait_time)

            # -------------------------------------------------
            # MOVE TO NEXT FALLBACK MODEL
            # -------------------------------------------------

            if model_index < len(self.models) - 1:

                print(
                    f"{model_name} is temporarily unavailable. "
                    f"Trying fallback model..."
                )

                time.sleep(1)

        # -----------------------------------------------------
        # ALL MODELS FAILED
        # -----------------------------------------------------

        raise RuntimeError(
            "All Gemini models are temporarily unavailable. "
            f"Last error: {last_error}"
        )