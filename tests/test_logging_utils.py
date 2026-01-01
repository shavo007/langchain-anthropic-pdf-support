"""Tests for pdf_agent.logging_utils module."""

import logging

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from pdf_agent.logging_utils import (
    log_agent_messages,
    log_analyzing,
    log_error,
    log_header,
    log_response,
)


@pytest.fixture
def caplog_info(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Set up caplog to capture INFO level logs."""
    caplog.set_level(logging.INFO)
    return caplog


class TestLogHeader:
    """Tests for log_header function."""

    def test_log_header_agent_mode(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test header logging in agent mode."""
        log_header("Test Title", use_agent=True)

        log_text = caplog_info.text
        assert "Test Title" in log_text
        assert "Agent Mode" in log_text

    def test_log_header_direct_mode(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test header logging in direct mode."""
        log_header("Test Title", use_agent=False)

        log_text = caplog_info.text
        assert "Test Title" in log_text
        assert "Direct Mode" in log_text


class TestLogAnalyzing:
    """Tests for log_analyzing function."""

    def test_log_analyzing_short_url(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test analyzing log with short URL."""
        log_analyzing("https://example.com/short.pdf")

        log_text = caplog_info.text
        assert "Analyzing PDF" in log_text
        assert "example.com" in log_text

    def test_log_analyzing_long_url(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test analyzing log with long URL (should be truncated)."""
        long_url = "https://example.com/" + "a" * 100 + ".pdf"
        log_analyzing(long_url)

        log_text = caplog_info.text
        assert "Analyzing PDF" in log_text
        assert "..." in log_text


class TestLogResponse:
    """Tests for log_response function."""

    def test_log_response_short_content(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test response logging with short content."""
        log_response("This is a short response.")

        log_text = caplog_info.text
        assert "RESPONSE" in log_text
        assert "short response" in log_text

    def test_log_response_multiline_content(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test response logging with multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        log_response(content)

        log_text = caplog_info.text
        assert "Line 1" in log_text
        assert "Line 2" in log_text
        assert "Line 3" in log_text


class TestLogError:
    """Tests for log_error function."""

    def test_log_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test error logging."""
        caplog.set_level(logging.ERROR)
        log_error("Something went wrong")

        log_text = caplog.text
        assert "ERROR" in log_text
        assert "Something went wrong" in log_text


class TestLogAgentMessages:
    """Tests for log_agent_messages function."""

    def test_log_agent_messages_human_message(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test logging of HumanMessage."""
        messages = [HumanMessage(content="Hello, agent!")]
        log_agent_messages(messages)

        log_text = caplog_info.text
        assert "Human Message" in log_text
        assert "Hello, agent!" in log_text

    def test_log_agent_messages_ai_message(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test logging of AIMessage."""
        messages = [AIMessage(content="Hello, human!")]
        log_agent_messages(messages)

        log_text = caplog_info.text
        assert "AI Message" in log_text
        assert "Hello, human!" in log_text

    def test_log_agent_messages_tool_message(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test logging of ToolMessage."""
        messages = [ToolMessage(content="Tool result", tool_call_id="123")]
        log_agent_messages(messages)

        log_text = caplog_info.text
        assert "Tool Result" in log_text
        assert "Tool result" in log_text

    def test_log_agent_messages_success_status(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test that successful tool results show success status."""
        messages = [ToolMessage(content="Successfully loaded", tool_call_id="123")]
        log_agent_messages(messages)

        log_text = caplog_info.text
        assert "Success" in log_text

    def test_log_agent_messages_error_status(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test that error tool results show error status."""
        messages = [ToolMessage(content="Error: Something failed", tool_call_id="123")]
        log_agent_messages(messages)

        log_text = caplog_info.text
        assert "Error" in log_text

    def test_log_agent_messages_ai_with_tool_calls(
        self, caplog_info: pytest.LogCaptureFixture
    ) -> None:
        """Test logging of AIMessage with tool calls."""
        ai_message = AIMessage(content="Planning...")
        ai_message.tool_calls = [{"name": "load_pdf_from_url", "args": {"url": "https://test.com"}}]
        messages = [ai_message]
        log_agent_messages(messages)

        log_text = caplog_info.text
        assert "Tool Calls" in log_text
        assert "load_pdf_from_url" in log_text

    def test_log_agent_messages_complete_flow(self, caplog_info: pytest.LogCaptureFixture) -> None:
        """Test logging of a complete agent message flow."""
        messages = [
            HumanMessage(content="Analyze this PDF"),
            AIMessage(content="I'll load the PDF"),
            ToolMessage(content="Successfully loaded", tool_call_id="1"),
            AIMessage(content="Here's the analysis"),
        ]
        log_agent_messages(messages)

        log_text = caplog_info.text
        assert "AGENT EXECUTION LOG" in log_text
        assert "Execution complete" in log_text
        assert "[1]" in log_text
        assert "[4]" in log_text
