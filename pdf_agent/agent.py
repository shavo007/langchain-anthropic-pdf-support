"""PDF Agent creation.

This module provides the agent factory for creating
the PDF analysis agent.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call
from langchain_core.messages import AIMessage, HumanMessage

from .core import get_model
from .prompts import PDF_AGENT_SYSTEM_PROMPT
from .tools import (
    clear_pdf_cache,
    get_pdf_cache,
    list_loaded_pdfs,
    load_pdf_from_base64,
    load_pdf_from_file,
    load_pdf_from_url,
)

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph


@wrap_model_call
def inject_pdf_content(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Inject loaded PDF content into the messages before sending to the LLM.

    This middleware checks if PDFs are loaded in the cache and injects them
    as multimodal document content, allowing the agent to analyze PDFs directly
    without a separate tool call to the LLM.
    """
    pdf_cache = get_pdf_cache()

    if pdf_cache:
        # Build PDF content blocks for multimodal message
        pdf_content: list[dict[str, Any]] = []
        for identifier, pdf_data in pdf_cache.items():
            pdf_content.append(
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data,
                    },
                    "cache_control": {"type": "ephemeral"},
                }
            )
            pdf_content.append(
                {
                    "type": "text",
                    "text": f"[PDF loaded with identifier: {identifier}]",
                }
            )

        # Inject PDF content and acknowledgment before the conversation
        injected_messages = [
            HumanMessage(content=pdf_content),  # type: ignore[arg-type]
            AIMessage(
                content="I have the PDF document(s) loaded and can now directly "
                "answer questions about the content."
            ),
            *request.messages,
        ]
        request = request.override(messages=injected_messages)

    return handler(request)


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
        list_loaded_pdfs,
        clear_pdf_cache,
    ]

    agent: CompiledStateGraph[Any, Any] = create_agent(
        model,
        tools=tools,
        system_prompt=PDF_AGENT_SYSTEM_PROMPT,
        middleware=[inject_pdf_content],
    )

    return agent
