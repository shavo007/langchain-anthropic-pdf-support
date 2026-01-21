"""Non-LLM performance evaluations for the PDF Agent.

This module contains deterministic, non-LLM evaluations for testing
latency and cost metrics. These tests are fast and don't require
LLM-as-a-judge API calls.

Run with: uv run pytest evals/test_pdf_agent_performance.py -v
"""

import time

import pytest
from deepeval import assert_test
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

from pdf_agent import create_pdf_agent, get_pdf_cache

# Test PDF: Anthropic's Claude 3.5 Model Card Addendum
TEST_PDF_URL = "https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf"


class LatencyMetric(BaseMetric):
    """Custom metric for evaluating response latency.

    Measures whether the LLM response completed within the specified
    time threshold.
    """

    def __init__(self, max_latency_seconds: float = 30.0):
        """Initialize the latency metric.

        Args:
            max_latency_seconds: Maximum acceptable latency in seconds.
        """
        self.max_latency = max_latency_seconds
        self.threshold = 1.0  # Score threshold for passing (DeepEval convention)
        self.score = 0.0
        self.reason = ""

    def measure(self, test_case: LLMTestCase) -> float:
        """Measure latency against threshold.

        Args:
            test_case: Test case with completion_time set.

        Returns:
            Score between 0 and 1 (1 if within threshold, 0 if exceeded).
        """
        if test_case.completion_time is None:
            self.score = 0.0
            self.reason = "No completion_time provided in test case"
            return self.score

        latency = test_case.completion_time
        if latency <= self.max_latency:
            self.score = 1.0
            self.reason = f"Latency {latency:.2f}s within limit {self.max_latency}s"
        else:
            # Score degrades based on how much limit is exceeded
            self.score = max(0.0, 1.0 - (latency - self.max_latency) / self.max_latency)
            self.reason = f"Latency {latency:.2f}s exceeded limit {self.max_latency}s"

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        """Async version of measure."""
        return self.measure(test_case)

    def is_successful(self) -> bool:
        """Check if the metric passed."""
        return self.score >= 0.7  # Allow some grace for slight overages

    @property
    def __name__(self) -> str:
        return "Latency"


class CostMetric(BaseMetric):
    """Custom metric for evaluating token cost.

    Measures whether the LLM interaction stayed within the specified
    cost threshold.
    """

    def __init__(self, max_cost_usd: float = 0.10):
        """Initialize the cost metric.

        Args:
            max_cost_usd: Maximum acceptable cost in USD.
        """
        self.max_cost = max_cost_usd
        self.threshold = 1.0  # Score threshold for passing (DeepEval convention)
        self.score = 0.0
        self.reason = ""

    def measure(self, test_case: LLMTestCase) -> float:
        """Measure cost against threshold.

        Args:
            test_case: Test case with token_cost set.

        Returns:
            Score between 0 and 1 (1 if within threshold, 0 if exceeded).
        """
        if test_case.token_cost is None:
            self.score = 0.0
            self.reason = "No token_cost provided in test case"
            return self.score

        cost = test_case.token_cost
        if cost <= self.max_cost:
            self.score = 1.0
            self.reason = f"Cost ${cost:.4f} within limit ${self.max_cost:.4f}"
        else:
            # Score degrades based on how much limit is exceeded
            self.score = max(0.0, 1.0 - (cost - self.max_cost) / self.max_cost)
            self.reason = f"Cost ${cost:.4f} exceeded limit ${self.max_cost:.4f}"

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        """Async version of measure."""
        return self.measure(test_case)

    def is_successful(self) -> bool:
        """Check if the metric passed."""
        return self.score >= 0.7  # Allow some grace for slight overages

    @property
    def __name__(self) -> str:
        return "Cost"


