from fastapi import APIRouter, HTTPException
from app.models.schemas import TextRequest, AnalysisResponse
from app.ai.pipeline import process_text_request, test_adjudicator, test_evidence_retrieval, test_full_pipeline_steps_1_3_4

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


@router.get("/test-adjudicator")
async def test_adjudicator_endpoint():
    """
    Test endpoint for the adjudicator with hard-coded realistic data
    """
    try:
        result = await test_adjudicator()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@router.get("/test-evidence-retrieval")
async def test_evidence_retrieval_endpoint():
    """
    Test endpoint for evidence retrieval (Step 3) using Google Fact-Check API
    """
    try:
        result = await test_evidence_retrieval()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence retrieval test error: {str(e)}")


@router.get("/test-full-pipeline")
async def test_full_pipeline_endpoint():
    """
    Test endpoint for complete pipeline: Claim Extraction -> Evidence Retrieval -> Adjudication
    This shows what the adjudicator LLM actually returns when given real Google API evidence.
    """
    try:
        result = await test_full_pipeline_steps_1_3_4()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full pipeline test error: {str(e)}")