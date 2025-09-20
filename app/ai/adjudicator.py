from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.models.factchecking import (
    AdjudicationInput, 
    FactCheckResult, 
    ExtractedClaim, 
    ClaimEvidence,
    Citation
)
from app.core.config import get_settings

settings = get_settings()

# Initialize OpenAI model for reasoning
reasoning_model = ChatOpenAI(
    model="gpt-4o",  # Use latest reasoning model
    temperature=0.1,  # Low temperature for consistency
    max_tokens=4000,  # Sufficient for detailed analysis
    timeout=30,  # 30 second timeout
)

# Portuguese adjudication prompt
adjudication_prompt = ChatPromptTemplate.from_messages([
    ("system", """Você é um especialista em verificação de fatos. Analise as alegações fornecidas contra as evidências disponíveis e forneça um veredicto fundamentado.

REGRAS IMPORTANTES:
1. Use APENAS as evidências fornecidas - não utilize conhecimento externo
2. Se as fontes conflitam ou são insuficientes → 'unverifiable'
3. Use 'misleading' se os fatos são verdadeiros mas o contexto induz ao erro
4. Prefira fontes recentes e de autoridades reconhecidas
5. Para múltiplas alegações, determine um veredicto geral:
   - Se todas são 'true' → 'true'
   - Se todas são 'false' → 'false' 
   - Se misturadas → 'mixed'
   - Se maioria é 'unverifiable' → 'unverifiable'
6. Forneça explicação em português claro e objetivo
7. Inclua pelo menos 3 citações quando possível
8. Seja específico sobre datas, contexto e nuances

VERDICTS DISPONÍVEIS: 'true', 'false', 'misleading', 'unverifiable', 'mixed'"""),
    
    ("user", """CONSULTA ORIGINAL DO USUÁRIO:
{original_query}

ALEGAÇÕES EXTRAÍDAS:
{claims_text}

EVIDÊNCIAS COLETADAS:
{evidence_text}

ANÁLISE SOLICITADA:
Por favor, analise cada alegação individualmente e depois forneça um veredicto geral. Considere:
- A qualidade e credibilidade das fontes
- A data das informações vs. quando a alegação foi feita
- Contexto e nuances importantes
- Contradições entre fontes

Forneça o resultado no formato estruturado solicitado.""")
])

# Create the adjudication chain with structured output
adjudication_chain = (
    adjudication_prompt 
    | reasoning_model.with_structured_output(FactCheckResult)
)


async def adjudicate_claims(adjudication_input: AdjudicationInput) -> FactCheckResult:
    """
    Main adjudication function that analyzes claims against evidence.
    
    Args:
        adjudication_input: Contains original text, claims, and evidence
        
    Returns:
        FactCheckResult with overall verdict, rationale, and citations
    """
    try:
        # Format claims for the prompt
        claims_text = _format_claims_for_prompt(adjudication_input.claims)
        
        # Format evidence for the prompt
        evidence_text = _format_evidence_for_prompt(adjudication_input.evidence_map)
        
        # Invoke the adjudication chain
        result = await adjudication_chain.ainvoke({
            "original_query": adjudication_input.original_user_text,
            "claims_text": claims_text,
            "evidence_text": evidence_text
        })
        
        # Validate and enhance the result
        result = _validate_and_enhance_result(result, adjudication_input)
        
        return result
        
    except Exception as e:
        # Fallback to unverifiable with error explanation
        return _create_fallback_result(adjudication_input, str(e))


def _format_claims_for_prompt(claims: List[ExtractedClaim]) -> str:
    """Format extracted claims for the LLM prompt"""
    if not claims:
        return "Nenhuma alegação específica foi extraída."
    
    formatted_claims = []
    for i, claim in enumerate(claims, 1):
        claim_text = f"{i}. **Alegação**: {claim.text}\n"
        
        if claim.entities:
            claim_text += f"   **Entidades**: {', '.join(claim.entities)}\n"
        
        if claim.links:
            claim_text += f"   **Links mencionados**: {', '.join(claim.links)}\n"
        
        claim_text += f"   **Análise LLM**: {claim.llm_comment}\n"
        
        formatted_claims.append(claim_text)
    
    return "\n".join(formatted_claims)


