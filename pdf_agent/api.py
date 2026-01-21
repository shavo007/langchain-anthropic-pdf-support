"""FastAPI application for PDF Agent.

This module provides a REST API to interact with the PDF analysis agent,
allowing chat-style interactions and PDF management via HTTP endpoints.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from .agent import create_pdf_agent
from .tools import get_pdf_cache, load_pdf_from_base64, load_pdf_from_url

logger = logging.getLogger(__name__)

# Global agent instance (lazy initialized)
_agent: Any = None


def get_agent() -> Any:
    """Get or create the singleton agent instance."""
    global _agent
    if _agent is None:
        logger.info("Initializing PDF agent...")
        _agent = create_pdf_agent()
        logger.info("PDF agent initialized successfully")
    return _agent


# Pydantic models for request/response
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., description="User message to send to the agent")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    response: str = Field(..., description="Agent's response message")
    pdf_count: int = Field(..., description="Number of PDFs currently loaded")


class PDFListResponse(BaseModel):
    """Response model for listing PDFs."""

    pdfs: list[str] = Field(..., description="List of loaded PDF identifiers")
    count: int = Field(..., description="Number of PDFs currently loaded")


class LoadPDFRequest(BaseModel):
    """Request model for loading a PDF."""

    url: str | None = Field(None, description="URL to load PDF from")
    base64_data: str | None = Field(None, description="Base64-encoded PDF data")
    identifier: str | None = Field(None, description="Optional identifier for base64 PDFs")


class LoadPDFResponse(BaseModel):
    """Response model for PDF loading."""

    success: bool = Field(..., description="Whether the PDF was loaded successfully")
    message: str = Field(..., description="Result message")
    identifier: str | None = Field(None, description="Identifier for the loaded PDF")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    agent_initialized: bool = Field(..., description="Whether agent is initialized")
    pdf_count: int = Field(..., description="Number of PDFs currently loaded")


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Application lifespan handler for startup/shutdown."""
    # Startup: log ready (agent is lazily initialized on first chat request)
    logger.info("Starting PDF Agent API...")
    logger.info("Agent will be initialized on first /chat request")
    yield
    # Shutdown: cleanup
    logger.info("Shutting down PDF Agent API...")


def create_api_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="PDF Agent API",
        description="REST API for interacting with the PDF analysis agent",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check() -> HealthResponse:
        """Check the health status of the API."""
        pdf_cache = get_pdf_cache()
        return HealthResponse(
            status="healthy",
            agent_initialized=_agent is not None,
            pdf_count=len(pdf_cache),
        )

    @app.post("/chat", response_model=ChatResponse, tags=["Chat"])
    async def chat(request: ChatRequest) -> ChatResponse:
        """Send a message to the PDF agent and get a response."""
        try:
            agent = get_agent()
            result = agent.invoke({"messages": [HumanMessage(content=request.message)]})

            # Extract the last AI message from the response
            messages = result.get("messages", [])
            response_text = ""
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    response_text = str(msg.content)
                    break

            pdf_cache = get_pdf_cache()
            return ChatResponse(
                response=response_text,
                pdf_count=len(pdf_cache),
            )
        except Exception as e:
            logger.exception("Error processing chat request")
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/pdfs", response_model=PDFListResponse, tags=["PDFs"])
    async def list_pdfs() -> PDFListResponse:
        """List all currently loaded PDFs."""
        pdf_cache = get_pdf_cache()
        return PDFListResponse(
            pdfs=list(pdf_cache.keys()),
            count=len(pdf_cache),
        )

    @app.post("/pdfs", response_model=LoadPDFResponse, tags=["PDFs"])
    async def load_pdf(request: LoadPDFRequest) -> LoadPDFResponse:
        """Load a PDF from URL or base64 data."""
        if request.url and request.base64_data:
            raise HTTPException(
                status_code=400,
                detail="Provide either 'url' or 'base64_data', not both",
            )

        if not request.url and not request.base64_data:
            raise HTTPException(
                status_code=400,
                detail="Must provide either 'url' or 'base64_data'",
            )

        try:
            if request.url:
                result = load_pdf_from_url.invoke(request.url)
                identifier = request.url
            else:
                # base64_data is guaranteed to be not None here
                pdf_identifier = request.identifier or "base64_pdf"
                result = load_pdf_from_base64.invoke(
                    {"pdf_base64": request.base64_data, "identifier": pdf_identifier}
                )
                identifier = pdf_identifier

            success = "Successfully" in result
            return LoadPDFResponse(
                success=success,
                message=result,
                identifier=identifier if success else None,
            )
        except Exception as e:
            logger.exception("Error loading PDF")
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.delete("/pdfs", response_model=LoadPDFResponse, tags=["PDFs"])
    async def clear_all_pdfs() -> LoadPDFResponse:
        """Clear all loaded PDFs from memory."""
        pdf_cache = get_pdf_cache()
        count = len(pdf_cache)
        pdf_cache.clear()
        return LoadPDFResponse(
            success=True,
            message=f"Cleared {count} PDF(s) from memory",
            identifier=None,
        )

    @app.delete("/pdfs/{identifier:path}", response_model=LoadPDFResponse, tags=["PDFs"])
    async def clear_pdf(identifier: str) -> LoadPDFResponse:
        """Clear a specific PDF from memory by identifier."""
        pdf_cache = get_pdf_cache()

        if identifier not in pdf_cache:
            raise HTTPException(
                status_code=404,
                detail=f"PDF with identifier '{identifier}' not found",
            )

        del pdf_cache[identifier]
        return LoadPDFResponse(
            success=True,
            message=f"Cleared PDF '{identifier}' from memory",
            identifier=identifier,
        )

    return app


# Create the app instance for uvicorn
api_app = create_api_app()
