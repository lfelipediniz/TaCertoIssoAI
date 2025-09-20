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
from app.ai.factchecking.evidence_retrieval import retrieve_evidence_from_enriched
from app.ai.factchecking.link_enricher import create_link_enricher


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


async def test_full_pipeline_steps_1_3_4() -> dict:
    """
    Test the complete pipeline: Claim Extraction -> Evidence Retrieval -> Adjudication
    This will show what the adjudicator LLM actually returns when given real Google API evidence.
    Saves output of each step to timestamped files.
    
    Returns:
        Dict with results from all 3 steps
    """
    import time
    import json
    import os
    from datetime import datetime
    from app.models.factchecking import ClaimExtractionResult, UserInput, AdjudicationInput
    from app.ai.claim_extractor import create_claim_extractor
    
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get the project root directory (where this script is located)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))  # Go up two levels from app/ai/
    output_dir = os.path.join(project_root, "testoutput")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Step 1: Claim Extraction with real input (including URLs)
        user_input = UserInput(
            text="Flavio bolsonaro amo o PT segundo esse link: https://noticias.uol.com.br/politica/ultimas-noticias/2025/09/20/flavio-bolsonaro-defende-anistia-pec-da-blindagem-de-pec-da-sobrevivencia.htm e as vacinas causam autismo segundo esse link https://familia.sbim.org.br/duvidas/mitos/o-mercurio-presente-nas-vacinas-causa-autismo",
            locale="pt-BR"
        )
        
        claim_extractor = create_claim_extractor()
        claims_result = await claim_extractor.extract_claims(user_input)
        
        # Save Step 1 output
        step1_output = {
            "timestamp": timestamp,
            "step": "1_claim_extraction",
            "input": user_input.dict(),
            "output": claims_result.dict(),
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
        
        with open(f"{output_dir}/step1_claims_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(step1_output, f, indent=2, ensure_ascii=False)
        
        # Step 2.5: Link Enrichment
        step25_start = time.time()
        link_enricher = create_link_enricher()
        enrichment_result = await link_enricher.enrich_links(claims_result)
        
        # Save Step 2.5 output
        step25_output = {
            "timestamp": timestamp,
            "step": "2.5_link_enrichment",
            "input": claims_result.dict(),
            "output": enrichment_result.dict(),
            "processing_time_ms": int((time.time() - step25_start) * 1000)
        }
        
        with open(f"{output_dir}/step25_link_enrichment_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(step25_output, f, indent=2, ensure_ascii=False)
        
        # Step 3: Evidence Retrieval with enriched claims
        step3_start = time.time()
        evidence_result = await retrieve_evidence_from_enriched(enrichment_result)
        
        # Save Step 3 output
        step3_output = {
            "timestamp": timestamp,
            "step": "3_evidence_retrieval",
            "input": enrichment_result.dict(),
            "output": evidence_result.dict(),
            "processing_time_ms": int((time.time() - step3_start) * 1000)
        }
        
        with open(f"{output_dir}/step3_evidence_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(step3_output, f, indent=2, ensure_ascii=False)
        
        # Step 4: Adjudication with enriched claims and evidence
        step4_start = time.time()
        adjudication_input = AdjudicationInput(
            original_user_text=user_input.text,
            enriched_claims=enrichment_result.enriched_claims,
            evidence_map=evidence_result.claim_evidence_map,
            additional_context="Pipeline completo: extração -> enriquecimento -> evidências -> adjudicação"
        )
        
        final_result = await adjudicate_claims(adjudication_input)
        
        # Save Step 4 output
        step4_output = {
            "timestamp": timestamp,
            "step": "4_adjudication",
            "input": adjudication_input.dict(),
            "output": final_result.dict(),
            "processing_time_ms": int((time.time() - step4_start) * 1000)
        }
        
        with open(f"{output_dir}/step4_adjudication_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(step4_output, f, indent=2, ensure_ascii=False)
        
        # Save complete pipeline summary
        total_processing_time = int((time.time() - start_time) * 1000)
        pipeline_summary = {
            "timestamp": timestamp,
            "complete_pipeline_summary": {
                "user_input": user_input.text,
                "step1_claims_extracted": len(claims_result.claims),
                "step25_links_processed": enrichment_result.total_links_processed,
                "step25_successful_extractions": enrichment_result.successful_extractions,
                "step3_total_sources": evidence_result.total_sources_found,
                "step4_final_verdict": final_result.overall_verdict,
                "step4_rationale": final_result.rationale,
                "step4_citations_count": len(final_result.supporting_citations),
                "total_processing_time_ms": total_processing_time
            },
            "files_created": [
                f"step1_claims_{timestamp}.json",
                f"step25_link_enrichment_{timestamp}.json",
                f"step3_evidence_{timestamp}.json", 
                f"step4_adjudication_{timestamp}.json",
                f"pipeline_summary_{timestamp}.json"
            ]
        }
        
        with open(f"{output_dir}/pipeline_summary_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(pipeline_summary, f, indent=2, ensure_ascii=False)
        
        # Return API response
        return {
            "success": True,
            "timestamp": timestamp,
            "files_saved": pipeline_summary["files_created"],
            "step1_claims": [{"text": c.text, "llm_comment": c.llm_comment} for c in claims_result.claims],
            "step3_evidence_summary": {
                "total_sources": evidence_result.total_sources_found,
                "claims_with_evidence": len(evidence_result.claim_evidence_map)
            },
            "step4_adjudication_result": {
                "original_query": final_result.original_query,
                "overall_verdict": final_result.overall_verdict,
                "rationale": final_result.rationale,
                "citations_count": len(final_result.supporting_citations),
                "citations": [
                    {
                        "title": c.title,
                        "publisher": c.publisher,
                        "url": c.url,
                        "quoted": c.quoted,
                        "rating": c.rating,
                        "review_date": c.review_date
                    } for c in final_result.supporting_citations
                ]
            },
            "processing_time_ms": total_processing_time,
            "error": None
        }
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        
        # Save error to file
        error_output = {
            "timestamp": timestamp,
            "step": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "processing_time_ms": processing_time
        }
        
        with open(f"{output_dir}/error_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(error_output, f, indent=2, ensure_ascii=False)
        
        return {
            "success": False,
            "timestamp": timestamp,
            "error": str(e),
            "error_type": type(e).__name__,
            "processing_time_ms": processing_time,
            "error_file": f"error_{timestamp}.json"
        }


async def test_evidence_retrieval() -> dict:
    """
    Test function for evidence retrieval (Step 3) with real claims
    
    Returns:
        Dict with test results and evidence found
    """
    import time
    from app.models.factchecking import ClaimExtractionResult
    
    start_time = time.time()
    
    # Create realistic extracted claims (same as adjudicator test)
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
    
    # Create ClaimExtractionResult
    claims_result = ClaimExtractionResult(
        original_text="vacina causa autismo e pessoas com olhos azuis sao mais inteligente",
        claims=claims,
        processing_notes="Teste do sistema de recuperação de evidências"
    )
    
    try:
        # Step 2.5: Link Enrichment first
        link_enricher = create_link_enricher()
        enrichment_result = await link_enricher.enrich_links(claims_result)
        
        # Test evidence retrieval with enriched claims
        evidence_result = await retrieve_evidence_from_enriched(enrichment_result)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Format response with full citation details
        evidence_summary = {}
        for claim_text, evidence in evidence_result.claim_evidence_map.items():
            evidence_summary[claim_text] = {
                "citations_found": len(evidence.citations),
                "publishers": [c.publisher for c in evidence.citations],
                "search_queries": evidence.search_queries,
                "retrieval_notes": evidence.retrieval_notes,
                "full_citations": [
                    {
                        "url": c.url,
                        "title": c.title,
                        "publisher": c.publisher,
                        "quoted": c.quoted,
                        "rating": c.rating,
                        "review_date": c.review_date
                    } for c in evidence.citations
                ]
            }
        
        return {
            "success": True,
            "total_sources_found": evidence_result.total_sources_found,
            "claims_processed": len(evidence_result.claim_evidence_map),
            "evidence_summary": evidence_summary,
            "processing_time_ms": processing_time,
            "error": None
        }
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "processing_time_ms": processing_time
        }
