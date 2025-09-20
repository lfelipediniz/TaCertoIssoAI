"""
Evidence Retrieval Module - Step 3 of Fact-Checking Pipeline

This module implements evidence retrieval using the Google Fact-Check Tools API.
Takes ClaimExtractionResult from Step 2 and retrieves fact-check evidence for each claim.

Outputs structured data models for Step 4 (Adjudication).
"""

import requests
from typing import List, Optional
import logging

from app.models.factchecking import (
    ClaimExtractionResult,
    ExtractedClaim,
    Citation,
    ClaimEvidence,
    EvidenceRetrievalResult
)
from app.core.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()


class GoogleFactCheckRetriever:
    """
    Retrieves fact-check evidence using Google Fact-Check Tools API
    """
    
    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY
        self.base_url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        
    async def search_claim(self, claim_text: str) -> List[Citation]:
        """
        Search for fact-check evidence for a single claim
        
        Args:
            claim_text: The claim to search for
            
        Returns:
            List of Citation objects from fact-checkers
        """
        if not self.api_key:
            logger.warning("Google API key not configured")
            return []
            
        try:
            # Build request URL
            url = f"{self.base_url}?query={claim_text}&key={self.api_key}"
            
            # Make API request
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Extract citations
            citations = []
            if 'claims' in data and data['claims']:
                for claim in data['claims']:
                    if 'claimReview' in claim and claim['claimReview']:
                        for review in claim['claimReview']:
                            citation = self._parse_claim_review(claim, review)
                            if citation:
                                citations.append(citation)
            
            logger.info(f"Found {len(citations)} fact-check results for claim: {claim_text[:50]}...")
            return citations
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing Google API response: {e}")
            return []
    
    def _parse_claim_review(self, claim: dict, review: dict) -> Optional[Citation]:
        """
        Parse a single claimReview into a Citation object
        
        Args:
            claim: The claim data from Google API
            review: The claimReview data from Google API
            
        Returns:
            Citation object or None if parsing fails
        """
        try:
            # Extract required fields
            url = review.get('url', '')
            title = review.get('title', f"Fact-check: {claim.get('text', 'Unknown claim')[:50]}...")
            publisher = review.get('publisher', {}).get('name', 'Unknown Publisher')
            rating = review.get('textualRating', 'Unknown')
            review_date = review.get('reviewDate')
            
            # Create quoted text with better formatting
            claim_text = claim.get('text', 'No claim text available')
            quoted = f"Fact-check verdict: {rating}. Original claim: {claim_text[:150]}..."
            
            return Citation(
                url=url,
                title=title,
                publisher=publisher,
                quoted=quoted,
                rating=rating,
                review_date=review_date
            )
            
        except Exception as e:
            logger.error(f"Error parsing claim review: {e}")
            return None


async def retrieve_evidence(claims_result: ClaimExtractionResult) -> EvidenceRetrievalResult:
    """
    Main evidence retrieval function for Step 3 of the pipeline
    
    Args:
        claims_result: Output from Step 2 (Claim Extraction)
        
    Returns:
        EvidenceRetrievalResult: Structured evidence for Step 4 (Adjudication)
    """
    retriever = GoogleFactCheckRetriever()
    evidence_map = {}
    total_sources_found = 0
    
    # Process each extracted claim
    for claim in claims_result.claims:
        logger.info(f"Retrieving evidence for claim: {claim.text}")
        
        # Search for fact-check evidence
        citations = await retriever.search_claim(claim.text)
        
        # Create search queries used
        search_queries = [
            claim.text,
            f"fact check {claim.text}",
            # Add entity-based queries if entities exist
            *[f"fact check {entity}" for entity in claim.entities[:2]]
        ]
        
        # Build retrieval notes
        retrieval_notes = f"Google Fact-Check API: Found {len(citations)} results"
        if citations:
            publishers = [c.publisher for c in citations]
            retrieval_notes += f". Publishers: {', '.join(set(publishers))}"
        
        # Create ClaimEvidence
        claim_evidence = ClaimEvidence(
            claim_text=claim.text,
            citations=citations,
            search_queries=search_queries,
            retrieval_notes=retrieval_notes
        )
        
        evidence_map[claim.text] = claim_evidence
        total_sources_found += len(citations)
    
    # Return structured result
    return EvidenceRetrievalResult(
        claim_evidence_map=evidence_map,
        total_sources_found=total_sources_found,
        retrieval_time_ms=0  # Could add timing if needed
    )


# Convenience function for direct usage
async def retrieve_evidence_for_claims(claims: List[ExtractedClaim]) -> EvidenceRetrievalResult:
    """
    Convenience function to retrieve evidence for a list of claims
    
    Args:
        claims: List of ExtractedClaim objects
        
    Returns:
        EvidenceRetrievalResult
    """
    # Create a minimal ClaimExtractionResult
    claims_result = ClaimExtractionResult(
        original_text=" | ".join([claim.text for claim in claims]),
        claims=claims,
        processing_notes=f"Processing {len(claims)} claims for evidence retrieval"
    )
    
    return await retrieve_evidence(claims_result)
