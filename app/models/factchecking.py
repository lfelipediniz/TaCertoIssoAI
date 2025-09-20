from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, Field


# ===== STEP 1: USER INPUT =====
class UserInput(BaseModel):
    """Raw, unstructured input from the user"""
    text: str = Field(..., description="Raw unstructured text from user")
    locale: str = Field(default="pt-BR", description="Language locale")
    timestamp: Optional[str] = Field(None, description="When the message was sent")
    context: Optional[str] = Field(None, description="Additional context or previous messages")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "I heard that vaccine X causes infertility in women, is this true?",
                "locale": "pt-BR",
                "timestamp": "2024-09-20T15:30:00Z",
                "context": "Previous discussion about vaccine safety"
            }
        }


# ===== STEP 2: CLAIM EXTRACTION =====
class ExtractedClaim(BaseModel):
    """A single claim extracted from user input"""
    text: str = Field(..., description="The normalized claim text")
    links: List[str] = Field(default_factory=list, description="Any URLs found in the original text")
    llm_comment: str = Field(..., description="LLM's analysis/comment about this claim")
    entities: List[str] = Field(default_factory=list, description="Named entities in the claim")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Vaccine X causes infertility in women",
                "links": ["https://example.com/article"],
                "llm_comment": "This is a specific medical claim that can be fact-checked against scientific literature",
                "entities": ["vaccine X", "infertility", "women"]
            }
        }


class ClaimExtractionResult(BaseModel):
    """Output of the claim extraction step"""
    original_text: str = Field(..., description="The original user input")
    claims: List[ExtractedClaim] = Field(..., description="List of extracted claims")
    processing_notes: Optional[str] = Field(None, description="Notes about the extraction process")

    class Config:
        json_schema_extra = {
            "example": {
                "original_text": "I heard that vaccine X causes infertility in women, is this true?",
                "claims": [
                    {
                        "text": "Vaccine X causes infertility in women",
                        "links": [],
                        "llm_comment": "Medical claim about vaccine safety that requires scientific evidence",
                        "entities": ["vaccine X", "infertility", "women"]
                    }
                ],
                "processing_notes": "Extracted 1 verifiable claim from user question"
            }
        }


# ===== STEP 2.5: LINK ENRICHMENT =====
class EnrichedLink(BaseModel):
    """A single enriched link with extracted content"""
    url: str = Field(..., description="The original URL")
    title: str = Field(default="", description="Title extracted from the webpage")
    content: str = Field(default="", description="Main text content extracted from the webpage")
    summary: str = Field(default="", description="AI-generated summary of the content")
    extraction_status: str = Field(default="pending", description="Status: 'success', 'failed', 'timeout', 'blocked'")
    extraction_notes: Optional[str] = Field(None, description="Notes about the extraction process")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/vaccine-study",
                "title": "Study on Vaccine Safety",
                "content": "This comprehensive study examined the safety profile of vaccines...",
                "summary": "Large-scale study found no link between vaccines and autism",
                "extraction_status": "success",
                "extraction_notes": "Content extracted successfully via web scraping"
            }
        }


class EnrichedClaim(BaseModel):
    """A claim with enriched link content"""
    text: str = Field(..., description="The normalized claim text")
    original_links: List[str] = Field(default_factory=list, description="Original URLs from claim extraction")
    enriched_links: List[EnrichedLink] = Field(default_factory=list, description="Links with extracted content")
    llm_comment: str = Field(..., description="LLM's analysis/comment about this claim")
    entities: List[str] = Field(default_factory=list, description="Named entities in the claim")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Vaccine X causes infertility in women",
                "original_links": ["https://example.com/study"],
                "enriched_links": [
                    {
                        "url": "https://example.com/study",
                        "title": "Vaccine Safety Study",
                        "content": "Study content...",
                        "summary": "Study summary...",
                        "extraction_status": "success"
                    }
                ],
                "llm_comment": "Medical claim requiring scientific evidence",
                "entities": ["vaccine X", "infertility", "women"]
            }
        }


class LinkEnrichmentResult(BaseModel):
    """Output of the link enrichment step"""
    original_claims: List[ExtractedClaim] = Field(..., description="Original claims from extraction")
    enriched_claims: List[EnrichedClaim] = Field(..., description="Claims with enriched link content")
    total_links_processed: int = Field(default=0, description="Total number of links processed")
    successful_extractions: int = Field(default=0, description="Number of successful content extractions")
    processing_time_ms: int = Field(default=0, description="Time taken for link enrichment")
    processing_notes: Optional[str] = Field(None, description="Notes about the enrichment process")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_claims": [],
                "enriched_claims": [],
                "total_links_processed": 2,
                "successful_extractions": 1,
                "processing_time_ms": 3500,
                "processing_notes": "1 of 2 links successfully enriched with content"
            }
        }


