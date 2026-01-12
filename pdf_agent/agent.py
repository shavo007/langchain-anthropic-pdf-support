"""PDF Agent creation.

This module provides the agent factory for creating
the PDF analysis agent.
"""

import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelRequest,
    ModelResponse,
    wrap_model_call,
)
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

logger = logging.getLogger(__name__)


@wrap_model_call
def log_request_metrics(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """Log request duration and request ID for Anthropic API calls."""
    start_time = time.perf_counter()

    response = handler(request)

    duration_ms = (time.perf_counter() - start_time) * 1000

    # Extract request_id and model from the response
    # ModelResponse.result is a list[BaseMessage] containing the AI response
    request_id = None
    model_name = None
    if response.result:
        last_message = response.result[-1]
        if isinstance(last_message, AIMessage):
            metadata = getattr(last_message, "response_metadata", {})
            request_id = metadata.get("id")
            model_name = metadata.get("model")

    logger.info(
        "Anthropic API call: model=%s, request_id=%s, duration=%.2fms",
        model_name,
        request_id,
        duration_ms,
    )

    return response


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


def create_pdf_agent(model_name: str | None = None) -> "CompiledStateGraph[Any, Any]":
    """Create a LangChain agent specialized for PDF document analysis.

    Args:
        model_name: Optional model name to use. Defaults to Claude Sonnet 4.5.

    Returns:
        Configured agent instance with PDF analysis tools.
    """
    model = get_model(model_name) if model_name else get_model()
    logger.info("Creating PDF agent with model: %s", model.model)

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
        middleware=[log_request_metrics, inject_pdf_content],
    )

    return agent
