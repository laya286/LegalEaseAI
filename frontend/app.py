import os
import requests
import streamlit as st

from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000"
).rstrip("/")


st.set_page_config(
    page_title="LegalEase",
    page_icon="⚖️",
    layout="wide"
)


st.title("⚖️ LegalEase")

st.subheader(
    "AI-Powered Legal Document Generator"
)

st.info(
    "Create AI-assisted legal document drafts "
    "using Gemini."
)


st.divider()


document_type = st.selectbox(
    "Document Type",
    [
        "Employment Contract",
        "Lease Agreement",
        "Non-Disclosure Agreement",
        "Freelance Work Contract",
        "Service Agreement",
        "General Agreement",
        "Custom"
    ]
)


if document_type == "Custom":

    document_type = st.text_input(
        "Enter Document Type"
    )


parties = st.text_area(
    "Parties Involved",
    placeholder=(
        "Example: Jane Doe (Employee), "
        "ABC Company (Employer)"
    )
)


terms = st.text_area(
    "Terms & Conditions",
    placeholder=(
        "Example: Salary is paid monthly; "
        "Confidentiality must be maintained; "
        "Either party can terminate with 30 days notice."
    )
)


effective_date = st.text_input(
    "Effective Date",
    placeholder="2026-10-01"
)


if st.button(
    "✨ Generate Document",
    type="primary"
):

    if not all(
        [
            document_type.strip(),
            parties.strip(),
            terms.strip(),
            effective_date.strip()
        ]
    ):

        st.error(
            "Please fill in all fields."
        )

    else:

        payload = {
            "document_type": document_type,
            "parties": parties,
            "terms": terms,
            "effective_date": effective_date
        }

        try:

            with st.spinner(
                "Generating document..."
            ):

                response = requests.post(
                    f"{BACKEND_URL}/generate",
                    json=payload,
                    timeout=120
                )


            if response.status_code == 200:

                data = response.json()

                st.success(
                    "Document generated successfully!"
                )

                st.text_area(
                    "Generated Document",
                    value=data["content"],
                    height=600
                )

            else:

                st.error(
                    f"Backend Error: {response.text}"
                )

        except Exception as error:

            st.error(
                "Cannot connect to FastAPI backend."
            )

            st.code(
                str(error)
            )


st.divider()

st.caption(
    "LegalEase • FastAPI + Streamlit + Gemini"
)