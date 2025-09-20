from fastapi import APIRouter, HTTPException, File, UploadFile
from app.models.schemas import ImageRequest, AnalysisResponse

router = APIRouter()


@router.post("/images")
async def analyze_image(
    chatId: str = None,
    file: UploadFile = File(...)
):
    """
    Analyze image-only messages for fact-checking (with OCR)
    """
    # TODO: Implement image analysis logic
    raise HTTPException(status_code=501, detail="Not implemented yet")