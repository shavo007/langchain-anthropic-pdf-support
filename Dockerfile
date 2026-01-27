FROM python:3.13-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies (no dev deps for production)
RUN uv sync --frozen --no-dev

# Copy application code
COPY pdf_agent/ ./pdf_agent/

# Expose the API port
EXPOSE 8000

# Run the FastAPI server
CMD ["uv", "run", "uvicorn", "pdf_agent.server:app", "--host", "0.0.0.0", "--port", "8000"]
