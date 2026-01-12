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
| `pdf_agent/agent.py` | Agent creation with `inject_pdf_content` and `log_request_metrics` middleware |
| `pdf_agent/tools.py` | PDF loading tools (`load_pdf_from_url`, `load_pdf_from_file`, `load_pdf_from_base64`) |
| `pdf_agent/core.py` | Direct PDF analysis functions (non-agent), model initialization |
| `pdf_agent/prompts.py` | System prompt for the agent |
| `pdf_agent/logging_utils.py` | Pretty-printed logging utilities for agent execution |
| `pdf_agent/__main__.py` | CLI entry point with argparse-based demo modes |
| `pdf_agent/__init__.py` | Public API exports for the package |

## Common Tasks

### Run the agent
```bash
uv run poe dev
```

### Run with debug logging (shows Anthropic API request/response details)
```bash
uv run poe dev-debug
```

Sets `ANTHROPIC_LOG=debug` environment variable to enable verbose API logging.

### Run with custom PDF
```bash
python -m pdf_agent https://example.com/document.pdf
python -m pdf_agent --direct  # Direct analysis without agent
```

### Run tests
```bash
uv run poe test
uv run poe test-cov  # With coverage report
```

### Run evaluations
```bash
uv run poe eval          # Run all DeepEval tests
uv run poe eval-verbose  # Run with verbose output (-v flag)
```

Rate limiting is handled via retry configuration in `evals/conftest.py`:
- `DEEPEVAL_RETRY_MAX_ATTEMPTS=5` - Number of retry attempts
- `DEEPEVAL_RETRY_INITIAL_SECONDS=10` - Initial delay before retry (with exponential backoff)
- `DEEPEVAL_RETRY_CAP_SECONDS=60` - Maximum delay cap

### Type checking
```bash
uv run poe typecheck
```

### All quality checks
```bash
uv run poe check  # Runs: lint, format, typecheck
uv run poe ci     # CI checks: lint, typecheck, test
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

The project uses LangChain's `@wrap_model_call` middleware to modify messages before LLM calls or log metrics:

```python
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse

@wrap_model_call
def my_middleware(request: ModelRequest, handler: Callable) -> ModelResponse:
    # Pre-processing: Modify request.messages here
    modified_request = request.override(messages=new_messages)

    response = handler(modified_request)

    # Post-processing: Log metrics, extract response metadata, etc.
    return response
