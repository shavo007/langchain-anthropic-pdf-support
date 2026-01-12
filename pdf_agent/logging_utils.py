"""Logging utilities for the PDF Agent.

Provides pretty-printed logging of agent execution flow with emojis.
"""

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

logger = logging.getLogger(__name__)


def log_agent_messages(messages: list[Any]) -> None:
    """Log all messages from agent execution including tool calls.

    Provides a pretty-printed view of the agent's execution flow
    with emojis for easy visual parsing.

    Args:
        messages: List of messages from agent response.
    """
    logger.info("")
    logger.info("╔══════════════════════════════════════════════════╗")
    logger.info("║           🤖 AGENT EXECUTION LOG                 ║")
    logger.info("╚══════════════════════════════════════════════════╝")

    for i, msg in enumerate(messages):
        msg_num = i + 1

        if isinstance(msg, HumanMessage):
            logger.info("")
            logger.info(f"┌─ [{msg_num}] 👤 Human Message ─────────────────────────")
            content = msg.content
            if isinstance(content, str):
                _log_content(content)
            else:
                logger.info(f"│  📎 Content type: {type(content).__name__}")
            logger.info("└" + "─" * 50)

        elif isinstance(msg, AIMessage):
            logger.info("")
            logger.info(f"┌─ [{msg_num}] 🧠 AI Message ───────────────────────────")

            # Log content if present
            if msg.content:
                content = str(msg.content)
                # Check if it's a tool call response (starts with [{'text':)
                if content.startswith("[{'text':") or content.startswith('[{"text":'):
                    logger.info("│  💭 Planning next action...")
                else:
                    _log_content(content)

            # Log tool calls if present
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                logger.info("│")
                logger.info(f"│  🔧 Tool Calls ({len(msg.tool_calls)}):")
                for tc in msg.tool_calls:
                    tool_name = tc.get("name", "unknown")
                    tool_args = tc.get("args", {})
                    # Truncate long args (like base64 data)
                    args_str = str(tool_args)
                    if len(args_str) > 80:
                        args_str = args_str[:80] + "..."
                    logger.info(f"│     ├─ 🛠️  {tool_name}")
                    logger.info(f"│     │     Args: {args_str}")

            logger.info("└" + "─" * 50)

        elif isinstance(msg, ToolMessage):
            logger.info("")
            logger.info(f"┌─ [{msg_num}] ⚡ Tool Result ──────────────────────────")
            tool_name = getattr(msg, "name", "unknown")
            content = str(msg.content)

            # Determine status emoji based on content
            is_error = content.startswith("Error") or content.startswith("Failed")
            status = "❌" if is_error else "✅"

            logger.info(f"│  🔧 Tool: {tool_name}")
            logger.info(f"│  {status} Status: {'Error' if is_error else 'Success'}")
            logger.info("│  📄 Result:")
            _log_content(content, prefix="│     ")
            logger.info("└" + "─" * 50)

    logger.info("")
    logger.info("═" * 52)
    logger.info("✨ Execution complete!")
    logger.info("═" * 52)


def _log_content(content: str, prefix: str = "│  ", max_length: int = 200) -> None:
    """Log content with proper formatting and truncation.

    Args:
        content: The content to log.
        prefix: Prefix for each line.
        max_length: Maximum length before truncation.
    """
    if len(content) > max_length:
        # Split into multiple lines if too long
        truncated = content[:max_length] + "..."
        lines = truncated.split("\n")
        for line in lines[:3]:  # Show first 3 lines max
            logger.info(f"{prefix}{line}")
        if len(lines) > 3:
            logger.info(f"{prefix}... (truncated)")
    else:
        lines = content.split("\n")
        for line in lines:
            logger.info(f"{prefix}{line}")


def log_header(title: str, use_agent: bool = True) -> None:
    """Log a pretty header for the demo.

    Args:
        title: The title to display.
        use_agent: Whether running in agent mode.
    """
    mode = "🤖 Agent Mode" if use_agent else "⚡ Direct Mode"
    logger.info("")
    logger.info("╔════════════════════════════════════════════════════════════╗")
    logger.info(f"║  📄 {title:^54} ║")
    logger.info(f"║  {mode:^56} ║")
    logger.info("╚════════════════════════════════════════════════════════════╝")


def log_analyzing(pdf_url: str) -> None:
    """Log that we're analyzing a PDF.

    Args:
        pdf_url: URL of the PDF being analyzed.
    """
    logger.info("")
    logger.info("┌────────────────────────────────────────────────────────────┐")
    logger.info("│  🔍 Analyzing PDF...                                       │")
    logger.info(f"│  📎 {pdf_url[:54]}{'...' if len(pdf_url) > 54 else '':<3} │")
    logger.info("└────────────────────────────────────────────────────────────┘")


def log_response(content: str) -> None:
    """Log the final agent/model response with pretty formatting.

    Args:
        content: The response content to display.
    """
    logger.info("")
    logger.info("╔════════════════════════════════════════════════════════════╗")
    logger.info("║  📋 RESPONSE                                               ║")
    logger.info("╠════════════════════════════════════════════════════════════╣")

    # Split content into lines and log each
    lines = content.split("\n")
    for line in lines:
        # Wrap long lines
        while len(line) > 58:
            logger.info(f"║  {line[:58]}")
            line = line[58:]
        logger.info(f"║  {line:<58} ║" if line.strip() else "║" + " " * 60 + "║")

    logger.info("╚════════════════════════════════════════════════════════════╝")


def log_error(error: str) -> None:
    """Log an error message.

    Args:
        error: The error message.
    """
    logger.error("")
    logger.error("╔════════════════════════════════════════════════════════════╗")
    logger.error("║  ❌ ERROR                                                   ║")
    logger.error("╠════════════════════════════════════════════════════════════╣")
    logger.error(f"║  {error[:58]:<58} ║")
    logger.error("╚════════════════════════════════════════════════════════════╝")


def log_model_capabilities(model_name: str, profile: dict[str, Any]) -> None:
    """Log the model's capabilities from its profile.

    Args:
        model_name: Name of the model.
        profile: The model's capability profile dictionary.
    """
    logger.info("")
    logger.info("╔════════════════════════════════════════════════════════════╗")
    logger.info(f"║  🧠 Model: {model_name:<48} ║")
    logger.info("╠════════════════════════════════════════════════════════════╣")
    logger.info("║  📊 Capabilities:                                          ║")

    # Token limits
    max_in = profile.get("max_input_tokens", "N/A")
    max_out = profile.get("max_output_tokens", "N/A")
    logger.info(f"║     max_input_tokens:  {str(max_in):<35} ║")
    logger.info(f"║     max_output_tokens: {str(max_out):<35} ║")

    # Key features
    features = [
        ("pdf_inputs", "PDF support"),
        ("image_inputs", "Image support"),
        ("tool_calling", "Tool calling"),
        ("reasoning_output", "Extended thinking"),
    ]

    logger.info("║  🔧 Features:                                              ║")
    for key, label in features:
        value = profile.get(key, False)
        status = "✓" if value else "✗"
        logger.info(f"║     {status} {label:<53} ║")

    logger.info("╚════════════════════════════════════════════════════════════╝")
