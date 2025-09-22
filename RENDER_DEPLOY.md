# Deploy no Render - Configuração para Selenium

Este documento explica como configurar o deploy no Render para que o link enricher funcione com Selenium.

## Opções de Configuração

### Opção 1: Usar Docker (Recomendado)

1. **Configure o serviço no Render para usar Docker:**
   - No painel do Render, vá em "New" > "Web Service"
   - Conecte seu repositório GitHub
   - **IMPORTANTE**: Selecione "Docker" como ambiente
   - O Render usará automaticamente o `Dockerfile` que criamos

2. **Variáveis de ambiente:**
   ```
   PORT=8000
   CONTAINER=true
   ```

3. **Build Command:** (deixar vazio - Docker cuida disso)

4. **Start Command:** (deixar vazio - Docker cuida disso)

### Opção 2: Usar Buildpacks

Se preferir não usar Docker, configure os buildpacks:

1. **No painel do Render:**
   - Vá em Settings > Build & Deploy
   - Adicione os seguintes buildpacks (nesta ordem):
     ```
     https://github.com/jontewks/puppeteer-heroku-buildpack.git
     https://github.com/heroku/heroku-buildpack-chromedriver.git
     https://github.com/heroku/heroku-buildpack-google-chrome.git
     https://github.com/heroku/heroku-buildpack-python.git
     ```

2. **Build Command:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Command:**
   ```bash
   gunicorn app.main:app --bind 0.0.0.0:$PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120
   ```

## Testando Localmente

### Com Docker:
```bash
# Build da imagem
docker build -t machines-are-smoking .

# Executar container
docker run -p 8000:8000 -e CONTAINER=true machines-are-smoking

# Ou usar docker-compose
docker-compose up --build
```

### Testar Selenium:
```bash
# Dentro do container
python test_selenium.py
```

## Verificações Importantes

### 1. Logs do Deploy
Verifique nos logs se o Chrome foi instalado corretamente:
```
Installing Google Chrome...
Chrome version: 120.x.x.x
Installing ChromeDriver...
ChromeDriver version: 120.x.x.x
```

### 2. Health Check
O endpoint `/health` deve responder com status 200.

### 3. Teste de Funcionamento
Após o deploy, teste uma URL que requer JavaScript:
```bash
curl -X POST "https://seu-app.onrender.com/api/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "Teste com link: https://example.com"}'
```

## Troubleshooting

### Chrome não instalado
- Verifique se está usando Docker ou os buildpacks corretos
- Confirme que o build não falhou na instalação do Chrome

### Selenium timeout
- Aumente o timeout no gunicorn (já configurado para 120s)
- Verifique se o Chrome está rodando em modo headless

### Erro de permissão
- O Dockerfile já cria um usuário não-root
- Se usando buildpacks, pode ser necessário ajustar permissões

### Memória insuficiente
- Render Free tier tem 512MB RAM
- Selenium + Chrome usa ~200-300MB
- Considere upgrade para plano pago se necessário

## Monitoramento

### Logs Importantes:
- `🚀 Selenium disponível - métodos pesados habilitados`
- `⚠️ Selenium não disponível - usando apenas métodos rápidos`
- `✅ Sucesso com selenium!`

### Métricas:
- Tempo de processamento de links
- Taxa de sucesso vs falha
- Qual método foi usado para cada URL

## Otimizações

### Para Render Free Tier:
1. Use apenas métodos rápidos (desabilitar Selenium)
2. Implemente cache para URLs já processadas
3. Limite o tamanho do conteúdo extraído

### Para Render Paid Tier:
1. Mantenha todos os métodos habilitados
2. Aumente workers para 4-8
3. Configure cache Redis se necessário

## Fallback Strategy

O sistema foi projetado para funcionar mesmo sem Selenium:

1. **Métodos rápidos** (sempre disponíveis):
   - Trafilatura
   - Newspaper3k
   - Readability
   - Requests + BeautifulSoup
   - Goose3 (para Twitter)

2. **Métodos pesados** (apenas se Selenium disponível):
   - Selenium básico
   - Selenium avançado (anti-detecção)

Isso garante que 80-90% das URLs funcionem mesmo sem JavaScript.
