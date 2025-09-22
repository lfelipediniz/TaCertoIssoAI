#!/usr/bin/env python3
"""
Script de teste para o Link Enricher com pipeline otimizada
Testa a extração de conteúdo de diferentes tipos de URLs
"""

import asyncio
import logging
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ai.factchecking.link_enricher import extrair_noticia_principal_de_link, LinkEnricher
from app.models.factchecking import ClaimExtractionResult, ExtractedClaim

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def testar_extracao_direta(url):
    """Testa a extração direta usando a função extrair_noticia_principal_de_link"""
    print(f"\n🔍 Testando extração direta para: {url}")
    print("=" * 60)
    
    try:
        dados_da_noticia = extrair_noticia_principal_de_link(url)
        
        if dados_da_noticia:
            print("\n✅ INFORMAÇÕES EXTRAÍDAS COM SUCESSO!")
            print(f"📰 Título: {dados_da_noticia['titulo']}")
            print(f"👤 Autores: {dados_da_noticia['autores']}")
            print(f"📅 Data de Publicação: {dados_da_noticia['data_publicacao']}")
            print(f"🔧 Método usado: {dados_da_noticia.get('metodo_usado', 'N/A')}")
            print(f"📝 Tamanho do texto: {len(dados_da_noticia['texto_completo'])} caracteres")
            print("\n--- TEXTO LIMPO DO ARTIGO ---")
            texto = dados_da_noticia['texto_completo']
            preview = texto[:500] + "..." if len(texto) > 500 else texto
            print(preview)
            
            return dados_da_noticia
        else:
            print("❌ Falha na extração - nenhum método funcionou")
            return None
            
    except Exception as e:
        print(f"❌ Erro durante extração: {e}")
        return None

async def testar_link_enricher(url):
    """Testa o LinkEnricher usando a pipeline completa"""
    print(f"\n🔍 Testando LinkEnricher para: {url}")
    print("=" * 60)
    
    try:
        # Criar um claim de teste
        test_claim = ExtractedClaim(
            text=f"Teste de extração para {url}",
            links=[url],
            llm_comment="Teste de pipeline otimizada",
            entities=[]
        )
        
        claims_result = ClaimExtractionResult(
            claims=[test_claim],
            processing_time_ms=100,
            processing_notes="Teste"
        )
        
        # Criar enricher e processar
        enricher = LinkEnricher(content_limit=2000)
        result = await enricher.enrich_links(claims_result)
        
        print(f"\n✅ RESULTADO DO LINK ENRICHER:")
        print(f"📊 Total de links processados: {result.total_links_processed}")
        print(f"✅ Extrações bem-sucedidas: {result.successful_extractions}")
        print(f"⏱️ Tempo de processamento: {result.processing_time_ms}ms")
        print(f"📝 Notas: {result.processing_notes}")
        
        for enriched_claim in result.enriched_claims:
            for enriched_link in enriched_claim.enriched_links:
                print(f"\n🔗 Link: {enriched_link.url}")
                print(f"📊 Status: {enriched_link.extraction_status}")
                print(f"📰 Título: {enriched_link.title}")
                print(f"📝 Resumo: {enriched_link.summary}")
                print(f"📄 Conteúdo (primeiros 200 chars): {enriched_link.content[:200]}...")
                print(f"🔧 Notas: {enriched_link.extraction_notes}")
        
        return result
        
    except Exception as e:
        print(f"❌ Erro durante teste do LinkEnricher: {e}")
        return None

async def main():
    """Função principal de teste"""
    print("🚀 TESTANDO SISTEMA DE WEB SCRAPING OTIMIZADO")
    print("=" * 80)
    print("PIPELINE OTIMIZADA - Métodos rápidos primeiro, pesados depois:")
    print("")
    print("FASE 1 - MÉTODOS RÁPIDOS (HTTP requests):")
    print("1. Trafilatura (muito robusto)")
    print("2. Goose3 (especializado em notícias) - apenas para X/Twitter")
    print("3. Newspaper3k (especializado em notícias)")
    print("4. Readability (focado em conteúdo principal)")
    print("5. Requests Session (com cookies)")
    print("6. BeautifulSoup (último recurso)")
    print("")
    print("FASE 2 - MÉTODOS PESADOS (apenas se necessário):")
    print("7. Selenium (para sites com JavaScript)")
    print("8. Selenium Avançado (anti-detecção)")
    print("")
    print("✅ DETECÇÃO INTELIGENTE: Rejeita mensagens de 'JavaScript disabled'")
    print("=" * 80)
    
    # URLs de teste
    urls_teste = [
        "https://www.threads.com/@brazilcalisthenics/post/DOwbblUAe2x?xmt=AQF0_znJyiKEGAcPFHY4Hz1gYB99kE_5pGgjc9wZMwRYkg",
        "https://www.cnn.com/2024/01/15/tech/ai-news/index.html",
        "https://www.bbc.com/news/technology-12345678"
    ]
    
    for i, url in enumerate(urls_teste, 1):
        print(f"\n🔍 TESTE {i}/{len(urls_teste)}")
        
        # Teste 1: Extração direta
        print("\n--- TESTE 1: EXTRAÇÃO DIRETA ---")
        testar_extracao_direta(url)
        
        # Teste 2: LinkEnricher completo
        print("\n--- TESTE 2: LINK ENRICHER COMPLETO ---")
        await testar_link_enricher(url)
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
