# LangChain Anthropic PDF Agent

A LangChain agent specialized for PDF document analysis using Anthropic's Claude model with native PDF support.

## Features

- **PDF Document Analysis Agent**: An intelligent agent that can load, analyze, and answer questions about PDF documents
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

## Agent Tools

The PDF Agent has access to these tools (defined with `@tool` decorators):

| Tool | Description |
|------|-------------|
| `load_pdf_from_url` | Load a PDF from a public URL |
| `load_pdf_from_file` | Load a PDF from a local file path |
| `load_pdf_from_base64` | Load a PDF from base64-encoded data |
| `analyze_loaded_pdf` | Analyze a previously loaded PDF with a question |
| `list_loaded_pdfs` | List all currently loaded PDFs |
| `clear_pdf_cache` | Clear all PDFs from memory |

## Development

### Poe Tasks

This project uses [poethepoet](https://github.com/nat-n/poethepoet) for task running:

| Command | Description |
|---------|-------------|
| `uv run poe dev` | Run the PDF agent demo |
| `uv run poe lint` | Check code with ruff |
| `uv run poe format` | Format code with ruff |
| `uv run poe fix` | Auto-fix linting issues |
| `uv run poe typecheck` | Run mypy type checking |
| `uv run poe check` | Run lint + format + typecheck |
| `uv run poe outdated` | Check for outdated packages |
| `uv run poe upgrade` | Upgrade all packages |

### Code Quality

```bash
# Run all checks (lint, format, typecheck)
uv run poe check

# Auto-fix issues
uv run poe fix
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

Output shows the complete execution flow:
```
[1] HumanMessage - User's input
[2] AIMessage - Model decides to call load_pdf_from_url
[3] ToolMessage - Result from load_pdf_from_url
[4] AIMessage - Model decides to call analyze_loaded_pdf
[5] ToolMessage - Analysis result
[6] AIMessage - Final response to user
```

## PDF Support Details

Claude's PDF support allows you to:

- Analyze text, images, charts, and tables in PDFs
- Process up to 100 pages per request
- Handle files up to 32MB total request size
- Use standard PDFs (no password protection)

## Project Structure

```
langchain-anthropic-pdf-support/
├── pdf_agent/              # Main package
│   ├── __init__.py         # Public API exports
│   ├── __main__.py         # CLI entry point
│   ├── agent.py            # Agent creation and logging utilities
│   ├── core.py             # Model initialization and direct analysis
│   └── tools.py            # Agent tools (@tool decorated functions)
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

### Development
- `ruff>=0.14.10` - Fast Python linter and formatter
- `mypy>=1.19.1` - Static type checker
- `poethepoet>=0.39.0` - Task runner

## Resources

- [Anthropic PDF Support Documentation](https://docs.anthropic.com/en/docs/build-with-claude/pdf-support)
- [LangChain Anthropic Integration](https://python.langchain.com/docs/integrations/chat/anthropic/)
- [LangChain Tools Documentation](https://python.langchain.com/docs/concepts/tools/)
- [LangChain Documentation](https://python.langchain.com/docs/)

## License

MIT
