"""PDF Agent creation.

This module provides the agent factory for creating
the PDF analysis agent.
"""

from typing import TYPE_CHECKING, Any

from langchain.agents import create_agent

from .core import get_model
from .prompts import PDF_AGENT_SYSTEM_PROMPT
from .tools import (
    analyze_loaded_pdf,
    clear_pdf_cache,
    list_loaded_pdfs,
    load_pdf_from_base64,
    load_pdf_from_file,
    load_pdf_from_url,
)

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


def create_pdf_agent() -> "CompiledStateGraph[Any, Any]":
    """Create a LangChain agent specialized for PDF document analysis.

    Returns:
        Configured agent instance with PDF analysis tools.
    """
    model = get_model()

    tools: list[Any] = [
        load_pdf_from_url,
        load_pdf_from_file,
        load_pdf_from_base64,
        analyze_loaded_pdf,
        list_loaded_pdfs,
        clear_pdf_cache,
    ]

    agent: CompiledStateGraph[Any, Any] = create_agent(
        model,
        tools=tools,
        system_prompt=PDF_AGENT_SYSTEM_PROMPT,
    )

    return agent