# ===== STEP 3: EVIDENCE RETRIEVAL =====
class Citation(BaseModel):
    """A single source citation"""
    url: str
    title: str
    publisher: str
    quoted: str
    rating: Optional[str] = None  # Google fact-check rating: "Falso", "Enganoso", "Verdadeiro", etc.
    review_date: Optional[str] = None  # When the fact-check was published

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://health.gov/vaccine-safety",
                "title": "Vaccine Safety Study Results",
                "publisher": "Ministry of Health",
                "published_at": "2024-11-05",
                "quoted": "No associations with infertility were observed in clinical studies"
            }
        }


class ClaimEvidence(BaseModel):
    """Evidence gathered for a specific claim"""
    claim_text: str = Field(..., description="The claim this evidence relates to")
    citations: List[Citation] = Field(default_factory=list, description="Sources supporting or refuting the claim")
    search_queries: List[str] = Field(default_factory=list, description="Queries used to find evidence")
    enriched_links: List[EnrichedLink] = Field(default_factory=list, description="Enriched links from the claim")
    retrieval_notes: Optional[str] = Field(None, description="Notes about the evidence retrieval process")

    class Config:
        json_schema_extra = {
            "example": {
                "claim_text": "Vaccine X causes infertility in women",
                "citations": [
                    {
                        "url": "https://health.gov/vaccine-safety",
                        "title": "Vaccine Safety Study",
                        "publisher": "Ministry of Health",
                        "published_at": "2024-11-05",
                        "quoted": "No associations with infertility were observed"
                    }
                ],
                "search_queries": ["vaccine X infertility", "vaccine safety women fertility"],
                "retrieval_notes": "Found 5 sources, selected top 3 most relevant"
            }
        }


class EvidenceRetrievalResult(BaseModel):
    """Output of the evidence retrieval step"""
    claim_evidence_map: Dict[str, ClaimEvidence] = Field(
        ..., 
        description="Maps each claim text to its evidence"
    )
    total_sources_found: int = Field(default=0, description="Total number of sources found")
    retrieval_time_ms: int = Field(default=0, description="Time taken for retrieval")

    class Config:
        json_schema_extra = {
            "example": {
                "claim_evidence_map": {
                    "Vaccine X causes infertility in women": {
                        "claim_text": "Vaccine X causes infertility in women",
                        "citations": [],
                        "search_queries": ["vaccine X infertility"],
                        "retrieval_notes": "Found multiple contradicting sources"
                    }
                },
                "total_sources_found": 8,
                "retrieval_time_ms": 2500
            }
        }


# ===== STEP 4: ADJUDICATION =====
class AdjudicationInput(BaseModel):
    """Input to the adjudication step"""
    original_user_text: str = Field(..., description="Original raw user input")
    enriched_claims: List[EnrichedClaim] = Field(..., description="Claims with enriched links from step 2.5")
    evidence_map: Dict[str, ClaimEvidence] = Field(..., description="Evidence for each claim")
    additional_context: Optional[str] = Field(None, description="Any additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "original_user_text": "I heard that vaccine X causes infertility in women, is this true?",
                "claims": [],
                "evidence_map": {},
                "additional_context": "User seems concerned about vaccine safety"
            }
        }


class FactCheckResult(BaseModel):
    """Final result of the fact-checking pipeline"""
    original_query: str
    analysis_text: str = Field(..., description="Complete analysis as formatted text")

    class Config:
        json_schema_extra = {
            "example": {
                "original_query": "I heard that vaccine X causes infertility in women, is this true?",
                "analysis_text": """O usuário questionou sobre a relação entre vacina X e infertilidade feminina. Esta é uma preocupação comum que circula em redes sociais mas não tem base científica sólida.

                Análise por alegação:
                • Vacina X causa infertilidade em mulheres: FALSE

                Fontes de apoio:
                - Ministerio da Saúde: nenhuma ligação entre vacinas e autismo foi encontrada """
            }
        }


# ===== PIPELINE FLOW SUMMARY =====
"""
Updated Pipeline Flow (5 Steps):
1. UserInput -> 
2. ClaimExtractionResult -> 
2.5. LinkEnrichmentResult -> 
3. EvidenceRetrievalResult -> 
4. AdjudicationInput -> FactCheckResult

Step 2.5 (Link Enrichment) extracts content from URLs found in claims,
providing additional context for evidence retrieval and adjudication.

Each step has clear inputs and outputs, making the pipeline traceable and debuggable.
"""