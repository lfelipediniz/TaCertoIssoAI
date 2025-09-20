"""
Fact-Checking Pipeline - Main Entry Point

This module orchestrates the complete 4-step fact-checking pipeline:
1. User Input Processing
2. Claim Extraction
3. Evidence Retrieval  
4. LLM Adjudication

Follows LangChain best practices with structured inputs/outputs and async processing.
"""

import time
from typing import Optional

from app.models.schemas import TextRequest, AnalysisResponse
from app.models.factchecking import UserInput, ClaimExtractionResult
from app.ai.claim_extractor import create_claim_extractor


async def process_text_request(request: TextRequest) -> AnalysisResponse:
    """
    Main pipeline entry point for text-only fact-checking.
    
    Args:
        request: TextRequest containing the text to fact-check
        
    Returns:
        AnalysisResponse with fact-check results
    """
    start_time = time.time()
    
    try:
        # Step 1: Convert API request to UserInput
        user_input = UserInput(
            text=request.text,
            locale="pt-BR",  # Default to Portuguese
            timestamp=None,
            context=None
        )
        
        # Step 2: Extract claims
        claim_extractor = create_claim_extractor()
        claims_result: ClaimExtractionResult = await claim_extractor.extract_claims(user_input)
        
        # For now, just return the claims extraction results
        # TODO: Add steps 3 (Evidence Retrieval) and 4 (Adjudication)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Temporary response showing claim extraction results
        claims_summary = [claim.text for claim in claims_result.claims]
        notes = claims_result.processing_notes or "No processing notes"
        
        return AnalysisResponse(
            message_id=f"test_{hash(request.text)}",
            verdict="unverifiable",  # Temporary
            rationale=f"Extracted {len(claims_result.claims)} claims: {claims_summary}. Notes: {notes}. Pipeline under development.",
            citations=[],  # Empty for now
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        
        # Return error response
        return AnalysisResponse(
            message_id=f"error_{hash(request.text)}",
            verdict="unverifiable",
            rationale=f"Error during processing: {str(e)}",
            citations=[],
            processing_time_ms=processing_time
        )
