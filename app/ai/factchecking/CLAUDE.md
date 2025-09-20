
## 8) Fact-Checking Pipeline Implementation

This section demonstrates how to implement a complete fact-checking pipeline using LangChain best practices, specifically designed for WhatsApp integration with a clean 4-step architecture.

### 8.1 Pipeline Overview

**Architecture:** Clean 4-step pipeline with Pydantic models and LCEL composition
```
UserInput → ClaimExtractionResult → EvidenceRetrievalResult → FactCheckResult
```

**Key Features:**
- Multi-claim processing (handles multiple claims per user message)
- Structured outputs at every step using `with_structured_output()`
- Async-first design with streaming support
- Portuguese language support with fallback to English

### 8.2 Data Models (Pydantic + LangChain Compatible)

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

# Step 1: User Input
class UserInput(BaseModel):
    chatId: str
    messageId: Optional[str] = None
    text: str
    locale: str = "pt-BR"
    timestamp: Optional[str] = None
    context: Optional[str] = None

# Step 2: Claim Extraction
class ExtractedClaim(BaseModel):
    text: str = Field(..., description="Normalized claim text")
    links: List[str] = Field(default_factory=list)
    llm_comment: str = Field(..., description="LLM analysis of this claim")
    entities: List[str] = Field(default_factory=list)

class ClaimExtractionResult(BaseModel):
    original_text: str
    claims: List[ExtractedClaim]
    processing_notes: Optional[str] = None

# Step 3: Evidence Retrieval
class Citation(BaseModel):
    url: str
    title: str
    publisher: str
    published_at: Optional[str] = None
    quoted: Optional[str] = None

class ClaimEvidence(BaseModel):
    claim_text: str
    citations: List[Citation] = Field(default_factory=list)
    search_queries: List[str] = Field(default_factory=list)
    retrieval_notes: Optional[str] = None

class EvidenceRetrievalResult(BaseModel):
    claim_evidence_map: Dict[str, ClaimEvidence]
    total_sources_found: int = 0
    retrieval_time_ms: int = 0

# Step 4: Final Adjudication
class FactCheckResult(BaseModel):
    original_query: str
    overall_verdict: Literal["true", "false", "misleading", "unverifiable", "mixed"]
    rationale: str = Field(..., min_length=10, max_length=2000)
    claim_verdicts: Dict[str, Literal["true", "false", "misleading", "unverifiable"]]
    supporting_citations: List[Citation] = Field(..., min_items=1)
    processing_time_ms: int = 0
```

### 8.3 Step Implementation Examples

**Step 1: Claim Extraction Chain**
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

claim_extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a claim extraction specialist. Extract verifiable claims from user text.
    Rules:
    - Extract multiple claims if present
    - Include any URLs found in the text
    - Provide analysis comments for each claim
    - Focus on factual statements that can be verified
    - Output in Portuguese when possible"""),
    ("user", "Text: {text}\n\nExtract verifiable claims:")
])

model = ChatOpenAI(model="gpt-4o", temperature=0)
claim_extraction_chain = (
    claim_extraction_prompt 
    | model.with_structured_output(ClaimExtractionResult)
)

# Usage
async def extract_claims(user_input: UserInput) -> ClaimExtractionResult:
    result = await claim_extraction_chain.ainvoke({"text": user_input.text})
    return result
```

**Step 2: Evidence Retrieval with Parallel Processing**
```python
from langchain_core.runnables import RunnableParallel, RunnableLambda
import httpx

async def search_news_for_claim(claim: str) -> List[Dict]:
    # Implement news API search
    # Return structured results
    pass

async def search_wikipedia_for_claim(claim: str) -> List[Dict]:
    # Implement Wikipedia search
    # Return structured results
    pass

def create_evidence_retrieval_chain():
    return RunnableParallel({
        "news_results": RunnableLambda(search_news_for_claim),
        "wiki_results": RunnableLambda(search_wikipedia_for_claim)
    })

# Usage
async def retrieve_evidence(claims: List[ExtractedClaim]) -> EvidenceRetrievalResult:
    evidence_map = {}
    total_sources = 0
    
    for claim in claims:
        # Process each claim in parallel
        results = await create_evidence_retrieval_chain().ainvoke(claim.text)
        
        citations = []
        # Convert results to Citation objects
        for result in results["news_results"] + results["wiki_results"]:
            citations.append(Citation(**result))
        
        evidence_map[claim.text] = ClaimEvidence(
            claim_text=claim.text,
            citations=citations,
            search_queries=[f"fact check {claim.text}"],
            retrieval_notes=f"Found {len(citations)} sources"
        )
        total_sources += len(citations)
    
    return EvidenceRetrievalResult(
        claim_evidence_map=evidence_map,
        total_sources_found=total_sources
    )
```

