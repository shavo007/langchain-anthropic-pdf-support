"""DeepEval configuration for rate limiting and retry handling.

This module configures DeepEval's retry behavior to handle Anthropic API
rate limits (50,000 input tokens per minute) more gracefully.
"""

import os


def pytest_configure(config):
    """Configure DeepEval retry settings before tests run.

    These environment variables control the backoff strategy for rate limit retries:
    - DEEPEVAL_RETRY_MAX_ATTEMPTS: Number of retry attempts (default: 5)
    - DEEPEVAL_RETRY_INITIAL_SECONDS: Initial delay before first retry (default: 10s)
    - DEEPEVAL_RETRY_EXP_BASE: Exponential backoff multiplier (default: 2.0)
    - DEEPEVAL_RETRY_JITTER: Random jitter added to delays (default: 1.0)
    - DEEPEVAL_RETRY_CAP_SECONDS: Maximum delay cap (default: 60s)
    """
    # Set retry configuration if not already set by user
    retry_defaults = {
        "DEEPEVAL_RETRY_MAX_ATTEMPTS": "5",
        "DEEPEVAL_RETRY_INITIAL_SECONDS": "10.0",
        "DEEPEVAL_RETRY_EXP_BASE": "2.0",
        "DEEPEVAL_RETRY_JITTER": "1.0",
        "DEEPEVAL_RETRY_CAP_SECONDS": "60.0",
    }

    for key, default_value in retry_defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value
