from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import text, images, multimodal
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Fake News Detector API",
    description="WhatsApp chatbot backend for fact-checking and claim verification",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(text.router, prefix="/api", tags=["text"])
app.include_router(images.router, prefix="/api", tags=["images"])
app.include_router(multimodal.router, prefix="/api", tags=["multimodal"])


@app.get("/")
async def root():
    return {"message": "Fake News Detector API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}