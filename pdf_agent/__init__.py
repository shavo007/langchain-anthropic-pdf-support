"""LangChain PDF Agent with Anthropic Claude.

A LangChain agent specialized for PDF document analysis using
Anthropic's Claude model with native PDF support.

Example usage:
    from pdf_agent import create_pdf_agent, log_agent_messages

    agent = create_pdf_agent()
    response = agent.invoke({
        "messages": [{
            "role": "user",
            "content": "Load and analyze this PDF: https://example.com/doc.pdf"
        }]
    })
    log_agent_messages(response["messages"])
"""

from .agent import create_pdf_agent
from .core import (
    analyze_pdf_from_base64,
    analyze_pdf_from_file,
    analyze_pdf_from_url,
    download_and_analyze_pdf,
    get_model,
)
from .logging_utils import log_agent_messages
from .prompts import PDF_AGENT_SYSTEM_PROMPT
from .tools import (
    analyze_loaded_pdf,
    clear_pdf_cache,
    get_pdf_cache,
    list_loaded_pdfs,
    load_pdf_from_base64,
    load_pdf_from_file,
    load_pdf_from_url,
)

__all__ = [
    # Agent
    "create_pdf_agent",
    "log_agent_messages",
    "PDF_AGENT_SYSTEM_PROMPT",
    # Direct analysis
    "analyze_pdf_from_url",
    "analyze_pdf_from_base64",
    "analyze_pdf_from_file",
    "download_and_analyze_pdf",
    "get_model",
    # Tools (for advanced usage)
    "load_pdf_from_url",
    "load_pdf_from_file",
    "load_pdf_from_base64",
    "analyze_loaded_pdf",
    "list_loaded_pdfs",
    "clear_pdf_cache",
    "get_pdf_cache",
]
