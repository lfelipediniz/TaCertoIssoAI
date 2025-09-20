import logging
import sys
from app.core.config import get_settings

settings = get_settings()


def setup_logging():
    """
    Configure logging for the application
    """
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)