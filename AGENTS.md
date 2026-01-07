# Agent Instructions

This file provides guidance for AI agents (Claude Code, Cursor, etc.) working with this codebase.

## Project Overview

A LangChain agent for PDF document analysis using Anthropic's Claude model with native PDF support.

## Key Architecture

### PDF Analysis Flow (Optimized - 2 API calls)

```
User Request → Agent (Call 1) → load_pdf_from_url tool → PDF cached
                                        ↓
              Middleware injects PDF into context
                                        ↓
              Agent (Call 2) → Direct analysis + response
```

The `inject_pdf_content` middleware in `agent.py` automatically injects cached PDFs into the agent's context, eliminating a separate `analyze_loaded_pdf` tool call.

## Important Files

| File | Purpose |
|------|---------|
| `pdf_agent/agent.py` | Agent creation with `inject_pdf_content` middleware |
| `pdf_agent/tools.py` | PDF loading tools (`load_pdf_from_url`, etc.) |
| `pdf_agent/core.py` | Direct PDF analysis functions (non-agent) |
| `pdf_agent/prompts.py` | System prompt for the agent |
| `pdf_agent/__main__.py` | CLI entry point |

## Common Tasks

### Run the agent
```bash
uv run poe dev
```

### Run tests
```bash
uv run poe test
```

### Run evaluations
```bash
uv run poe eval
```

### Type checking
```bash
uv run poe typecheck
```

### All quality checks
```bash
uv run poe check
```

## Code Patterns

### Adding New Tools

Tools are defined in `pdf_agent/tools.py` using the `@tool` decorator:

```python
@tool(parse_docstring=True)
def my_new_tool(param: str) -> str:
    """Tool description.

    Args:
        param: Parameter description.
    """
    # Implementation
    return result
```

Then add to:
1. `pdf_agent/agent.py` - `tools` list in `create_pdf_agent()`
2. `pdf_agent/__init__.py` - exports
3. `tests/test_tools.py` - unit tests

### Middleware Pattern

The project uses LangChain's `@wrap_model_call` middleware to modify messages before LLM calls:

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

@wrap_model_call
def my_middleware(request: ModelRequest, handler: Callable) -> ModelResponse:
    # Modify request.messages here
    modified_request = request.override(messages=new_messages)
    return handler(modified_request)
```

## Testing

- Unit tests: `tests/test_*.py`
- Evaluations: `evals/test_pdf_agent_evals.py` (uses DeepEval)

Tests use `pytest` with fixtures in `tests/conftest.py`.

## Dependencies

- `langchain>=1.2.0` - Agent framework
- `langchain-anthropic>=1.3.0` - Claude integration
- `httpx` - HTTP client for PDF downloads
- `deepeval` - LLM evaluation framework (dev)
