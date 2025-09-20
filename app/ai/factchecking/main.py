import requests
import sys
import os

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from app.core.config import get_settings

# Obtém as configurações do sistema
settings = get_settings()

# O texto da notícia que o usuário enviou para o bot
texto_da_noticia = "vacina causa autismo e o lula tem um caso secreto sexual com o jair bolsonaro e pessoas com olhos azuis sao mais inteligentes"

# Montando a URL da API usando a chave do .env
url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?query={texto_da_noticia}&key={settings.GOOGLE_API_KEY}"

try:
    # Fazendo a requisição GET
    response = requests.get(url)
    response.raise_for_status()  # Lança um erro para respostas com status 4xx ou 5xx

    # Convertendo a resposta JSON em um dicionário Python
    data = response.json()

    # Verificando se encontramos alguma checagem ('claims')
    if 'claims' in data and data['claims']:
        print(f"Encontramos checagens para: '{texto_da_noticia}'\n")

        # Percorrendo a lista de checagens encontradas
        for claim in data['claims']:
            texto_checagem = claim.get('text', 'Texto da checagem não disponível')
            nome_checador = claim['claimReview'][0]['publisher']['name']
            avaliacao = claim['claimReview'][0]['textualRating']
            link_checagem = claim['claimReview'][0]['url']

            print("-----------------------------------------")
            print(f"🔎 Checado por: {nome_checador}")
            print(f"📰 Alegação: {texto_checagem}")
            print(f"⚖️ Avaliação: {avaliacao.upper()}")
            print(f"🔗 Link para a checagem: {link_checagem}")
            print("-----------------------------------------\n")

    else:
        print(f"Nenhuma checagem de fatos encontrada para: '{texto_da_noticia}'")
except requests.exceptions.HTTPError as http_err:
    print(f"Erro HTTP: {http_err}")
except Exception as err:
    print(f"Ocorreu um erro: {err}")