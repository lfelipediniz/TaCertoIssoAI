from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class TextRequest:
    text: str
    chatId: Optional[str] = None


@dataclass
class ImageRequest:
    chatId: Optional[str] = None


@dataclass
class MultimodalRequest:
    chatId: Optional[str] = None
    text: Optional[str] = None


@dataclass
class Citation:
    title: str
    source: str
    url: str
    snippet: str
    published_at: Optional[datetime] = None


@dataclass
class AnalysisResponse:
    message_id: str
    verdict: str  # "true", "false", "misleading", "unverifiable"
    confidence: float
    rationale: str
    citations: List[Citation]
    processing_time_ms: int


@dataclass
class HealthResponse:
    status: str
    timestamp: datetime