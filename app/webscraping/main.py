from newspaper import Article, Config

def extrair_noticia_principal_de_link(url):
    """
    Usa a biblioteca Newspaper3k para baixar e extrair o conteúdo limpo
    e os metadados de um artigo de notícia em uma URL.
    
    Args:
        url (str): O link da notícia.
        
    Returns:
        dict: Um dicionário com o título, autores, data e o texto limpo da notícia.
        None: Se ocorrer um erro.
    """
    try:
        # Configuração para simular um navegador e definir o idioma (melhora a extração)
        config = Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        config.request_timeout = 10
        
        # Cria um objeto 'Article' com a URL
        artigo = Article(url, language='pt', config=config)
        
        # 1. Baixa o HTML da página
        artigo.download()
        
        # 2. Processa o HTML para encontrar o conteúdo principal
        artigo.parse()
        
        # 3. Usa Processamento de Linguagem Natural para extrair palavras-chave (opcional)
        # artigo.nlp()

        # Agora, os dados limpos estão disponíveis como atributos do objeto!
        info_noticia = {
            "titulo": artigo.title,
            "autores": artigo.authors,
            "data_publicacao": artigo.publish_date,
            "texto_completo": artigo.text,
            # "palavras_chave": artigo.keywords # Disponível após chamar artigo.nlp()
        }
        
        return info_noticia

    except Exception as e:
        print(f"Falha ao processar o artigo com newspaper3k: {e}")
        return None

# --- Exemplo Prático de Uso ---

# Um link de notícia qualquer
link_da_noticia = "https://noticias.uol.com.br/politica/ultimas-noticias/2025/09/20/flavio-bolsonaro-defende-anistia-pec-da-blindagem-de-pec-da-sobrevivencia.htm"

# Chama a função
dados_da_noticia = extrair_noticia_principal_de_link(link_da_noticia)

if dados_da_noticia:
    print("--- INFORMAÇÕES EXTRAÍDAS COM SUCESSO ---")
    print(f"Título: {dados_da_noticia['titulo']}")
    print(f"Autores: {dados_da_noticia['autores']}")
    print(f"Data de Publicação: {dados_da_noticia['data_publicacao']}")
    print("\n--- TEXTO LIMPO DO ARTIGO ---")
    print(dados_da_noticia['texto_completo']) # Imprime o texto completo
    
    # AGORA VOCÊ PODE USAR ESTE TEXTO LIMPO NA API DO GOOGLE FACT CHECK
    # query_para_google = f"{dados_da_noticia['titulo']} {dados_da_noticia['texto_completo']}"