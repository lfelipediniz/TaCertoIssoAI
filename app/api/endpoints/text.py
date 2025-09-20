from fastapi import APIRouter, HTTPException
from app.models.schemas import TextRequest, AnalysisResponse
from app.ai.pipeline import process_text_request

router = APIRouter()


@router.post("/text", response_model=AnalysisResponse)
async def analyze_text(request: TextRequest) -> AnalysisResponse:
    """
    Analyze text-only messages for fact-checking
    """
    try:
        return await process_text_request(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")