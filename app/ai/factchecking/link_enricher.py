"""
Link Enrichment Module - Step 2.5 of Fact-Checking Pipeline

This module takes claims with URLs and enriches them by extracting content from those URLs.
Based on the existing webscraping module using newspaper3k library.

Follows LangChain best practices:
- Async-first design
- Structured outputs with Pydantic models
- Error handling and fallback mechanisms
- Detailed logging and processing notes
"""

import asyncio
import time
import logging

from newspaper import Article, Config

from app.models.factchecking import (
    ClaimExtractionResult,
    ExtractedClaim,
    EnrichedLink,
    EnrichedClaim,
    LinkEnrichmentResult
)

logger = logging.getLogger(__name__)


class LinkEnricher:
    """
    Enriches claims by extracting content from their associated URLs.
    
    Uses newspaper3k for web scraping with async execution.
    """
    
    def __init__(self, content_limit: int = 5000):
        """Initialize the link enricher with web scraping capabilities."""
        
        # Configure newspaper3k for web scraping
        self.newspaper_config = Config()
        self.newspaper_config.browser_user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        self.newspaper_config.request_timeout = 15  # Increased timeout
        
        # Content limit for extracted text
        self.content_limit = content_limit

    async def enrich_links(self, claims_result: ClaimExtractionResult) -> LinkEnrichmentResult:
        """
        Main method to enrich all claims with link content.
        
        Args:
            claims_result: Result from claim extraction step
            
        Returns:
            LinkEnrichmentResult with enriched claims
        """
        start_time = time.time()
        
        enriched_claims = []
        total_links = 0
        successful_extractions = 0
        
        for claim in claims_result.claims:
            if claim.links:
                total_links += len(claim.links)
                enriched_claim = await self._enrich_single_claim(claim)
                
                # Count successful extractions
                for enriched_link in enriched_claim.enriched_links:
                    if enriched_link.extraction_status == "success":
                        successful_extractions += 1
                        
                enriched_claims.append(enriched_claim)
            else:
                # No links to enrich, convert to EnrichedClaim as-is
                enriched_claim = EnrichedClaim(
                    text=claim.text,
                    original_links=[],
                    enriched_links=[],
                    llm_comment=claim.llm_comment,
                    entities=claim.entities
                )
                enriched_claims.append(enriched_claim)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        processing_notes = (
            f"Processados {total_links} links. "
            f"{successful_extractions} extrações bem-sucedidas. "
            f"{total_links - successful_extractions} falhas."
        )
        
        return LinkEnrichmentResult(
            original_claims=claims_result.claims,
            enriched_claims=enriched_claims,
            total_links_processed=total_links,
            successful_extractions=successful_extractions,
            processing_time_ms=processing_time,
            processing_notes=processing_notes
        )

    async def _enrich_single_claim(self, claim: ExtractedClaim) -> EnrichedClaim:
        """Enrich a single claim by extracting content from its links."""
        
        enriched_links = []
        
        # Process each link in the claim
        for url in claim.links:
            enriched_link = await self._extract_link_content(url)
            enriched_links.append(enriched_link)
        
        return EnrichedClaim(
            text=claim.text,
            original_links=claim.links,
            enriched_links=enriched_links,
            llm_comment=claim.llm_comment,
            entities=claim.entities
        )

    async def _extract_link_content(self, url: str) -> EnrichedLink:
        """
        Extract content from a single URL using newspaper3k.
        
        Args:
            url: The URL to extract content from
            
        Returns:
            EnrichedLink with extracted content and summary
        """
        enriched_link = EnrichedLink(
            url=url,
            extraction_status="pending"
        )
        
        try:
            # Use asyncio to run newspaper3k extraction in thread pool
            # (newspaper3k is synchronous, so we need to wrap it)
            loop = asyncio.get_event_loop()
            extraction_result = await loop.run_in_executor(
                None, 
                self._extract_with_newspaper, 
                url
            )
            
            if extraction_result:
                enriched_link.title = extraction_result.get("titulo", "")
                
                # Apply content limit from the existing webscraping logic
                full_content = extraction_result.get("texto_completo", "")
                enriched_link.content = full_content[:self.content_limit] if full_content else ""
                
                # Create a simple summary based on title and first paragraph
                enriched_link.summary = self._create_simple_summary(
                    enriched_link.title, 
                    enriched_link.content
                )
                
                enriched_link.extraction_status = "success"
                enriched_link.extraction_notes = f"Conteúdo extraído com newspaper3k. Tamanho: {len(full_content)} chars, limitado a {len(enriched_link.content)} chars"
            else:
                enriched_link.extraction_status = "failed"
                enriched_link.extraction_notes = "Falha na extração de conteúdo"
                
        except Exception as e:
            logger.error(f"Link enrichment failed for {url}: {e}")
            enriched_link.extraction_status = "failed"
            enriched_link.extraction_notes = f"Erro durante extração: {str(e)[:100]}"
        
        return enriched_link

    def _extract_with_newspaper(self, url: str) -> dict:
        """
        Synchronous wrapper for newspaper3k extraction.
        Based on the existing webscraping/main.py implementation.
        """
        try:
            # Create Article object with our configuration
            artigo = Article(url, language='pt', config=self.newspaper_config)
            
            # Download and parse the HTML
            artigo.download()
            artigo.parse()
            
            # Extract the information
            info_noticia = {
                "titulo": artigo.title or "",
                "autores": artigo.authors or [],
                "data_publicacao": artigo.publish_date,
                "texto_completo": artigo.text or "",
            }
            
            return info_noticia
            
        except Exception as e:
            logger.error(f"Newspaper3k extraction failed for {url}: {e}")
            return None

    def _create_simple_summary(self, title: str, content: str) -> str:
        """
        Create a simple summary without LLM, using basic text processing.
        """
        if not content:
            return "Conteúdo não disponível"
        
        # Use title and first paragraph as summary
        summary_parts = []
        
        if title:
            summary_parts.append(f"Título: {title}")
        
        # Get first paragraph (up to first double newline or first 200 chars)
        first_paragraph = content.split('\n\n')[0] if '\n\n' in content else content
        first_paragraph = first_paragraph[:200] + "..." if len(first_paragraph) > 200 else first_paragraph
        
        if first_paragraph.strip():
            summary_parts.append(f"Resumo: {first_paragraph.strip()}")
        
        return " | ".join(summary_parts) if summary_parts else "Conteúdo extraído mas sem informações resumíveis"


# Factory function for creating enricher
def create_link_enricher(content_limit: int = 5000) -> LinkEnricher:
    """
    Factory function to create a LinkEnricher instance.
    """
    return LinkEnricher(content_limit=content_limit)


# Async helper function for direct usage
async def enrich_claim_links(claims_result: ClaimExtractionResult) -> LinkEnrichmentResult:
    """
    Convenience function to enrich links from claim extraction result.
    
    Args:
        claims_result: ClaimExtractionResult from step 2
        
    Returns:
        LinkEnrichmentResult with enriched claims
    """
    enricher = create_link_enricher()
    return await enricher.enrich_links(claims_result)
