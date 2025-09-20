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
    claims: List[ExtractedClaim] = Field(..., description="Claims from extraction step")
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
    overall_verdict: str  # "true", "false", "misleading", "unverifiable", "mixed"
    rationale: str
    supporting_citations: List[Citation]

    class Config:
        json_schema_extra = {
            "example": {
                "original_query": "I heard that vaccine X causes infertility in women, is this true?",
                "overall_verdict": "false",
                "rationale": "Scientific evidence from multiple health authorities shows no link between vaccine X and infertility. Clinical trials and post-marketing surveillance have not identified fertility issues as a side effect.",
                "claim_verdicts": {
                    "Vaccine X causes infertility in women": "false"
                },
                "supporting_citations": [
                    {
                        "url": "https://health.gov/vaccine-safety",
                        "title": "Vaccine Safety Study",
                        "publisher": "Ministry of Health",
                        "published_at": "2024-11-05",
                        "quoted": "No associations with infertility were observed in clinical studies"
                    }
                ],
                "processing_time_ms": 8500
            }
        }


# ===== PIPELINE FLOW SUMMARY =====
"""
Pipeline Flow:
1. UserInput -> 
2. ClaimExtractionResult -> 
3. EvidenceRetrievalResult -> 
4. AdjudicationInput -> FactCheckResult

Each step has clear inputs and outputs, making the pipeline traceable and debuggable.
"""