class ResponseLengthMetric(BaseMetric):
    """Custom metric for evaluating response length bounds.

    Ensures responses are neither too short (potentially unhelpful)
    nor too long (potentially verbose or runaway generation).
    """

    def __init__(self, min_length: int = 50, max_length: int = 5000):
        """Initialize the response length metric.

        Args:
            min_length: Minimum acceptable response length in characters.
            max_length: Maximum acceptable response length in characters.
        """
        self.min_length = min_length
        self.max_length = max_length
        self.threshold = 1.0
        self.score = 0.0
        self.reason = ""

    def measure(self, test_case: LLMTestCase) -> float:
        """Measure response length against bounds.

        Args:
            test_case: Test case with actual_output set.

        Returns:
            Score of 1.0 if within bounds, 0.0 otherwise.
        """
        if test_case.actual_output is None:
            self.score = 0.0
            self.reason = "No actual_output provided in test case"
            return self.score

        length = len(test_case.actual_output)
        if self.min_length <= length <= self.max_length:
            self.score = 1.0
            self.reason = (
                f"Response length {length} chars within bounds "
                f"[{self.min_length}, {self.max_length}]"
            )
        elif length < self.min_length:
            self.score = 0.0
            self.reason = f"Response length {length} chars below minimum {self.min_length}"
        else:
            self.score = 0.0
            self.reason = f"Response length {length} chars exceeds maximum {self.max_length}"

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        """Async version of measure."""
        return self.measure(test_case)

    def is_successful(self) -> bool:
        """Check if the metric passed."""
        return self.score >= self.threshold

    @property
    def __name__(self) -> str:
        return "Response Length"


# Pricing for Claude models (per token, in USD)
# https://www.anthropic.com/pricing
CLAUDE_PRICING = {
    "claude-3-5-haiku-20241022": {
        "input": 0.80 / 1_000_000,  # $0.80 per 1M input tokens
        "output": 4.00 / 1_000_000,  # $4.00 per 1M output tokens
    },
    "claude-sonnet-4-5-20250929": {
        "input": 3.00 / 1_000_000,  # $3.00 per 1M input tokens
        "output": 15.00 / 1_000_000,  # $15.00 per 1M output tokens
    },
}


def estimate_token_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "claude-3-5-haiku-20241022",
) -> float:
    """Estimate the cost of an LLM call based on token usage.

    Args:
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        model: Model name for pricing lookup.

    Returns:
        Estimated cost in USD.
    """
    pricing = CLAUDE_PRICING.get(model, CLAUDE_PRICING["claude-3-5-haiku-20241022"])
    return (input_tokens * pricing["input"]) + (output_tokens * pricing["output"])


def invoke_agent_with_metrics(agent, question: str) -> tuple[str, float, float]:
    """Invoke the PDF agent and return response with timing and cost.

    Args:
        agent: The PDF agent to invoke.
        question: The question to ask.

    Returns:
        Tuple of (response_text, completion_time_seconds, estimated_cost_usd).
    """
    start_time = time.perf_counter()
    response = agent.invoke({"messages": [{"role": "user", "content": question}]})
    completion_time = time.perf_counter() - start_time

    # Get the final response
    final_message = response["messages"][-1]
    actual_output = final_message.content

    # Estimate token usage and cost
    # Note: This is a rough estimate. For production, use actual token counts
    # from the API response metadata.
    input_chars = len(question)
    output_chars = len(actual_output)
    # Rough approximation: ~4 chars per token
    input_tokens = input_chars // 4
    output_tokens = output_chars // 4

    # Account for tool calls and system prompts (rough multiplier)
    input_tokens *= 3  # System prompt + tool definitions add overhead

    estimated_cost = estimate_token_cost(input_tokens, output_tokens)

    return actual_output, completion_time, estimated_cost


