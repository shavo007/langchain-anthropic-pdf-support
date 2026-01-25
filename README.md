# LangChain Anthropic PDF Agent

[![CI](https://github.com/shavo007/langchain-anthropic-pdf-support/actions/workflows/ci.yml/badge.svg)](https://github.com/shavo007/langchain-anthropic-pdf-support/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/shavo007/langchain-anthropic-pdf-support/graph/badge.svg)](https://codecov.io/gh/shavo007/langchain-anthropic-pdf-support)

A LangChain agent specialized for PDF document analysis using Anthropic's Claude model with native PDF support.

## Features

- **PDF Document Analysis Agent**: An intelligent agent that can load, analyze, and answer questions about PDF documents
- **REST API Server**: FastAPI-based HTTP API for chat interactions and PDF management
- **Multiple Input Methods**: Support for PDFs from URLs, local files, or base64-encoded data
- **Multi-Document Support**: Load and compare multiple PDFs in a single session
- **Visual Understanding**: Analyze text, images, charts, tables, and visual elements
- **Agent Execution Logging**: Detailed logging of tool calls and AI messages
- **Type Safety**: Full type hints with mypy strict mode validation
- **Modern Tooling**: Ruff for linting/formatting, poethepoet for task running

## Agent Capabilities

The PDF Agent can:
- Load PDF documents from URLs, local file paths, or base64-encoded data
- Analyze text content, tables, charts, images, and visual elements
- Answer specific questions about document contents
- Summarize documents or specific sections
- Extract structured data from PDFs
- Compare information across multiple loaded PDFs
- Identify key findings, themes, and important details

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Anthropic API key

## Setup

### 1. Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

### 2. Clone and setup the project

```bash
git clone https://github.com/shavo007/langchain-anthropic-pdf-support.git
cd langchain-anthropic-pdf-support

# Install dependencies
uv sync
```

### 3. Set your API key

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=your-api-key-here
```

Or export it directly:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Get your API key from [Anthropic Console](https://console.anthropic.com/).

## Usage

### Run the demo

```bash
# Run the agent demo (default)
uv run poe dev

# Or run direct analysis without the agent
uv run python -m pdf_agent --direct
```

### Using the PDF Agent

```python
from pdf_agent import create_pdf_agent, log_agent_messages

# Create the PDF analysis agent
agent = create_pdf_agent()

# Ask the agent to analyze a PDF
response = agent.invoke({
    "messages": [
        {
            "role": "user",
            "content": (
                "Please load this PDF: https://example.com/document.pdf "
                "Then summarize the key findings."
            )
        }
    ]
})

# Log all tool calls and messages
log_agent_messages(response["messages"])

# Get the final response
print(response["messages"][-1].content)
```

### Direct PDF Analysis (without agent)

```python
from pdf_agent import (
    analyze_pdf_from_url,
    analyze_pdf_from_file,
    analyze_pdf_from_base64,
)

# Analyze a PDF from URL
result = analyze_pdf_from_url(
    url="https://example.com/document.pdf",
    question="What is the main topic of this document?"
)
print(result)

# Analyze a local PDF file
result = analyze_pdf_from_file(
    file_path="./my-document.pdf",
    question="Summarize the key points."
)
print(result)

# Analyze from base64-encoded data
import base64
with open("document.pdf", "rb") as f:
    pdf_base64 = base64.standard_b64encode(f.read()).decode("utf-8")

result = analyze_pdf_from_base64(
    pdf_data=pdf_base64,
    question="What are the main conclusions?"
)
print(result)
```

### Using Base64 with the Agent

```python
from pdf_agent import create_pdf_agent, load_pdf_from_base64

# Pre-load a base64 PDF (useful for large files)
load_pdf_from_base64(pdf_base64, identifier="my_report")

# Then use the agent to analyze it
agent = create_pdf_agent()
response = agent.invoke({
    "messages": [{
        "role": "user",
        "content": "Analyze the PDF with identifier 'my_report' and summarize it."
    }]
})
```

### REST API Server

Start the FastAPI server to interact with the PDF agent via HTTP:

```bash
# Development mode with auto-reload
uv run poe serve

# Production mode
uv run poe serve-prod
```

The server runs at `http://localhost:8000` with these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with agent status |
| POST | `/chat` | Send message to agent |
| GET | `/pdfs` | List loaded PDFs |
| POST | `/pdfs` | Load PDF from URL or base64 |
| DELETE | `/pdfs` | Clear all PDFs |
| DELETE | `/pdfs/{id}` | Clear specific PDF |

**Example API Usage:**

**1. Health Check**
```bash
curl -s http://localhost:8000/health | jq
```
Response:
```json
{
  "status": "healthy",
  "agent_initialized": false,
  "pdf_count": 0
}
```

**2. Load a PDF from URL**
```bash
curl -s -X POST http://localhost:8000/pdfs \
  -H "Content-Type: application/json" \
  -d '{"url": "https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf"}' | jq
```
Response:
```json
{
  "success": true,
  "message": "Successfully loaded PDF from URL. Use this identifier for analysis: https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf",
  "identifier": "https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf"
}
```

**3. List Loaded PDFs**
```bash
curl -s http://localhost:8000/pdfs | jq
```
Response:
```json
{
  "pdfs": [
    "https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf"
  ],
  "count": 1
}
```

**4. Chat with the Agent (with PDF URL in message)**

The agent can load and analyze a PDF directly from a URL in your message - no need to load it separately first:
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Load and summarize this PDF: https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf"}' | jq
```
Response:
```json
{
  "response": "This document is a Model Card Addendum for Anthropic's Claude 3.5 Sonnet and Claude 3.5 Haiku models. It describes their capabilities including a new computer use feature that allows Claude to interpret screenshots and perform GUI actions. The document covers performance benchmarks showing improvements in coding, reasoning, and agentic tasks, along with safety evaluations conducted in collaboration with AI safety institutes.",
  "pdf_count": 1
}
```

**5. Chat with a Previously Loaded PDF**
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What benchmarks are mentioned in the document?"}' | jq
```
Response:
```json
{
  "response": "The document mentions several benchmarks: SWE-bench Verified (49.0% pass rate for software engineering tasks), TAU-bench (69.2% in retail, 46.0% in airline domains for agentic tasks), and OSWorld (22% success rate for computer use tasks).",
  "pdf_count": 1
}
```

**5. Load PDF from Base64**
```bash
curl -s -X POST http://localhost:8000/pdfs \
  -H "Content-Type: application/json" \
  -d '{"base64_data": "JVBERi0xLjAK...", "identifier": "my-document"}' | jq
```
Response:
```json
{
  "success": true,
  "message": "Successfully loaded PDF from base64 data. Use this identifier for analysis: my-document",
  "identifier": "my-document"
}
```

**6. Clear a Specific PDF**
```bash
curl -s -X DELETE "http://localhost:8000/pdfs/my-document" | jq
```
Response:
```json
{
  "success": true,
  "message": "Cleared PDF 'my-document' from memory",
  "identifier": "my-document"
}
```

**7. Clear All PDFs**
```bash
curl -s -X DELETE http://localhost:8000/pdfs | jq
```
Response:
```json
{
  "success": true,
  "message": "Cleared 1 PDF(s) from memory",
  "identifier": null
}
```

Interactive API documentation is available at `http://localhost:8000/docs` (Swagger UI).

## Agent Tools

The PDF Agent has access to these tools (defined with `@tool` decorators):

| Tool | Description |
|------|-------------|
| `load_pdf_from_url` | Load a PDF from a public URL |
| `load_pdf_from_file` | Load a PDF from a local file path |
| `load_pdf_from_base64` | Load a PDF from base64-encoded data |
| `list_loaded_pdfs` | List all currently loaded PDFs |
| `clear_pdf_cache` | Clear all PDFs from memory |

**Note:** Once a PDF is loaded, the agent can directly analyze its contents without additional tool calls. The PDF content is automatically injected into the agent's context via middleware, enabling efficient single-pass analysis.

## Development

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) for automated code quality checks on every commit.

**Setup (one-time):**

```bash
# Install pre-commit hooks
uv run poe pre-commit-install
```

**Hooks included:**
- **ruff** - Lint and auto-fix Python code
- **ruff-format** - Format Python code
- **trailing-whitespace** - Remove trailing whitespace
- **end-of-file-fixer** - Ensure files end with newline
- **check-yaml** - Validate YAML syntax
- **check-added-large-files** - Prevent files > 1MB
- **check-merge-conflict** - Detect merge conflict markers
- **detect-private-key** - Prevent committing secrets
- **mypy** - Type check Python code

**Manual run:**

```bash
# Run all hooks on all files
uv run poe pre-commit-run
```

### Poe Tasks

This project uses [poethepoet](https://github.com/nat-n/poethepoet) for task running:

| Command | Description |
|---------|-------------|
| `uv run poe dev` | Run the PDF agent demo |
| `uv run poe demo` | Run demo with W3C test PDF |
| `uv run poe serve` | Run FastAPI server (dev mode with reload) |
| `uv run poe serve-prod` | Run FastAPI server (production mode) |
| `uv run poe test` | Run unit tests |
| `uv run poe test-cov` | Run tests with coverage report |
| `uv run poe lint` | Check code with ruff |
| `uv run poe format` | Format code with ruff |
| `uv run poe fix` | Auto-fix linting issues |
| `uv run poe typecheck` | Run mypy type checking |
| `uv run poe check` | Run lint + format + typecheck |
| `uv run poe ci` | Run lint + typecheck + test |
| `uv run poe pre-commit-install` | Install pre-commit hooks |
| `uv run poe pre-commit-run` | Run pre-commit on all files |
| `uv run poe outdated` | Check for outdated packages |
| `uv run poe upgrade` | Upgrade all packages |

### Code Quality

```bash
# Run all checks (lint, format, typecheck)
uv run poe check

# Auto-fix issues
uv run poe fix
```

### Testing

```bash
# Run all tests
uv run poe test

# Run tests with coverage report
uv run poe test-cov
```

### Type Checking

The project uses strict mypy configuration:

```bash
uv run poe typecheck
```

## Agent Execution Logging

The agent includes built-in logging for debugging and monitoring:

```python
from pdf_agent import create_pdf_agent, log_agent_messages

agent = create_pdf_agent()
response = agent.invoke({"messages": [...]})

# Log all messages including tool calls
log_agent_messages(response["messages"])
```

Example output from `uv run poe dev`:
```
╔════════════════════════════════════════════════════════════╗
║  📄                 PDF Document Analyzer                  ║
║                        🤖 Agent Mode                       ║
╚════════════════════════════════════════════════════════════╝

INFO - Anthropic API call: request_id=msg_01Tk2CJ1R1KqLLL3JGStedst, duration=4270.82ms

┌─ [1] 👤 Human Message ─────────────────────────
│  Please load this PDF: https://example.com/doc.pdf
│  Then tell me what it's about and list 3 key points.
└──────────────────────────────────────────────────

┌─ [2] 🧠 AI Message ───────────────────────────
│  🔧 Tool Calls (1):
│     ├─ 🛠️  load_pdf_from_url
│     │     Args: {'url': 'https://example.com/doc.pdf'}
└──────────────────────────────────────────────────

┌─ [3] ⚡ Tool Result ──────────────────────────
│  🔧 Tool: load_pdf_from_url
│  ✅ Status: Success
│  📄 Result: Successfully loaded PDF from URL.
└──────────────────────────────────────────────────

INFO - Anthropic API call: request_id=msg_01XMHxjAsqEzksv1LU2eVKU3, duration=17872.93ms

┌─ [4] 🧠 AI Message ───────────────────────────
│  ## Document Overview
│  This document describes... (PDF analysis via middleware)
└──────────────────────────────────────────────────

✨ Execution complete! (2 API calls)
```

**Request Logging**: Each API call logs the Anthropic `request_id` (useful for debugging with Anthropic support) and `duration` in milliseconds.

This optimized flow reduces API calls from 4 to 2 by injecting PDF content directly into the agent's context after loading, eliminating the need for a separate analysis tool call.

## PDF Support Details

Claude's PDF support allows you to:

- Analyze text, images, charts, and tables in PDFs
- Process up to 100 pages per request
- Handle files up to 32MB total request size
- Use standard PDFs (no password protection)

## Project Structure

```
langchain-anthropic-pdf-support/
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions CI workflow
├── pdf_agent/              # Main package
│   ├── __init__.py         # Public API exports
│   ├── __main__.py         # CLI entry point
│   ├── agent.py            # Agent creation
│   ├── api.py              # FastAPI REST API endpoints
│   ├── core.py             # Model initialization and direct analysis
│   ├── logging_utils.py    # Pretty logging with emojis
│   ├── prompts.py          # System prompts
│   ├── server.py           # Server entry point for uvicorn
│   └── tools.py            # Agent tools (@tool decorated functions)
├── tests/                  # Unit tests
│   ├── conftest.py         # Shared fixtures
│   ├── test_agent.py       # Agent tests
│   ├── test_api.py         # FastAPI endpoint tests
│   ├── test_core.py        # Core module tests
│   ├── test_logging_utils.py # Logging tests
│   └── test_tools.py       # Tools tests
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── pyproject.toml          # Project configuration and dependencies
├── uv.lock                 # Locked dependencies
├── .env                    # Environment variables (gitignored)
├── .gitignore              # Git ignore rules
├── .python-version         # Python version specification
└── README.md               # This file
```

## Dependencies

### Runtime
- `langchain>=1.2.0` - LangChain framework
- `langchain-anthropic>=1.3.0` - Anthropic integration for LangChain
- `httpx>=0.28.0` - HTTP client for downloading PDFs
- `python-dotenv>=1.2.1` - Environment variable management
- `fastapi>=0.115.0` - Modern web framework for REST API
- `uvicorn[standard]>=0.34.0` - ASGI server for FastAPI

### Development
- `ruff>=0.14.10` - Fast Python linter and formatter
- `mypy>=1.19.1` - Static type checker
- `pytest>=9.0.2` - Testing framework
- `pytest-cov>=7.0.0` - Coverage reporting
- `pytest-mock>=3.15.1` - Mocking utilities
- `pre-commit>=4.5.1` - Git hooks framework
- `poethepoet>=0.39.0` - Task runner

## Resources

- [Anthropic PDF Support Documentation](https://docs.anthropic.com/en/docs/build-with-claude/pdf-support)
- [LangChain Anthropic Integration](https://python.langchain.com/docs/integrations/chat/anthropic/)
- [LangChain Tools Documentation](https://python.langchain.com/docs/concepts/tools/)
- [LangChain Documentation](https://python.langchain.com/docs/)

## License

MIT