**Step 3: LLM Adjudication with Structured Output**
```python
adjudication_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a fact-checking judge. Analyze claims against evidence.
    
    Rules:
    - Use ONLY the provided evidence (no external knowledge)
    - If sources conflict or are insufficient → 'unverifiable'
    - 'misleading' if facts are true but context misleads
    - Prefer recent, authoritative sources
    - Provide rationale in Portuguese
    - Include at least 3 citations when possible"""),
    ("user", """
    Original Query: {original_query}
    
    Claims to verify:
    {claims_text}
    
    Available Evidence:
    {evidence_text}
    
    Provide fact-check verdict with citations:""")
])

adjudication_chain = (
    adjudication_prompt 
    | model.with_structured_output(FactCheckResult)
)

async def adjudicate_claims(
    original_query: str,
    claims: List[ExtractedClaim], 
    evidence: EvidenceRetrievalResult
) -> FactCheckResult:
    
    # Format evidence for prompt
    claims_text = "\n".join([f"- {claim.text}" for claim in claims])
    evidence_text = ""
    
    for claim_text, claim_evidence in evidence.claim_evidence_map.items():
        evidence_text += f"\nClaim: {claim_text}\n"
        for citation in claim_evidence.citations:
            evidence_text += f"  - {citation.title} ({citation.publisher}): {citation.quoted}\n"
    
    result = await adjudication_chain.ainvoke({
        "original_query": original_query,
        "claims_text": claims_text,
        "evidence_text": evidence_text
    })
    
    return result
```

### 8.4 Complete Pipeline Chain

```python
from langchain_core.runnables import RunnableLambda

def create_fact_check_pipeline():
    """Create the complete 4-step fact-checking pipeline"""
    
    async def pipeline_logic(user_input: UserInput) -> FactCheckResult:
        # Step 1: Extract claims
        claims_result = await extract_claims(user_input)
        
        # Step 2: Retrieve evidence
        evidence_result = await retrieve_evidence(claims_result.claims)
        
        # Step 3: Adjudicate
        final_result = await adjudicate_claims(
            user_input.text,
            claims_result.claims,
            evidence_result
        )
        
        return final_result
    
    return RunnableLambda(pipeline_logic)

# Usage
pipeline = create_fact_check_pipeline()

# Process user input
user_input = UserInput(
    chatId="5521999999999@g.us",
    text="I heard that vaccine X causes infertility, is this true?",
    locale="pt-BR"
)

result = await pipeline.ainvoke(user_input)
print(f"Verdict: {result.overall_verdict}")
print(f"Rationale: {result.rationale}")
```

### 8.5 Streaming Implementation

```python
from langchain_core.callbacks import AsyncCallbackHandler

class FactCheckStreamingCallback(AsyncCallbackHandler):
    async def on_chain_start(self, serialized: dict, inputs: dict, **kwargs):
        print(f"🔍 Starting fact-check for: {inputs.get('text', '')[:50]}...")
    
    async def on_chain_end(self, outputs: dict, **kwargs):
        print(f"✅ Fact-check complete: {outputs.get('overall_verdict', 'unknown')}")

# Add streaming to pipeline
streaming_pipeline = pipeline.with_config({
    "callbacks": [FactCheckStreamingCallback()]
})

# Stream results to WhatsApp
async for chunk in streaming_pipeline.astream(user_input):
    # Send intermediate updates to WhatsApp
    await send_whatsapp_update(user_input.chatId, f"Processing: {chunk}")
```

### 8.6 Integration with FastAPI

```python
from fastapi import FastAPI, HTTPException
from app.models.schemas import TextRequest, AnalysisResponse
from app.models.factchecking import UserInput, FactCheckResult

app = FastAPI()

@app.post("/api/text", response_model=AnalysisResponse)
async def fact_check_text(request: TextRequest):
    try:
        # Convert API request to pipeline input
        user_input = UserInput(
            chatId=request.chatId or "api_request",
            text=request.text,
            locale="pt-BR"
        )
        
        # Run pipeline
        result: FactCheckResult = await pipeline.ainvoke(user_input)
        
        # Convert to API response
        return AnalysisResponse(
            message_id=f"fc_{hash(request.text)}",
            verdict=result.overall_verdict,
            rationale=result.rationale,
            citations=result.supporting_citations,
            processing_time_ms=result.processing_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 8.7 Key Benefits of This Architecture

- **Structured Outputs**: Every step returns validated Pydantic models
- **Type Safety**: Full typing throughout the pipeline
- **Async Support**: All operations are async-first for better performance
- **Streaming Ready**: Can provide real-time updates to users
- **Multi-claim**: Handles complex inputs with multiple claims
- **Language Support**: Portuguese-first with English fallback
- **Error Handling**: Graceful degradation with 'unverifiable' fallbacks
- **Tracing**: Full LangSmith integration for debugging and evaluation

---
