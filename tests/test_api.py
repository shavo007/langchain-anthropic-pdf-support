"""Tests for pdf_agent.api module."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from pdf_agent.api import create_api_app, get_agent
from pdf_agent.tools import get_pdf_cache


@pytest.fixture(autouse=True)
def clear_cache_before_each_test() -> None:
    """Clear the PDF cache before each test."""
    get_pdf_cache().clear()


@pytest.fixture(autouse=True)
def reset_agent() -> None:
    """Reset the global agent before each test."""
    import pdf_agent.api as api_module

    api_module._agent = None


@pytest.fixture
def client() -> TestClient:
    """Create a test client with mocked agent."""
    with patch("pdf_agent.api.create_pdf_agent") as mock_create:
        mock_agent = MagicMock()
        mock_create.return_value = mock_agent
        app = create_api_app()
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def mock_agent() -> MagicMock:
    """Create a mock agent for testing."""
    mock = MagicMock()
    return mock


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "agent_initialized" in data
        assert "pdf_count" in data
        assert data["pdf_count"] == 0

    def test_health_check_with_pdfs(self, client: TestClient, sample_pdf_base64: str) -> None:
        """Test health check reflects loaded PDFs."""
        # Load a PDF first
        get_pdf_cache()["test_pdf"] = sample_pdf_base64

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["pdf_count"] == 1


class TestChatEndpoint:
    """Tests for /chat endpoint."""

    def test_chat_success(self, client: TestClient) -> None:
        """Test successful chat interaction."""
        from langchain_core.messages import AIMessage

        # Setup mock agent response
        with patch("pdf_agent.api.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.invoke.return_value = {
                "messages": [AIMessage(content="Hello! How can I help you?")]
            }
            mock_get_agent.return_value = mock_agent

            response = client.post("/chat", json={"message": "Hello"})

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"] == "Hello! How can I help you?"
        assert "pdf_count" in data

    def test_chat_empty_message(self, client: TestClient) -> None:
        """Test chat with empty message."""
        from langchain_core.messages import AIMessage

        with patch("pdf_agent.api.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.invoke.return_value = {
                "messages": [AIMessage(content="I need more information.")]
            }
            mock_get_agent.return_value = mock_agent

            response = client.post("/chat", json={"message": ""})

        assert response.status_code == 200

    def test_chat_agent_error(self, client: TestClient) -> None:
        """Test handling of agent errors."""
        with patch("pdf_agent.api.get_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.invoke.side_effect = Exception("Agent error")
            mock_get_agent.return_value = mock_agent

            response = client.post("/chat", json={"message": "Hello"})

        assert response.status_code == 500
        assert "Agent error" in response.json()["detail"]


class TestPDFListEndpoint:
    """Tests for GET /pdfs endpoint."""

    def test_list_pdfs_empty(self, client: TestClient) -> None:
        """Test listing PDFs when none are loaded."""
        response = client.get("/pdfs")

        assert response.status_code == 200
        data = response.json()
        assert data["pdfs"] == []
        assert data["count"] == 0

    def test_list_pdfs_with_pdfs(self, client: TestClient, sample_pdf_base64: str) -> None:
        """Test listing PDFs when some are loaded."""
        cache = get_pdf_cache()
        cache["pdf1"] = sample_pdf_base64
        cache["pdf2"] = sample_pdf_base64

        response = client.get("/pdfs")

        assert response.status_code == 200
        data = response.json()
        assert len(data["pdfs"]) == 2
        assert "pdf1" in data["pdfs"]
        assert "pdf2" in data["pdfs"]
        assert data["count"] == 2


class TestLoadPDFEndpoint:
    """Tests for POST /pdfs endpoint."""

    def test_load_pdf_from_url(self, client: TestClient) -> None:
        """Test loading PDF from URL."""
        with patch("pdf_agent.api.load_pdf_from_url") as mock_load:
            mock_load.invoke.return_value = "Successfully loaded PDF from URL"

            response = client.post("/pdfs", json={"url": "https://example.com/test.pdf"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Successfully" in data["message"]

    def test_load_pdf_from_base64(self, client: TestClient, sample_pdf_base64: str) -> None:
        """Test loading PDF from base64 data."""
        with patch("pdf_agent.api.load_pdf_from_base64") as mock_load:
            mock_load.invoke.return_value = "Successfully loaded PDF from base64 data"

            response = client.post(
                "/pdfs",
                json={"base64_data": sample_pdf_base64, "identifier": "my_pdf"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["identifier"] == "my_pdf"

    def test_load_pdf_both_url_and_base64(self, client: TestClient, sample_pdf_base64: str) -> None:
        """Test error when both URL and base64 are provided."""
        response = client.post(
            "/pdfs",
            json={"url": "https://example.com/test.pdf", "base64_data": sample_pdf_base64},
        )

        assert response.status_code == 400
        assert "not both" in response.json()["detail"]

    def test_load_pdf_neither_url_nor_base64(self, client: TestClient) -> None:
        """Test error when neither URL nor base64 is provided."""
        response = client.post("/pdfs", json={})

        assert response.status_code == 400
        assert "Must provide" in response.json()["detail"]


class TestClearPDFsEndpoint:
    """Tests for DELETE /pdfs endpoint."""

    def test_clear_all_pdfs(self, client: TestClient, sample_pdf_base64: str) -> None:
        """Test clearing all PDFs."""
        cache = get_pdf_cache()
        cache["pdf1"] = sample_pdf_base64
        cache["pdf2"] = sample_pdf_base64

        response = client.delete("/pdfs")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "2" in data["message"]
        assert len(get_pdf_cache()) == 0

    def test_clear_specific_pdf(self, client: TestClient, sample_pdf_base64: str) -> None:
        """Test clearing a specific PDF."""
        cache = get_pdf_cache()
        cache["pdf1"] = sample_pdf_base64
        cache["pdf2"] = sample_pdf_base64

        response = client.delete("/pdfs/pdf1")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["identifier"] == "pdf1"
        assert "pdf1" not in get_pdf_cache()
        assert "pdf2" in get_pdf_cache()

    def test_clear_nonexistent_pdf(self, client: TestClient) -> None:
        """Test clearing a PDF that doesn't exist."""
        response = client.delete("/pdfs/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_clear_pdf_with_url_identifier(
        self, client: TestClient, sample_pdf_base64: str
    ) -> None:
        """Test clearing a PDF with URL-like identifier."""
        url_id = "https://example.com/test.pdf"
        cache = get_pdf_cache()
        cache[url_id] = sample_pdf_base64

        response = client.delete(f"/pdfs/{url_id}")

        assert response.status_code == 200
        assert url_id not in get_pdf_cache()


class TestGetAgent:
    """Tests for get_agent function."""

    def test_get_agent_creates_singleton(self) -> None:
        """Test that get_agent creates a singleton."""
        import pdf_agent.api as api_module

        api_module._agent = None

        with patch("pdf_agent.api.create_pdf_agent") as mock_create:
            mock_agent = MagicMock()
            mock_create.return_value = mock_agent

            agent1 = get_agent()
            agent2 = get_agent()

            assert agent1 is agent2
            mock_create.assert_called_once()