def _format_evidence_for_prompt(evidence_map: Dict[str, ClaimEvidence]) -> str:
    """Format evidence for the LLM prompt"""
    if not evidence_map:
        return "Nenhuma evidência foi coletada."
    
    formatted_evidence = []
    
    for claim_text, evidence in evidence_map.items():
        evidence_text = f"\n**EVIDÊNCIAS PARA**: {claim_text}\n"
        evidence_text += f"**Consultas utilizadas**: {', '.join(evidence.search_queries)}\n"
        
        if evidence.citations:
            evidence_text += "**Fontes encontradas**:\n"
            for i, citation in enumerate(evidence.citations, 1):
                evidence_text += f"  {i}. **{citation.title}** ({citation.publisher})\n"
                evidence_text += f"     URL: {citation.url}\n"
                if citation.published_at:
                    evidence_text += f"     Data: {citation.published_at}\n"
                if citation.quoted:
                    evidence_text += f"     Trecho: \"{citation.quoted}\"\n"
                evidence_text += "\n"
        else:
            evidence_text += "**Nenhuma fonte relevante encontrada**\n"
        
        if evidence.retrieval_notes:
            evidence_text += f"**Notas**: {evidence.retrieval_notes}\n"
        
        formatted_evidence.append(evidence_text)
    
    return "\n".join(formatted_evidence)


def _validate_and_enhance_result(result: FactCheckResult, input_data: AdjudicationInput) -> FactCheckResult:
    """Validate and enhance the LLM result"""
    
    # Ensure we have the original query
    if not result.original_query:
        result.original_query = input_data.original_user_text
    
    # Validate verdict is in allowed options
    allowed_verdicts = ["true", "false", "misleading", "unverifiable", "mixed"]
    if result.overall_verdict not in allowed_verdicts:
        result.overall_verdict = "unverifiable"
    
    # Ensure we have at least one citation if evidence was available
    if not result.supporting_citations and input_data.evidence_map:
        # Extract some citations from the evidence
        all_citations = []
        for evidence in input_data.evidence_map.values():
            all_citations.extend(evidence.citations)
        
        # Take up to 3 best citations
        result.supporting_citations = all_citations[:3]
    
    # Ensure rationale is within bounds
    if len(result.rationale) < 10:
        result.rationale = "Análise baseada nas evidências fornecidas não permite conclusão definitiva."
    elif len(result.rationale) > 2000:
        result.rationale = result.rationale[:1997] + "..."
    
    return result


def _create_fallback_result(input_data: AdjudicationInput, error_msg: str) -> FactCheckResult:
    """Create a fallback result when adjudication fails"""
    
    # Extract any available citations
    citations = []
    for evidence in input_data.evidence_map.values():
        citations.extend(evidence.citations[:2])  # Max 2 per claim
    
    if not citations:
        # Create a minimal citation to satisfy the constraint
        citations = [Citation(
            url="https://example.com/error",
            title="Erro no processamento",
            publisher="Sistema",
            quoted="Não foi possível processar as evidências adequadamente."
        )]
    
    return FactCheckResult(
        original_query=input_data.original_user_text,
        overall_verdict="unverifiable",
        rationale=f"Não foi possível completar a análise devido a um erro técnico. "
                 f"Recomendamos verificar manualmente as fontes disponíveis. Erro: {error_msg[:100]}",
        claim_verdicts={claim.text: "unverifiable" for claim in input_data.claims},
        supporting_citations=citations[:3],  # Max 3 citations
        processing_time_ms=0
    )


async def generate_citations(sources: List[Dict]) -> List[Citation]:
    """
    Convert source dictionaries to Citation objects
    """
    citations = []
    for source in sources:
        try:
            citation = Citation(
                url=source.get("url", ""),
                title=source.get("title", ""),
                publisher=source.get("publisher", ""),
                published_at=source.get("published_at"),
                quoted=source.get("quoted")
            )
            citations.append(citation)
        except Exception:
            continue  # Skip invalid citations
    
    return citations