@pytest.fixture(scope="module")
def pdf_agent():
    """Create and return the PDF agent."""
    return create_pdf_agent()


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear PDF cache before each test."""
    get_pdf_cache().clear()
    yield
    get_pdf_cache().clear()


class TestPDFAgentLatency:
    """Latency tests for the PDF agent."""

    def test_simple_question_latency(self, pdf_agent) -> None:
        """Test latency for a simple question without PDF loading."""
        question = "What can you help me with?"

        actual_output, completion_time, _ = invoke_agent_with_metrics(pdf_agent, question)

        # Simple questions should complete quickly (within 15 seconds)
        metric = LatencyMetric(max_latency_seconds=15.0)
        test_case = LLMTestCase(
            input=question,
            actual_output=actual_output,
            completion_time=completion_time,
        )
        assert_test(test_case, [metric])

    def test_pdf_loading_latency(self, pdf_agent) -> None:
        """Test latency for loading and querying a PDF."""
        question = f"Please load this PDF: {TEST_PDF_URL} What is this document about?"

        actual_output, completion_time, _ = invoke_agent_with_metrics(pdf_agent, question)

        # PDF loading + query should complete within 60 seconds
        metric = LatencyMetric(max_latency_seconds=60.0)
        test_case = LLMTestCase(
            input=question,
            actual_output=actual_output,
            completion_time=completion_time,
        )
        assert_test(test_case, [metric])

    def test_cached_pdf_query_latency(self, pdf_agent) -> None:
        """Test latency for querying an already-loaded PDF."""
        # First, load the PDF
        load_question = f"Load this PDF: {TEST_PDF_URL}"
        invoke_agent_with_metrics(pdf_agent, load_question)

        # Now query the cached PDF
        query_question = "What benchmark results are mentioned?"
        actual_output, completion_time, _ = invoke_agent_with_metrics(pdf_agent, query_question)

        # Cached queries should be faster (within 30 seconds)
        metric = LatencyMetric(max_latency_seconds=30.0)
        test_case = LLMTestCase(
            input=query_question,
            actual_output=actual_output,
            completion_time=completion_time,
        )
        assert_test(test_case, [metric])


class TestPDFAgentCost:
    """Cost monitoring tests for the PDF agent."""

    def test_simple_question_cost(self, pdf_agent) -> None:
        """Test that simple questions stay within cost bounds."""
        question = "What can you help me with?"

        actual_output, _, estimated_cost = invoke_agent_with_metrics(pdf_agent, question)

        # Simple questions should be very cheap (< $0.01)
        metric = CostMetric(max_cost_usd=0.01)
        test_case = LLMTestCase(
            input=question,
            actual_output=actual_output,
            token_cost=estimated_cost,
        )
        assert_test(test_case, [metric])

    def test_pdf_query_cost(self, pdf_agent) -> None:
        """Test that PDF queries stay within reasonable cost bounds."""
        question = (
            f"Load this PDF: {TEST_PDF_URL} "
            "Summarize the key findings about computer use capability."
        )

        actual_output, _, estimated_cost = invoke_agent_with_metrics(pdf_agent, question)

        # PDF queries with substantial content should stay under $0.10
        metric = CostMetric(max_cost_usd=0.10)
        test_case = LLMTestCase(
            input=question,
            actual_output=actual_output,
            token_cost=estimated_cost,
        )
        assert_test(test_case, [metric])


class TestPDFAgentResponseLength:
    """Response length validation tests."""

    def test_summary_response_length(self, pdf_agent) -> None:
        """Test that summary responses have appropriate length."""
        question = (
            f"Load this PDF: {TEST_PDF_URL} Give me a brief summary of what this document is about."
        )

        actual_output, completion_time, estimated_cost = invoke_agent_with_metrics(
            pdf_agent, question
        )

        # Summaries should be substantive but not excessively long
        length_metric = ResponseLengthMetric(min_length=100, max_length=3000)
        test_case = LLMTestCase(
            input=question,
            actual_output=actual_output,
            completion_time=completion_time,
            token_cost=estimated_cost,
        )
        assert_test(test_case, [length_metric])

    def test_detailed_query_response_length(self, pdf_agent) -> None:
        """Test that detailed queries produce appropriately sized responses."""
        question = (
            f"Load this PDF: {TEST_PDF_URL} "
            "List all the benchmark results mentioned in this document."
        )

        actual_output, _, _ = invoke_agent_with_metrics(pdf_agent, question)

        # Detailed queries can be longer but should still be bounded
        length_metric = ResponseLengthMetric(min_length=200, max_length=5000)
        test_case = LLMTestCase(
            input=question,
            actual_output=actual_output,
        )
        assert_test(test_case, [length_metric])


class TestPDFAgentCombinedPerformance:
    """Combined performance tests evaluating multiple non-LLM metrics."""

    def test_comprehensive_performance(self, pdf_agent) -> None:
        """Test a typical query against all performance metrics."""
        question = (
            f"Load this PDF: {TEST_PDF_URL} "
            "What are the main safety evaluations described in this document?"
        )

        actual_output, completion_time, estimated_cost = invoke_agent_with_metrics(
            pdf_agent, question
        )

        # PDF loading + complex query can take time; use generous threshold
        latency_metric = LatencyMetric(max_latency_seconds=90.0)
        cost_metric = CostMetric(max_cost_usd=0.10)
        length_metric = ResponseLengthMetric(min_length=100, max_length=4000)

        test_case = LLMTestCase(
            input=question,
            actual_output=actual_output,
            completion_time=completion_time,
            token_cost=estimated_cost,
        )

        assert_test(test_case, [latency_metric, cost_metric, length_metric])
