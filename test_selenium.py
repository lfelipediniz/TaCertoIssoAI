#!/usr/bin/env python3
"""
Script para testar se o Selenium está funcionando corretamente no ambiente.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_selenium_availability():
    """Testa se o Selenium está disponível e funcionando."""
    
    print("🔍 Testando disponibilidade do Selenium...")
    
    # Test 1: Import Selenium
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        print("✅ Selenium importado com sucesso")
    except ImportError as e:
        print(f"❌ Falha ao importar Selenium: {e}")
        return False
    
    # Test 2: Check Chrome availability
    try:
        import subprocess
        result = subprocess.run(['google-chrome', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Google Chrome disponível: {result.stdout.strip()}")
        else:
            print("❌ Google Chrome não encontrado")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar Chrome: {e}")
        return False
    
    # Test 3: Check ChromeDriver
    try:
        result = subprocess.run(['chromedriver', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ ChromeDriver disponível: {result.stdout.strip()}")
        else:
            print("❌ ChromeDriver não encontrado")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar ChromeDriver: {e}")
        return False
    
    # Test 4: Try to create WebDriver
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        service = Service('/usr/local/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Test navigation
        driver.get("https://httpbin.org/get")
        title = driver.title
        driver.quit()
        
        print(f"✅ WebDriver funcionando - título da página: {title}")
        return True
        
    except Exception as e:
        print(f"❌ Falha ao criar WebDriver: {e}")
        return False

def test_link_enricher():
    """Testa o link enricher com uma URL simples."""
    
    print("\n🔍 Testando Link Enricher...")
    
    try:
        # Import the link enricher
        from app.ai.factchecking.link_enricher import extrair_noticia_principal_de_link
        
        # Test with a simple URL
        test_url = "https://httpbin.org/html"
        print(f"Testando URL: {test_url}")
        
        result = extrair_noticia_principal_de_link(test_url)
        
        if result:
            print("✅ Link enricher funcionando!")
            print(f"Título: {result.get('titulo', 'N/A')}")
            print(f"Método usado: {result.get('metodo_usado', 'N/A')}")
            print(f"Tamanho do conteúdo: {len(result.get('texto_completo', ''))} chars")
            return True
        else:
            print("❌ Link enricher falhou")
            return False
            
    except Exception as e:
        print(f"❌ Erro no link enricher: {e}")
        return False

def main():
    """Função principal."""
    
    print("🚀 Testando configuração do Selenium para o Render\n")
    
    # Check environment
    if os.path.exists('/.dockerenv'):
        print("🐳 Executando em container Docker")
    elif os.getenv('RENDER'):
        print("☁️ Executando no Render")
    else:
        print("💻 Executando localmente")
    
    print(f"Python version: {sys.version}")
    print(f"Environment variables: CONTAINER={os.getenv('CONTAINER')}, RENDER={os.getenv('RENDER')}")
    
    # Run tests
    selenium_ok = test_selenium_availability()
    
    if selenium_ok:
        link_enricher_ok = test_link_enricher()
        
        if link_enricher_ok:
            print("\n🎉 Todos os testes passaram! O ambiente está configurado corretamente.")
            return 0
        else:
            print("\n⚠️ Selenium OK, mas link enricher falhou.")
            return 1
    else:
        print("\n❌ Selenium não está funcionando. Verifique a instalação do Chrome/ChromeDriver.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
