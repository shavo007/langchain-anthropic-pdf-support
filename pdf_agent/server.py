"""Server entry point for PDF Agent API.

This module configures and exports the FastAPI application for uvicorn.

Usage:
    uvicorn pdf_agent.server:app --reload --host 0.0.0.0 --port 8000

Environment variables:
    PDF_AGENT_HOST: Host to bind to (default: 0.0.0.0)
    PDF_AGENT_PORT: Port to bind to (default: 8000)
"""

import logging
import os
import sys

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Log startup configuration
host = os.getenv("PDF_AGENT_HOST", "0.0.0.0")
port = os.getenv("PDF_AGENT_PORT", "8000")
logger.info("PDF Agent API configured for %s:%s", host, port)

# Import and export the app
from .api import api_app as app  # noqa: E402

__all__ = ["app"]
