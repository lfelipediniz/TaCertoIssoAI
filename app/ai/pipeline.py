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
from app.models.factchecking import (
    UserInput, 
    ClaimExtractionResult, 
    ExtractedClaim,
    AdjudicationInput,
    ClaimEvidence,
    Citation
)
from app.ai.claim_extractor import create_claim_extractor
from app.ai.adjudicator import adjudicate_claims


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


async def test_adjudicator() -> dict:
    """
    Test function for the adjudicator with hard-coded realistic input.
    
    Returns:
        Dict with test results and timing information
    """
    start_time = time.time()
    
    # Create realistic extracted claims
    claims = [
        ExtractedClaim(
            text="Vacinas causam autismo",
            links=[],
            llm_comment="Alegação médica sobre efeitos adversos de vacinas que requer verificação científica",
            entities=["vacinas", "autismo"]
        ),
        ExtractedClaim(
            text="Pessoas com olhos azuis são mais inteligentes",
            links=[],
            llm_comment="Alegação sobre características físicas e inteligência que pode ser verificada com estudos científicos",
            entities=["olhos azuis", "inteligência"]
        )
    ]
    
    # Create realistic evidence with citations
    evidence_map = {
        "Vacinas causam autismo": ClaimEvidence(
            claim_text="Vacinas causam autismo",
            citations=[
                Citation(
                    url="https://www.cdc.gov/vaccinesafety/concerns/autism.html",
                    title="Vaccines Do Not Cause Autism",
                    publisher="Centers for Disease Control and Prevention",
                    quoted="Multiple studies have found no link between vaccines and autism spectrum disorders."
                ),
                Citation(
                    url="https://www.who.int/news-room/feature-stories/detail/autism-spectrum-disorders",
                    title="Autism spectrum disorders",
                    publisher="World Health Organization",
                    quoted="There is no evidence of a causal association between measles, mumps and rubella vaccine and autism."
                ),
                Citation(
                    url="https://pediatrics.aappublications.org/content/113/2/259",
                    title="Age at first measles-mumps-rubella vaccination in children with autism",
                    publisher="American Academy of Pediatrics",
                    quoted="No significant association was found between the timing of MMR vaccination and the onset of autistic symptoms."
                )
            ],
            search_queries=["vaccines autism link", "MMR autism studies", "vaccine safety autism"],
            retrieval_notes="Encontradas múltiplas fontes autoritativas contradizendo a alegação"
        ),
        "Pessoas com olhos azuis são mais inteligentes": ClaimEvidence(
            claim_text="Pessoas com olhos azuis são mais inteligentes",
            citations=[
                Citation(
                    url="https://www.nature.com/articles/s41562-018-0362-x",
                    title="No association between eye color and intelligence",
                    publisher="Nature Human Behaviour",
                    quoted="Large-scale genetic studies show no causal relationship between eye pigmentation and cognitive ability."
                ),
                Citation(
                    url="https://psycnet.apa.org/record/2007-10421-003",
                    title="Intelligence and physical attractiveness",
                    publisher="American Psychological Association",
                    quoted="Eye color shows no significant correlation with measured IQ in controlled studies."
                )
            ],
            search_queries=["eye color intelligence correlation", "blue eyes IQ studies"],
            retrieval_notes="Estudos científicos não encontram correlação entre cor dos olhos e inteligência"
        )
    }
    
    # Create adjudication input
    adjudication_input = AdjudicationInput(
        original_user_text="vacina causa autismo e pessoas com olhos azuis sao mais inteligente",
        claims=claims,
        evidence_map=evidence_map,
        additional_context="Teste do sistema de adjudicação com alegações comuns"
    )
    
    try:
        # Test the adjudicator
        result = await adjudicate_claims(adjudication_input)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "original_query": result.original_query,
            "overall_verdict": result.overall_verdict,
            "rationale": result.rationale,
            "citations_count": len(result.supporting_citations),
            "citations": [{"title": c.title, "publisher": c.publisher, "url": c.url, "quoted": c.quoted} for c in result.supporting_citations],
            "processing_time_ms": processing_time,
            "error": None
        }
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "processing_time_ms": processing_time,
            "full_error": repr(e)
        }
