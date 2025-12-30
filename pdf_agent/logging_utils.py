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
