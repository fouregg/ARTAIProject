from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.schemas import LegalBundleOut, LegalDocumentOut
from app.services import legal

router = APIRouter(prefix="/api/legal", tags=["legal"])


@router.get("", response_model=LegalBundleOut)
async def get_legal_bundle() -> LegalBundleOut:
    """Всё, что терминал показывает до акцепта, одним запросом."""
    return LegalBundleOut(
        documents=[
            LegalDocumentOut(
                key=document.key,
                title=document.title,
                version=document.version,
                sha256=document.sha256,
                text=document.text,
            )
            for document in legal.documents()
        ],
        policy_url=legal.POLICY_URL,
        checkbox_agreement=legal.CHECKBOX_AGREEMENT,
        checkbox_consent=legal.CHECKBOX_CONSENT,
        age_notice=legal.AGE_NOTICE,
        ai_disclosure=legal.AI_DISCLOSURE,
        rejection_notice=legal.REJECTION_NOTICE,
    )


@router.get("/policy.pdf")
async def get_policy() -> FileResponse:
    """Политика обработки ПДН: 32 страницы, отдаём файлом для просмотра в браузере."""
    if not legal.POLICY_FILE.is_file():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="Файл политики обработки персональных данных не найден на сервере.",
        )

    return FileResponse(
        legal.POLICY_FILE,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="privacy-policy.pdf"'},
    )
