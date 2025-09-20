from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from typing import Optional
from app.models.schemas import MultimodalRequest, AnalysisResponse

router = APIRouter()


@router.post("/multimodal")
async def analyze_multimodal(
    chatId: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Analyze messages containing both text and images
    """
    # TODO: Implement multimodal analysis logic
    raise HTTPException(status_code=501, detail="Not implemented yet")