# Fake News Detector API

A WhatsApp chatbot backend for fact-checking and claim verification using LangChain and OpenAI.

## Overview

This FastAPI application provides a comprehensive fact-checking pipeline that:
- Extracts verifiable claims from Portuguese text
- Retrieves evidence from trusted sources
- Uses LLM adjudication to provide verdicts with citations
- Supports text-only, image (OCR), and multimodal analysis

## Architecture

**4-Step Pipeline:**
1. **Claim Extraction** - OpenAI LLM extracts verifiable claims from user input
2. **Evidence Retrieval** - Google Fact-Check API and other sources gather evidence
3. **LLM Adjudication** - Structured analysis produces verdicts with citations
4. **Response Formatting** - Clean API responses for WhatsApp integration

## Requirements

- Python 3.11+
- OpenAI API Key
- Google Fact-Check API Key (optional)

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd MachinesAreSmoking
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
```env
# AI Services
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# App Configuration
DEBUG=False
PORT=8000
```

## Running the Application

**Development:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production:**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Access the API:**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Root: http://localhost:8000/

## API Endpoints

### Core Endpoints

#### `POST /api/text`
Analyze text-only messages for fact-checking.

**Request:**
```json
{
  "text": "The government announced new policies yesterday"
}
```

**Response:**
```json
{
  "message_id": "fc_123456",
  "verdict": "true",
  "rationale": "Government announcement confirmed by official sources",
  "citations": [
    {
      "url": "https://example.com/source",
      "title": "Official Government Statement",
      "publisher": "Government Portal",
      "quoted": "New policies were announced on the specified date"
    }
  ],
  "processing_time_ms": 3500
}
```

#### `POST /api/images`
Analyze images using OCR for fact-checking.

**Request (multipart/form-data):**
- `file`: Image file
- `chatId`: Optional chat identifier

**Response:** Same as `/api/text`

#### `POST /api/multimodal`
Analyze messages with both text and images.

**Request (multipart/form-data):**
- `text`: Optional text content
- `file`: Optional image file
- `chatId`: Optional chat identifier

**Response:** Same as `/api/text`

### Test Endpoints

#### `GET /api/test-adjudicator`
Test the LLM adjudication step with sample data.

#### `GET /api/test-evidence-retrieval`
Test evidence retrieval using Google Fact-Check API.

### System Endpoints

#### `GET /`
API information and version.

#### `GET /health`
Health check endpoint.

## Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── api/
│   └── endpoints/       # API route handlers
│       ├── text.py      # Text analysis endpoints
│       ├── images.py    # Image analysis endpoints
│       └── multimodal.py # Combined analysis endpoints
├── core/
│   └── config.py        # Configuration management
├── models/
│   ├── schemas.py       # API request/response models
│   └── factchecking.py  # Pipeline data models
└── ai/
    ├── claim_extractor.py    # Step 1: Extract claims from text
    ├── retrieval.py          # Step 2: Evidence retrieval
    ├── adjudicator.py        # Step 3: LLM fact-checking
    └── pipeline.py           # Complete pipeline orchestration
```

## Development

**Run tests:**
```bash
# Test individual components
curl -X GET "http://localhost:8000/api/test-adjudicator"
curl -X GET "http://localhost:8000/api/test-evidence-retrieval"

# Test full pipeline
curl -X POST "http://localhost:8000/api/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "A vacina X causa infertilidade em mulheres"}'
```

**View API documentation:**
Visit http://localhost:8000/docs for interactive Swagger documentation.

## Deployment

### Render.com (Recomendado)

1. **Connect Repository:**
   - Go to [render.com](https://render.com)
   - Create new Web Service
   - Connect your GitHub repository

2. **Configure Build Settings:**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
   ```

3. **Set Environment Variables:**
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   DEBUG=False
   PORT=8000
   SECRET_KEY=your-secret-key-here
   ```

4. **Deploy:**
   - Render will automatically build and deploy from your main branch
   - Your API will be available at: `https://your-app-name.onrender.com`

### Heroku:
```bash
# Uses Procfile and runtime.txt
git push heroku main
```

### Railway:
```bash
# Uses gunicorn command from Procfile
# Set environment variables in platform dashboard
```

## Features

- ✅ **Portuguese Language Support** - Optimized for pt-BR content
- ✅ **Structured LLM Outputs** - Type-safe Pydantic models throughout
- ✅ **Async-First Design** - High-performance async operations
- ✅ **Error Handling** - Graceful fallbacks and detailed error messages
- ✅ **Evidence Citations** - Transparent source attribution
- ✅ **Multi-Step Pipeline** - Modular claim extraction and verification
- 🚧 **OCR Support** - Image text extraction (planned)
- 🚧 **WhatsApp Integration** - Evolution API webhook support (planned)

## Contributing

1. Follow the existing code structure and patterns
2. Use async/await for all I/O operations
3. Maintain type hints and Pydantic models
4. Test endpoints using the `/test-*` endpoints
5. Update documentation for new features