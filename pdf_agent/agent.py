"""PDF Agent creation and logging utilities.

This module provides the agent factory and utilities for logging
agent execution flow.
"""

import logging
from typing import TYPE_CHECKING, Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from .core import get_model
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

logger = logging.getLogger(__name__)

PDF_AGENT_SYSTEM_PROMPT = """You are an expert PDF Document Analyst agent powered by Claude. Your primary purpose is to help users analyze, understand, and extract information from PDF documents.

## Your Capabilities

You can:
- Load PDF documents from URLs, local file paths, or base64-encoded data
- Analyze text content, tables, charts, images, and visual elements within PDFs
- Answer specific questions about document contents
- Summarize documents or specific sections
- Extract structured data from PDFs
- Compare information across multiple loaded PDFs
- Identify key findings, themes, and important details

## How to Work with PDFs

1. **Loading PDFs**: Before analyzing a PDF, it must be loaded using one of:
   - `load_pdf_from_url` for PDFs accessible via URL
   - `load_pdf_from_file` for local PDF files
   - `load_pdf_from_base64` for base64-encoded PDF data (from APIs, databases, etc.)

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


def log_agent_messages(messages: list[Any]) -> None:
    """Log all messages from agent execution including tool calls.

    Args:
        messages: List of messages from agent response.
    """
    logger.info("=" * 50)
    logger.info("AGENT EXECUTION LOG")
    logger.info("=" * 50)

    for i, msg in enumerate(messages):
        msg_type = type(msg).__name__
        logger.info(f"\n[{i + 1}] {msg_type}")

        if isinstance(msg, HumanMessage):
            content = msg.content
            if isinstance(content, str):
                logger.info(f"    Content: {content[:200]}{'...' if len(content) > 200 else ''}")
            else:
                logger.info(f"    Content: {type(content)}")

        elif isinstance(msg, AIMessage):
            # Log content if present
            if msg.content:
                content = str(msg.content)
                logger.info(f"    Content: {content[:200]}{'...' if len(content) > 200 else ''}")

            # Log tool calls if present
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                logger.info(f"    Tool Calls ({len(msg.tool_calls)}):")
                for tc in msg.tool_calls:
                    tool_name = tc.get("name", "unknown")
                    tool_args = tc.get("args", {})
                    # Truncate long args (like base64 data)
                    args_str = str(tool_args)
                    if len(args_str) > 100:
                        args_str = args_str[:100] + "..."
                    logger.info(f"      - {tool_name}({args_str})")

        elif isinstance(msg, ToolMessage):
            tool_name = getattr(msg, "name", "unknown")
            content = str(msg.content)
            logger.info(f"    Tool: {tool_name}")
            logger.info(f"    Result: {content[:200]}{'...' if len(content) > 200 else ''}")

    logger.info("\n" + "=" * 50)
