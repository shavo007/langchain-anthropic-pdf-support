"""Tests for pdf_agent.core module."""

import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pdf_agent.core import (
    analyze_pdf_from_base64,
    analyze_pdf_from_file,
    analyze_pdf_from_url,
    download_and_analyze_pdf,
    get_model,
)


class TestGetModel:
    """Tests for get_model function."""

    def test_get_model_returns_chat_anthropic(self, mock_env_api_key: None) -> None:
        """Test that get_model returns a ChatAnthropic instance."""
        with patch("pdf_agent.core.ChatAnthropic") as mock_chat:
            mock_chat.return_value = MagicMock()
            model = get_model()
            assert model is not None
            mock_chat.assert_called_once()

    def test_get_model_uses_default_model_name(self, mock_env_api_key: None) -> None:
        """Test that get_model uses the default model name."""
        with patch("pdf_agent.core.ChatAnthropic") as mock_chat:
            mock_chat.return_value = MagicMock()
            get_model()
            call_kwargs = mock_chat.call_args[1]
            assert "claude-sonnet-4-5-20250929" in call_kwargs["model"]

    def test_get_model_accepts_custom_model_name(self, mock_env_api_key: None) -> None:
        """Test that get_model accepts a custom model name."""
        with patch("pdf_agent.core.ChatAnthropic") as mock_chat:
            mock_chat.return_value = MagicMock()
            get_model("custom-model")
            call_kwargs = mock_chat.call_args[1]
            assert call_kwargs["model"] == "custom-model"

    def test_get_model_raises_without_api_key(self, clear_env_api_key: None) -> None:
        """Test that get_model raises ValueError without API key."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            get_model()


class TestAnalyzePdfFromUrl:
    """Tests for analyze_pdf_from_url function."""

    def test_analyze_pdf_from_url_returns_content(
        self,
        mock_env_api_key: None,
        sample_pdf_url: str,
        mock_anthropic_response: MagicMock,
    ) -> None:
        """Test that analyze_pdf_from_url returns response content."""
        with patch("pdf_agent.core.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.invoke.return_value = mock_anthropic_response
            mock_get_model.return_value = mock_model

            result = analyze_pdf_from_url(sample_pdf_url, "What is this?")

            assert result == "This is a test response from Claude."
            mock_model.invoke.assert_called_once()

    def test_analyze_pdf_from_url_sends_correct_message_structure(
        self,
        mock_env_api_key: None,
        sample_pdf_url: str,
        mock_anthropic_response: MagicMock,
    ) -> None:
        """Test that the message structure is correct for URL-based PDF."""
        with patch("pdf_agent.core.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.invoke.return_value = mock_anthropic_response
            mock_get_model.return_value = mock_model

            analyze_pdf_from_url(sample_pdf_url, "Test question")

            call_args = mock_model.invoke.call_args[0][0]
            message = call_args[0]
            content = message.content

            assert len(content) == 2
            assert content[0]["type"] == "document"
            assert content[0]["source"]["type"] == "url"
            assert content[0]["source"]["url"] == sample_pdf_url
            assert content[1]["type"] == "text"
            assert content[1]["text"] == "Test question"


class TestAnalyzePdfFromBase64:
    """Tests for analyze_pdf_from_base64 function."""

    def test_analyze_pdf_from_base64_returns_content(
        self,
        mock_env_api_key: None,
        sample_pdf_base64: str,
        mock_anthropic_response: MagicMock,
    ) -> None:
        """Test that analyze_pdf_from_base64 returns response content."""
        with patch("pdf_agent.core.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.invoke.return_value = mock_anthropic_response
            mock_get_model.return_value = mock_model

            result = analyze_pdf_from_base64(sample_pdf_base64, "What is this?")

            assert result == "This is a test response from Claude."

    def test_analyze_pdf_from_base64_sends_correct_message_structure(
        self,
        mock_env_api_key: None,
        sample_pdf_base64: str,
        mock_anthropic_response: MagicMock,
    ) -> None:
        """Test that the message structure is correct for base64 PDF."""
        with patch("pdf_agent.core.get_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.invoke.return_value = mock_anthropic_response
            mock_get_model.return_value = mock_model

            analyze_pdf_from_base64(sample_pdf_base64, "Test question")

            call_args = mock_model.invoke.call_args[0][0]
            message = call_args[0]
            content = message.content

            assert len(content) == 2
            assert content[0]["type"] == "document"
            assert content[0]["source"]["type"] == "base64"
            assert content[0]["source"]["media_type"] == "application/pdf"
            assert content[0]["source"]["data"] == sample_pdf_base64


class TestAnalyzePdfFromFile:
    """Tests for analyze_pdf_from_file function."""

    def test_analyze_pdf_from_file_raises_for_missing_file(self, mock_env_api_key: None) -> None:
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            analyze_pdf_from_file("/nonexistent/path/to/file.pdf", "Question")

    def test_analyze_pdf_from_file_reads_and_encodes_file(
        self,
        mock_env_api_key: None,
        tmp_path: Path,
        mock_anthropic_response: MagicMock,
    ) -> None:
        """Test that file is read and base64 encoded."""
        # Create a temporary PDF file
        pdf_content = b"%PDF-1.0\ntest content"
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(pdf_content)

        with patch("pdf_agent.core.analyze_pdf_from_base64") as mock_analyze:
            mock_analyze.return_value = "Test response"

            result = analyze_pdf_from_file(str(pdf_file), "Question")

            assert result == "Test response"
            mock_analyze.assert_called_once()
            # Verify base64 encoding
            call_args = mock_analyze.call_args[0]
            decoded = base64.standard_b64decode(call_args[0])
            assert decoded == pdf_content


class TestDownloadAndAnalyzePdf:
    """Tests for download_and_analyze_pdf function."""

    def test_download_and_analyze_pdf_downloads_and_encodes(
        self,
        mock_env_api_key: None,
        sample_pdf_url: str,
    ) -> None:
        """Test that PDF is downloaded and base64 encoded."""
        pdf_content = b"%PDF-1.0\ndownloaded content"

        with (
            patch("pdf_agent.core.httpx.get") as mock_get,
            patch("pdf_agent.core.analyze_pdf_from_base64") as mock_analyze,
        ):
            mock_response = MagicMock()
            mock_response.content = pdf_content
            mock_get.return_value = mock_response
            mock_analyze.return_value = "Analysis result"

            result = download_and_analyze_pdf(sample_pdf_url, "Question")

            assert result == "Analysis result"
            mock_get.assert_called_once_with(sample_pdf_url, follow_redirects=True)
            # Verify base64 encoding
            call_args = mock_analyze.call_args[0]
            decoded = base64.standard_b64decode(call_args[0])
            assert decoded == pdf_content
