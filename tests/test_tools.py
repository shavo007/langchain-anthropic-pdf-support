"""Tests for pdf_agent.tools module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pdf_agent.tools import (
    clear_pdf_cache,
    get_pdf_cache,
    get_pdf_content,
    list_loaded_pdfs,
    load_pdf_from_base64,
    load_pdf_from_file,
    load_pdf_from_url,
)


@pytest.fixture(autouse=True)
def clear_cache_before_each_test() -> None:
    """Clear the PDF cache before each test."""
    get_pdf_cache().clear()


class TestLoadPdfFromUrl:
    """Tests for load_pdf_from_url tool."""

    def test_load_pdf_from_url_success(self, sample_pdf_url: str) -> None:
        """Test successful PDF loading from URL."""
        pdf_content = b"%PDF-1.0\ntest content"

        with patch("pdf_agent.tools.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = pdf_content
            mock_get.return_value = mock_response

            result = load_pdf_from_url.invoke({"url": sample_pdf_url})

            assert "Successfully loaded PDF" in result
            assert sample_pdf_url in result
            assert sample_pdf_url in get_pdf_cache()

    def test_load_pdf_from_url_timeout(self, sample_pdf_url: str) -> None:
        """Test handling of timeout errors."""
        import httpx

        with patch("pdf_agent.tools.httpx.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Timeout")

            result = load_pdf_from_url.invoke({"url": sample_pdf_url})

            assert "Failed to load PDF" in result
            assert "timed out" in result

    def test_load_pdf_from_url_http_error(self, sample_pdf_url: str) -> None:
        """Test handling of HTTP errors."""
        import httpx

        with patch("pdf_agent.tools.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.side_effect = httpx.HTTPStatusError(
                "Not found", request=MagicMock(), response=mock_response
            )

            result = load_pdf_from_url.invoke({"url": sample_pdf_url})

            assert "Failed to load PDF" in result
            assert "404" in result


class TestLoadPdfFromFile:
    """Tests for load_pdf_from_file tool."""

    def test_load_pdf_from_file_success(self, tmp_path: Path) -> None:
        """Test successful PDF loading from file."""
        pdf_content = b"%PDF-1.0\ntest content"
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(pdf_content)

        result = load_pdf_from_file.invoke({"file_path": str(pdf_file)})

        assert "Successfully loaded PDF" in result
        assert str(pdf_file) in get_pdf_cache()

    def test_load_pdf_from_file_not_found(self) -> None:
        """Test handling of missing file."""
        result = load_pdf_from_file.invoke({"file_path": "/nonexistent/file.pdf"})

        assert "Error: File not found" in result

    def test_load_pdf_from_file_permission_error(self, tmp_path: Path) -> None:
        """Test handling of permission errors."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.0")

        with patch("builtins.open") as mock_open:
            mock_open.side_effect = PermissionError("Permission denied")

            result = load_pdf_from_file.invoke({"file_path": str(pdf_file)})

            assert "Failed to load PDF" in result
            assert "Permission denied" in result


class TestLoadPdfFromBase64:
    """Tests for load_pdf_from_base64 tool."""

    def test_load_pdf_from_base64_success(self, sample_pdf_base64: str) -> None:
        """Test successful PDF loading from base64."""
        result = load_pdf_from_base64.invoke(
            {"pdf_base64": sample_pdf_base64, "identifier": "test_pdf"}
        )

        assert "Successfully loaded PDF" in result
        assert "test_pdf" in result
        assert "test_pdf" in get_pdf_cache()

    def test_load_pdf_from_base64_default_identifier(self, sample_pdf_base64: str) -> None:
        """Test that default identifier is used when not provided."""
        result = load_pdf_from_base64.invoke({"pdf_base64": sample_pdf_base64})

        assert "base64_pdf" in result
        assert "base64_pdf" in get_pdf_cache()

    def test_load_pdf_from_base64_invalid_encoding(self) -> None:
        """Test handling of invalid base64 encoding."""
        result = load_pdf_from_base64.invoke(
            {"pdf_base64": "not-valid-base64!!!", "identifier": "test"}
        )

        assert "Failed to load PDF" in result
        assert "Invalid base64" in result


class TestGetPdfContent:
    """Tests for get_pdf_content function."""

    def test_get_pdf_content_success(self, sample_pdf_base64: str) -> None:
        """Test retrieving PDF content from cache."""
        get_pdf_cache()["test_pdf"] = sample_pdf_base64

        result = get_pdf_content("test_pdf")

        assert result is not None
        assert result["data"] == sample_pdf_base64
        assert result["identifier"] == "test_pdf"

    def test_get_pdf_content_not_found(self) -> None:
        """Test that None is returned for non-existent PDF."""
        result = get_pdf_content("nonexistent")

        assert result is None


class TestListLoadedPdfs:
    """Tests for list_loaded_pdfs tool."""

    def test_list_loaded_pdfs_empty(self) -> None:
        """Test listing when no PDFs are loaded."""
        result = list_loaded_pdfs.invoke({})

        assert "No PDFs currently loaded" in result

    def test_list_loaded_pdfs_with_pdfs(self, sample_pdf_base64: str) -> None:
        """Test listing with loaded PDFs."""
        cache = get_pdf_cache()
        cache["pdf1"] = sample_pdf_base64
        cache["pdf2"] = sample_pdf_base64

        result = list_loaded_pdfs.invoke({})

        assert "Currently loaded PDFs" in result
        assert "pdf1" in result
        assert "pdf2" in result


class TestClearPdfCache:
    """Tests for clear_pdf_cache tool."""

    def test_clear_pdf_cache(self, sample_pdf_base64: str) -> None:
        """Test clearing the PDF cache."""
        cache = get_pdf_cache()
        cache["pdf1"] = sample_pdf_base64
        cache["pdf2"] = sample_pdf_base64

        result = clear_pdf_cache.invoke({})

        assert "cleared" in result.lower()
        assert len(get_pdf_cache()) == 0
