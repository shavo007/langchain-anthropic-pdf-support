# LangChain Anthropic PDF Agent

A LangChain agent specialized for PDF document analysis using Anthropic's Claude model with native PDF support.

## Features

- **PDF Document Analysis Agent**: An intelligent agent that can load, analyze, and answer questions about PDF documents
- **Multiple Input Methods**: Support for PDFs from URLs, local files, or base64-encoded data
- **Multi-Document Support**: Load and compare multiple PDFs in a single session
- **Visual Understanding**: Analyze text, images, charts, tables, and visual elements

## Agent Capabilities

The PDF Agent can:
- Load PDF documents from URLs or local file paths
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
cd langchain-anthropic-pdf-support

# Install dependencies
uv sync
```

### 3. Set your API key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Get your API key from [Anthropic Console](https://console.anthropic.com/).

## Usage

### Run the demo

```bash
uv run python pdf_agent.py

# Or use the installed command
uv run pdf-agent
```

### Using the PDF Agent

```python
from pdf_agent import create_pdf_agent

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
```

## Agent Tools

The PDF Agent has access to these tools:

| Tool | Description |
|------|-------------|
| `load_pdf_from_url` | Load a PDF from a public URL |
| `load_pdf_from_file` | Load a PDF from a local file path |
| `analyze_loaded_pdf` | Analyze a previously loaded PDF with a question |
| `list_loaded_pdfs` | List all currently loaded PDFs |
| `clear_pdf_cache` | Clear all PDFs from memory |

## PDF Support Details

Claude's PDF support allows you to:

- Analyze text, images, charts, and tables in PDFs
- Process up to 100 pages per request
- Handle files up to 32MB total request size
- Use standard PDFs (no password protection)

## Project Structure

```
langchain-anthropic-pdf-support/
├── pdf_agent.py      # Main module with PDF agent and analysis functions
├── pyproject.toml    # Project configuration and dependencies
├── README.md         # This file
└── .python-version   # Python version specification
```

## Dependencies

- `langchain>=1.2.0` - LangChain framework
- `langchain-anthropic>=1.3.0` - Anthropic integration for LangChain
- `httpx>=0.28.0` - HTTP client for downloading PDFs

## Resources

- [Anthropic PDF Support Documentation](https://docs.anthropic.com/en/docs/build-with-claude/pdf-support)
- [LangChain Anthropic Integration](https://python.langchain.com/docs/integrations/chat/anthropic/)
- [LangChain Documentation](https://python.langchain.com/docs/)

## License

MIT
