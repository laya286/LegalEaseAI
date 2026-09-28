import os

from fastapi import APIRouter, HTTPException

from backend.schemas import (
    DocumentRequest,
    DocumentResponse
)

from backend.ai_core.gemini_generator import (
    GeminiDocumentGenerator
)


router = APIRouter(
    tags=["LegalEase"]
)


@router.get("/")
def root():
    return {
        "service": "LegalEase API",
        "status": "running",
        "message": "AI-powered legal document generator backend is running."
    }


@router.get("/health")
def health():
    return {
        "status": "ok",
        "gemini_configured": bool(
            os.getenv("GEMINI_API_KEY")
        ),
        "model": os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash"
        )
    }


@router.post(
    "/generate",
    response_model=DocumentResponse
)
def generate_document(
    request: DocumentRequest
):

    try:

        generator = GeminiDocumentGenerator()

        content = generator.generate_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            effective_date=request.effective_date
        )

        return DocumentResponse(
            document_type=request.document_type,
            content=content,
            model=generator.model
        )

    except RuntimeError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=502,
            detail=f"Document generation failed: {error}"
        )