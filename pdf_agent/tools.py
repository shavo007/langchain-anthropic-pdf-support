"""Agent tools for PDF document loading and analysis.

This module defines the LangChain tools that the PDF agent uses to
load, cache, and analyze PDF documents.
"""

import base64
from pathlib import Path
from typing import cast

import httpx
from langchain.tools import tool
from langchain_core.messages import HumanMessage

from .core import get_model

# In-memory cache for loaded PDFs (shared across agent sessions)
_pdf_cache: dict[str, str] = {}


def get_pdf_cache() -> dict[str, str]:
    """Get the PDF cache dictionary.

    Returns:
        The shared PDF cache dictionary.
    """
    return _pdf_cache


@tool(parse_docstring=True)
def load_pdf_from_url(url: str) -> str:
    """Load a PDF document from a URL for analysis.

    Downloads and caches the PDF so it can be analyzed multiple times
    without re-downloading.

    Args:
        url: Public URL pointing to the PDF document.
    """
    try:
        response = httpx.get(url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        pdf_data = base64.standard_b64encode(response.content).decode("utf-8")

        _pdf_cache[url] = pdf_data
        return f"Successfully loaded PDF from URL. Use this identifier for analysis: {url}"
    except httpx.TimeoutException:
        return f"Failed to load PDF: Request timed out for {url}"
    except httpx.HTTPStatusError as e:
        return f"Failed to load PDF: HTTP {e.response.status_code} error for {url}"
    except httpx.RequestError as e:
        return f"Failed to load PDF: {e}"


@tool(parse_docstring=True)
def load_pdf_from_file(file_path: str) -> str:
    """Load a PDF document from a local file for analysis.

    Reads and caches the PDF so it can be analyzed multiple times.

    Args:
        file_path: Path to the local PDF file.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File not found at {file_path}"

        with open(path, "rb") as f:
            pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

        _pdf_cache[file_path] = pdf_data
        return f"Successfully loaded PDF from file. Use this identifier for analysis: {file_path}"
    except PermissionError:
        return f"Failed to load PDF: Permission denied for {file_path}"
    except OSError as e:
        return f"Failed to load PDF: {e}"


@tool(parse_docstring=True)
def load_pdf_from_base64(pdf_base64: str, identifier: str = "base64_pdf") -> str:
    """Load a PDF document from base64-encoded data for analysis.

    Caches the PDF so it can be analyzed multiple times. Useful when receiving
    PDFs from APIs, databases, or other sources that provide base64-encoded data.

    Args:
        pdf_base64: Base64-encoded PDF content.
        identifier: Optional name to identify this PDF. Defaults to 'base64_pdf'.
    """
    try:
        # Validate base64 data by attempting to decode it
        base64.standard_b64decode(pdf_base64)

        _pdf_cache[identifier] = pdf_base64
        return f"Successfully loaded PDF from base64 data. Use this identifier for analysis: {identifier}"
    except ValueError:
        return "Failed to load PDF: Invalid base64 encoding"


@tool(parse_docstring=True)
def analyze_loaded_pdf(pdf_identifier: str, question: str) -> str:
    """Analyze a previously loaded PDF document.

    Args:
        pdf_identifier: The identifier (URL, file path, or custom name) used when loading the PDF.
        question: The question to ask about the PDF content.
    """
    if pdf_identifier not in _pdf_cache:
        return f"Error: No PDF loaded with identifier '{pdf_identifier}'. Please load the PDF first using load_pdf_from_url or load_pdf_from_file."

    try:
        model = get_model()
        pdf_data = _pdf_cache[pdf_identifier]

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
    except ValueError as e:
        return f"Error analyzing PDF: {e}"
    except httpx.RequestError as e:
        return f"Error analyzing PDF: API request failed - {e}"


@tool
def list_loaded_pdfs() -> str:
    """List all currently loaded PDFs and their identifiers."""
    if not _pdf_cache:
        return (
            "No PDFs currently loaded. Use load_pdf_from_url or load_pdf_from_file to load a PDF."
        )

    pdf_list = "\n".join(f"  - {identifier}" for identifier in _pdf_cache)
    return f"Currently loaded PDFs:\n{pdf_list}"


@tool
def clear_pdf_cache() -> str:
    """Clear all loaded PDFs from memory to free up resources."""
    _pdf_cache.clear()
    return "All PDFs have been cleared from memory."
