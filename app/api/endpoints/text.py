from fastapi import APIRouter, HTTPException
from app.models.schemas import TextRequest, AnalysisResponse

router = APIRouter()


@router.post("/text")
async def analyze_text(request: TextRequest):
    """
    Analyze text-only messages for fact-checking
    """
    # TODO: Implement text analysis logic
    raise HTTPException(status_code=501, detail="Not implemented yet")