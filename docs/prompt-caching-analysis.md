# Prompt Caching Analysis

## Current State

PDF documents are already cached via middleware at `pdf_agent/agent.py:92`:

```python
"cache_control": {"type": "ephemeral"}
```

## Additional Caching Opportunities

| Component | Tokens | Currently Cached |
|-----------|--------|------------------|
| PDF documents | Variable (large) | Yes |
| System prompt | ~1,200 | No |
| Tool definitions | ~560 | No |

Combined: ~1,760 tokens sent on every call that could be cached.

## When Additional Caching Helps

1. **Multi-turn conversations** - Same system prompt repeated each turn
2. **Evaluation runs** - Test suite makes many calls with identical prompts
3. **Latency-sensitive apps** - Cache hits are faster than re-processing

## Implementation

Change `pdf_agent/agent.py` to use a `SystemMessage` with cache control:

```python
from langchain_core.messages import SystemMessage

agent = create_agent(
    model,
    tools=tools,
    system_prompt=SystemMessage(
        content=[
            {
                "type": "text",
                "text": PDF_AGENT_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}
            }
        ]
    ),
    middleware=[log_request_metrics, inject_pdf_content],
)
```

## Cost/Benefit

- **Cache creation**: 25% extra cost on first request
- **Cache hit**: 90% discount on cached tokens
- **Cache lifetime**: 5 minutes (refreshed on each hit)
- **Minimum threshold**: 1,024 tokens (system prompt qualifies)

For ~1,760 token prefix:
- First call: ~$0.013 (at Sonnet rates, includes creation cost)
- Subsequent calls: ~$0.0005 (90% off)

## References

- [LangChain Anthropic Middleware Docs](https://docs.langchain.com/oss/python/integrations/middleware/anthropic#prompt-caching)
- [Working with cache control in middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom)
