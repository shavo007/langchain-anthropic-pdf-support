"""Core model initialization and direct PDF analysis functions.

This module provides the foundational model setup and direct PDF analysis
capabilities without requiring the agent framework.
"""

import base64
import os
from pathlib import Path
from typing import cast

import httpx
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

from pdf_agent.logging_utils import log_model_capabilities

# Default model - using Haiku for cost-effective demos
# Can be overridden via PDF_AGENT_MODEL environment variable
DEFAULT_MODEL = "claude-3-5-haiku-20241022"

# Higher-capability model for production use
SONNET_MODEL = "claude-sonnet-4-5-20250929"


def get_model(model_name: str | None = None) -> ChatAnthropic:
    """Initialize the Anthropic Claude model.

    Args:
        model_name: The Claude model to use. If not provided, uses the
            PDF_AGENT_MODEL environment variable, or defaults to Claude Sonnet 4.5.
            Set PDF_AGENT_MODEL=haiku to use the cheaper Haiku model for demos.

    Returns:
        Configured ChatAnthropic instance.

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable must be set. "
            "Get your API key from https://console.anthropic.com/"
        )

    # Determine model: explicit parameter > environment variable > default
    if model_name is None:
        env_model = os.environ.get("PDF_AGENT_MODEL", "").lower()
        if env_model == "sonnet":
            model_name = SONNET_MODEL
        elif env_model:
            model_name = env_model
        else:
            model_name = DEFAULT_MODEL

    model = ChatAnthropic(model=model_name)  # type: ignore[call-arg]
    if model.profile:
        log_model_capabilities(model_name, dict(model.profile))
    return model


def analyze_pdf_from_url(url: str, question: str) -> str:
    """Analyze a PDF document from a URL.

    This method uses Claude's native PDF support to process documents
    directly from URLs without downloading them first.

    Args:
        url: Public URL pointing to the PDF document.
        question: The question to ask about the PDF content.

    Returns:
        Claude's response about the PDF content.
    """
    model = get_model()

    message = HumanMessage(
        content=[
            {
                "type": "document",
                "source": {
                    "type": "url",
                    "url": url,
                },
            },
            {
                "type": "text",
                "text": question,
            },
        ]
    )

    response = model.invoke([message])
    return cast(str, response.content)


def analyze_pdf_from_base64(pdf_data: str, question: str) -> str:
    """Analyze a PDF document from base64-encoded data.

    This method is useful when you have PDF content in memory or
    need to process PDFs that aren't accessible via URL.

    Args:
        pdf_data: Base64-encoded PDF content.
        question: The question to ask about the PDF content.

    Returns:
        Claude's response about the PDF content.
    """
    model = get_model()

    message = HumanMessage(
        content=[
            {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": pdf_data,
                },
            },
            {
                "type": "text",
                "text": question,
            },
        ]
    )

    response = model.invoke([message])
    return cast(str, response.content)


def analyze_pdf_from_file(file_path: str | Path, question: str) -> str:
    """Analyze a PDF document from a local file.

    This is a convenience method that loads a local PDF file,
    encodes it to base64, and sends it to Claude for analysis.

    Args:
        file_path: Path to the local PDF file.
        question: The question to ask about the PDF content.

    Returns:
        Claude's response about the PDF content.

    Raises:
        FileNotFoundError: If the PDF file doesn't exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    with open(path, "rb") as f:
        pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

    return analyze_pdf_from_base64(pdf_data, question)


def download_and_analyze_pdf(url: str, question: str) -> str:
    """Download a PDF and analyze it using base64 encoding.

    This method downloads the PDF first, then sends it as base64.
    Useful when URL-based access doesn't work (e.g., authentication required).

    Args:
        url: URL to download the PDF from.
        question: The question to ask about the PDF content.

    Returns:
        Claude's response about the PDF content.
    """
    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()

    pdf_data = base64.standard_b64encode(response.content).decode("utf-8")
    return analyze_pdf_from_base64(pdf_data, question)
