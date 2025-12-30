"""
LangChain Agent with Anthropic Claude and PDF Support

This module demonstrates how to create a simple LangChain agent using Anthropic's
Claude model with native PDF support. It showcases three methods for providing PDFs:
1. URL-based PDF documents
2. Base64-encoded PDF documents
3. Local file PDF documents
"""

import base64
import os
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledGraph

# Load environment variables from .env file
load_dotenv()


def get_model(model_name: str = "claude-sonnet-4-5-20250929") -> ChatAnthropic:
    """Initialize the Anthropic Claude model.

    Args:
        model_name: The Claude model to use. Defaults to Claude Sonnet 4.5.

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

    return ChatAnthropic(model=model_name)


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
    return response.content


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
    return response.content


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


# ============================================================================
# Agent with PDF Analysis Tools
# ============================================================================

# Store for loaded PDFs (in-memory cache for the agent session)
_pdf_cache: dict[str, str] = {}


def load_pdf_from_url(url: str) -> str:
    """Load a PDF document from a URL for analysis.

    Downloads and caches the PDF so it can be analyzed multiple times
    without re-downloading.

    Args:
        url: Public URL pointing to the PDF document.

    Returns:
        Confirmation message with the PDF identifier.
    """
    try:
        response = httpx.get(url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        pdf_data = base64.standard_b64encode(response.content).decode("utf-8")

        # Use URL as identifier
        _pdf_cache[url] = pdf_data
        return f"Successfully loaded PDF from URL. Use this identifier for analysis: {url}"
    except httpx.TimeoutException:
        return f"Failed to load PDF: Request timed out for {url}"
    except httpx.HTTPStatusError as e:
        return f"Failed to load PDF: HTTP {e.response.status_code} error for {url}"
    except httpx.RequestError as e:
        return f"Failed to load PDF: {e}"


def load_pdf_from_file(file_path: str) -> str:
    """Load a PDF document from a local file for analysis.

    Reads and caches the PDF so it can be analyzed multiple times.

    Args:
        file_path: Path to the local PDF file.

    Returns:
        Confirmation message with the PDF identifier.
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


def analyze_loaded_pdf(pdf_identifier: str, question: str) -> str:
    """Analyze a previously loaded PDF document.

    Args:
        pdf_identifier: The URL or file path used when loading the PDF.
        question: The question to ask about the PDF content.

    Returns:
        Analysis results from Claude.
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
        return response.content
    except ValueError as e:
        return f"Error analyzing PDF: {e}"
    except httpx.RequestError as e:
        return f"Error analyzing PDF: API request failed - {e}"


def list_loaded_pdfs() -> str:
    """List all currently loaded PDFs.

    Returns:
        List of loaded PDF identifiers.
    """
    if not _pdf_cache:
        return (
            "No PDFs currently loaded. Use load_pdf_from_url or load_pdf_from_file to load a PDF."
        )

    pdf_list = "\n".join(f"  - {identifier}" for identifier in _pdf_cache)
    return f"Currently loaded PDFs:\n{pdf_list}"


def clear_pdf_cache() -> str:
    """Clear all loaded PDFs from memory.

    Returns:
        Confirmation message.
    """
    _pdf_cache.clear()
    return "All PDFs have been cleared from memory."


PDF_AGENT_SYSTEM_PROMPT = """You are an expert PDF Document Analyst agent powered by Claude. Your primary purpose is to help users analyze, understand, and extract information from PDF documents.

## Your Capabilities

You can:
- Load PDF documents from URLs or local file paths
- Analyze text content, tables, charts, images, and visual elements within PDFs
- Answer specific questions about document contents
- Summarize documents or specific sections
- Extract structured data from PDFs
- Compare information across multiple loaded PDFs
- Identify key findings, themes, and important details

## How to Work with PDFs

1. **Loading PDFs**: Before analyzing a PDF, it must be loaded using either:
   - `load_pdf_from_url` for PDFs accessible via URL
   - `load_pdf_from_file` for local PDF files

2. **Analyzing PDFs**: Once loaded, use `analyze_loaded_pdf` with the PDF identifier and your question

3. **Managing PDFs**: Use `list_loaded_pdfs` to see what's loaded, or `clear_pdf_cache` to free memory

## Best Practices

- Always confirm successful PDF loading before attempting analysis
- For complex documents, break down analysis into specific focused questions
- When comparing multiple documents, load all relevant PDFs first
- Provide clear, structured responses with relevant quotes or references from the document
- If a PDF fails to load or analyze, explain the issue and suggest alternatives

## Response Style

- Be thorough but concise
- Use bullet points and structured formatting for clarity
- Quote relevant passages when appropriate
- Clearly distinguish between information from the PDF and your own analysis
- If uncertain about something in the document, acknowledge the limitation"""


def create_pdf_agent() -> "CompiledGraph":
    """Create a LangChain agent specialized for PDF document analysis.

    Returns:
        Configured agent instance with PDF analysis tools.
    """
    model = get_model()

    tools = [
        load_pdf_from_url,
        load_pdf_from_file,
        analyze_loaded_pdf,
        list_loaded_pdfs,
        clear_pdf_cache,
    ]

    agent = create_agent(
        model,
        tools=tools,
        system_prompt=PDF_AGENT_SYSTEM_PROMPT,
    )

    return agent


# ============================================================================
# Demo / Main Entry Point
# ============================================================================


def main() -> None:
    """Run demonstration of PDF analysis capabilities."""
    print("=" * 60)
    print("LangChain + Anthropic Claude PDF Agent Demo")
    print("=" * 60)

    # Example PDF URL (Claude Model Card)
    sample_pdf_url = (
        "https://assets.anthropic.com/m/1cd9d098ac3e6467/"
        "original/Claude-3-Model-Card-October-Addendum.pdf"
    )

    print("\n[1] Direct PDF Analysis (without agent)...")
    print(f"    URL: {sample_pdf_url[:60]}...")
    print("-" * 60)

    try:
        result = analyze_pdf_from_url(
            url=sample_pdf_url,
            question="What are the key findings in this document? Please summarize in 3-5 bullet points.",
        )
        print(f"Response:\n{result}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("[2] PDF Analysis Agent Demo...")
    print("-" * 60)

    try:
        agent = create_pdf_agent()

        # Ask the agent to analyze a PDF
        print("\nAsking agent to load and analyze a PDF...")
        response = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Please load this PDF: {sample_pdf_url} "
                            "Then tell me what the document is about and list 3 key points."
                        ),
                    }
                ]
            }
        )

        # Extract the final message
        final_message = response["messages"][-1].content
        print(f"\nAgent Response:\n{final_message}")

    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
