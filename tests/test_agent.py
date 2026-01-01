"""Tests for pdf_agent.agent module."""

from unittest.mock import MagicMock, patch

from pdf_agent.agent import create_pdf_agent
from pdf_agent.prompts import PDF_AGENT_SYSTEM_PROMPT


class TestCreatePdfAgent:
    """Tests for create_pdf_agent function."""

    def test_create_pdf_agent_returns_agent(self, mock_env_api_key: None) -> None:
        """Test that create_pdf_agent returns an agent instance."""
        with (
            patch("pdf_agent.agent.get_model") as mock_get_model,
            patch("pdf_agent.agent.create_agent") as mock_create_agent,
        ):
            mock_model = MagicMock()
            mock_get_model.return_value = mock_model
            mock_agent = MagicMock()
            mock_create_agent.return_value = mock_agent

            agent = create_pdf_agent()

            assert agent is mock_agent
            mock_get_model.assert_called_once()
            mock_create_agent.assert_called_once()

    def test_create_pdf_agent_uses_correct_system_prompt(self, mock_env_api_key: None) -> None:
        """Test that the agent is created with the PDF system prompt."""
        with (
            patch("pdf_agent.agent.get_model") as mock_get_model,
            patch("pdf_agent.agent.create_agent") as mock_create_agent,
        ):
            mock_model = MagicMock()
            mock_get_model.return_value = mock_model
            mock_create_agent.return_value = MagicMock()

            create_pdf_agent()

            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs["system_prompt"] == PDF_AGENT_SYSTEM_PROMPT

    def test_create_pdf_agent_includes_all_tools(self, mock_env_api_key: None) -> None:
        """Test that the agent is created with all PDF tools."""
        with (
            patch("pdf_agent.agent.get_model") as mock_get_model,
            patch("pdf_agent.agent.create_agent") as mock_create_agent,
        ):
            mock_model = MagicMock()
            mock_get_model.return_value = mock_model
            mock_create_agent.return_value = MagicMock()

            create_pdf_agent()

            call_kwargs = mock_create_agent.call_args[1]
            tools = call_kwargs["tools"]

            # Check that we have all 6 tools
            assert len(tools) == 6

            # Get tool names
            tool_names = [t.name for t in tools]
            assert "load_pdf_from_url" in tool_names
            assert "load_pdf_from_file" in tool_names
            assert "load_pdf_from_base64" in tool_names
            assert "analyze_loaded_pdf" in tool_names
            assert "list_loaded_pdfs" in tool_names
            assert "clear_pdf_cache" in tool_names


class TestSystemPrompt:
    """Tests for the system prompt."""

    def test_system_prompt_exists(self) -> None:
        """Test that the system prompt is defined."""
        assert PDF_AGENT_SYSTEM_PROMPT is not None
        assert len(PDF_AGENT_SYSTEM_PROMPT) > 0

    def test_system_prompt_mentions_pdf(self) -> None:
        """Test that the system prompt mentions PDF analysis."""
        assert "PDF" in PDF_AGENT_SYSTEM_PROMPT

    def test_system_prompt_mentions_tools(self) -> None:
        """Test that the system prompt mentions the available tools."""
        assert "load_pdf_from_url" in PDF_AGENT_SYSTEM_PROMPT
        assert "load_pdf_from_file" in PDF_AGENT_SYSTEM_PROMPT
        assert "analyze_loaded_pdf" in PDF_AGENT_SYSTEM_PROMPT

    def test_system_prompt_mentions_capabilities(self) -> None:
        """Test that the system prompt describes agent capabilities."""
        assert "Capabilities" in PDF_AGENT_SYSTEM_PROMPT
        assert "tables" in PDF_AGENT_SYSTEM_PROMPT.lower()
        assert "charts" in PDF_AGENT_SYSTEM_PROMPT.lower()
