from functools import lru_cache
import os


class Settings:
    def __init__(self):
        # App Config
        self.APP_NAME = os.getenv("APP_NAME", "Fake News Detector API")
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.PORT = int(os.getenv("PORT", 8000))

        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/fakenews")

        # Redis (for caching)
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

        # Evolution API
        self.EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "")
        self.EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")

        # AI Services
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

        # Security
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

        # Processing Limits
        self.MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", 10000))
        self.MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", 10))
        self.TEXT_PROCESSING_TIMEOUT = int(os.getenv("TEXT_PROCESSING_TIMEOUT", 5))
        self.IMAGE_PROCESSING_TIMEOUT = int(os.getenv("IMAGE_PROCESSING_TIMEOUT", 12))


@lru_cache()
def get_settings() -> Settings:
    return Settings()