```

Current middleware in `agent.py`:
- `inject_pdf_content` - Injects cached PDFs into the message context
- `log_request_metrics` - Logs request duration and Anthropic request ID

## Testing

### Unit Tests
Located in `tests/` directory:
- `tests/test_agent.py` - Agent creation and middleware tests
- `tests/test_core.py` - Core model and direct analysis function tests
- `tests/test_tools.py` - Tool function tests (load_pdf_from_url, etc.)
- `tests/test_logging_utils.py` - Logging utility tests
- `tests/conftest.py` - Shared pytest fixtures (mock responses, sample PDFs, API keys)

All tests use `pytest` with strict type checking. Run with `uv run poe test` or `uv run poe test-cov`.

### Evaluations (DeepEval)
Located in `evals/` directory:

#### Mock-based Evaluations (`evals/test_pdf_agent_mocks.py`)
- Fast, no API calls required
- Tests answer relevancy, faithfulness, and helpfulness metrics
- Uses synthetic test cases with predefined context and outputs
- Good for testing evaluation metrics and expected agent behaviors
- Three test classes: `TestPDFAgentAnswerRelevancy`, `TestPDFAgentFaithfulness`, `TestPDFAgentHelpfulness`, `TestPDFAgentCombinedMetrics`

#### Integration Evaluations (`evals/test_pdf_agent_integration.py`)
- Tests the actual PDF agent with real PDF documents
- Uses Anthropic's Claude 3.5 Model Card Addendum as test PDF
- Evaluates real agent responses using DeepEval metrics (AnswerRelevancy, Faithfulness, Helpfulness)
- Slower but provides real-world validation
- Uses module-scoped fixtures to reduce API calls
- Three test classes: `TestPDFAgentIntegrationRelevancy`, `TestPDFAgentIntegrationFaithfulness`, `TestPDFAgentIntegrationHelpfulness`, `TestPDFAgentIntegrationCombined`

Both evaluation files use `claude-3-5-haiku-20241022` as the default judge model for metrics (override with `EVAL_MODEL=sonnet`). Rate limiting is handled via retry configuration with exponential backoff in `evals/conftest.py`. Run with `uv run poe eval` or `uv run poe eval-verbose`.

## Key Architecture Decisions

### Default Model
The agent uses `claude-sonnet-4-5-20250929` (Claude Sonnet 4.5) as the default model, defined in `core.py:get_model()`. This model provides:
- Native PDF support with multimodal capabilities
- Strong performance on document analysis tasks
- Support for prompt caching (via `cache_control` in middleware)

### PDF Caching Strategy
PDFs are stored in-memory in `tools.py:_pdf_cache` (a module-level dict). The cache:
- Stores base64-encoded PDF data keyed by identifier (URL, file path, or custom identifier)
- Persists across agent invocations within the same Python process
- Can be cleared with `clear_pdf_cache()` tool or by getting the cache dict directly
- Enables multi-document analysis without re-loading

### Middleware Architecture
The agent uses LangChain's `@wrap_model_call` middleware pattern for:
1. **Request Logging** (`log_request_metrics`): Captures Anthropic request IDs and timing
2. **PDF Injection** (`inject_pdf_content`): Automatically injects cached PDFs into context with ephemeral caching

This eliminates the need for a separate "analyze_loaded_pdf" tool - once loaded, PDFs are automatically available to the agent.

### Direct vs Agent Analysis
The package supports two modes:
1. **Agent Mode** (`create_pdf_agent()`): Full agentic workflow with tools, multi-step reasoning, and PDF caching
2. **Direct Mode** (`analyze_pdf_from_url/file/base64()`): Single-shot analysis without agent overhead

Use agent mode for complex multi-document workflows; use direct mode for simple one-off analyses.

## Dependencies

### Runtime
- `langchain>=1.2.0` - Agent framework with tools and middleware support
- `langchain-anthropic>=1.3.0` - Claude integration with PDF support
- `httpx>=0.28.0` - HTTP client for PDF downloads (async-ready)
- `python-dotenv>=1.2.1` - Environment variable loading

### Development
- `deepeval>=3.7.8` - LLM evaluation framework (metrics: relevancy, faithfulness, GEval)
- `pytest>=9.0.2` - Testing framework
- `pytest-cov>=7.0.0` - Coverage reporting (target: 80%)
- `pytest-mock>=3.15.1` - Mocking utilities for unit tests
- `mypy>=1.19.1` - Static type checker (strict mode enabled)
- `ruff>=0.14.10` - Fast linter and formatter (replaces black, flake8, isort)
- `bandit>=1.8.0` - Security vulnerability scanner
- `poethepoet>=0.39.0` - Task runner (poe tasks)
- `pre-commit>=4.5.1` - Git hooks framework

## Important Patterns & Gotchas

### Environment Variables
The project requires `ANTHROPIC_API_KEY` to be set. This is validated in `core.py:get_model()` and will raise a `ValueError` with a helpful message if missing. Use `.env` file (loaded via `python-dotenv` in `__main__.py`) or export directly.

To enable debug logging of Anthropic API requests/responses:
```bash
export ANTHROPIC_LOG=debug  # Or use: uv run poe dev-debug
```

### PDF Content Injection
The `inject_pdf_content` middleware automatically prepends cached PDFs to the message list as:
1. A `HumanMessage` with multimodal content (PDF + identifier text)
2. An `AIMessage` acknowledging the PDF is loaded

This happens BEFORE every LLM call if the cache is non-empty. The agent doesn't need to explicitly "analyze" - it just answers questions directly.

### Type Annotations
The codebase uses strict mypy configuration:
- `disallow_untyped_defs = true`
- `disallow_incomplete_defs = true`
- All functions must have full type annotations including return types
- Use `TYPE_CHECKING` imports to avoid circular dependencies (see `agent.py`)

### Tool Decorator Usage
Tools use `@tool(parse_docstring=True)` which:
- Automatically generates tool descriptions from the docstring
- Requires Google-style docstrings with Args section
- The first paragraph becomes the tool description shown to the agent

### Logging Utilities
The `logging_utils.py` module provides structured, emoji-rich logging:
- `log_agent_messages()` - Pretty-prints full agent execution trace
- `log_header()`, `log_analyzing()`, `log_response()`, `log_error()` - Formatted output
- All use Python's standard `logging` module at INFO/ERROR level
- Useful for demos and debugging, not for production structured logging

### Test Fixtures
`tests/conftest.py` provides shared fixtures:
- `mock_env_api_key` - Sets fake API key for tests that need it
- `clear_env_api_key` - Removes API key to test error handling
- `sample_pdf_base64` - Minimal valid PDF for unit tests
- `sample_pdf_url` - Test URL string
- `mock_anthropic_response` - Mock AI response object

### Coverage Configuration
- Minimum coverage: 80% (enforced in `pyproject.toml`)
- `__main__.py` is excluded from coverage (CLI entry point)
- Branch coverage enabled
- Run with: `uv run poe test-cov`

### Pre-commit Hooks
The project uses pre-commit hooks that run on every commit:
- Install once with: `uv run poe pre-commit-install`
- Includes: ruff (lint + format), mypy, trailing whitespace, YAML checks, secret detection
- Hooks will auto-fix issues when possible and block commits if checks fail
- Manually run all hooks: `uv run poe pre-commit-run`
