"""Pytest fixtures and configuration for pdf_agent tests."""

import base64
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_anthropic_response() -> MagicMock:
    """Create a mock Anthropic API response."""
    mock_response = MagicMock()
    mock_response.content = "This is a test response from Claude."
    return mock_response


@pytest.fixture
def sample_pdf_base64() -> str:
    """Return a minimal valid PDF as base64.

    This is a tiny valid PDF that can be used for testing.
    """
    # Minimal PDF content
    pdf_content = b"""%PDF-1.0
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
164
%%EOF"""
    return base64.standard_b64encode(pdf_content).decode("utf-8")


@pytest.fixture
def sample_pdf_url() -> str:
    """Return a sample PDF URL for testing."""
    return "https://example.com/test.pdf"


@pytest.fixture
def mock_env_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set a mock ANTHROPIC_API_KEY environment variable."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key-12345")


@pytest.fixture
def clear_env_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear the ANTHROPIC_API_KEY environment variable."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
