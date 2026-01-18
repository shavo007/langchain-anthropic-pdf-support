"""Integration evaluations for the PDF Agent.

This module tests the actual PDF agent with real PDF documents,
evaluating the quality of responses using DeepEval metrics.

Run with: uv run poe eval
Or directly: deepeval test run evals/test_pdf_agent_integration.py

Environment variables:
- PDF_AGENT_MODEL: Set to "sonnet" for higher-capability agent calls
- EVAL_MODEL: Set to "sonnet" for higher-capability evaluation calls
"""

import os

import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    GEval,
)
from deepeval.models import AnthropicModel
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from pdf_agent import DEFAULT_MODEL, SONNET_MODEL, create_pdf_agent, get_pdf_cache


def get_eval_model_name() -> str:
    """Get the model name for evaluations.

    Uses EVAL_MODEL environment variable if set:
    - "sonnet" -> uses Claude Sonnet 4.5 for higher-capability evaluations
    - other values -> used as-is
    - not set -> uses default Haiku model (cost-effective)
    """
    env_model = os.environ.get("EVAL_MODEL", "").lower()
    if env_model == "sonnet":
        return SONNET_MODEL
    elif env_model:
        return env_model
    return DEFAULT_MODEL


# Test PDF: Anthropic's Claude 3.5 Model Card Addendum
TEST_PDF_URL = "https://assets.anthropic.com/m/1cd9d098ac3e6467/original/Claude-3-Model-Card-October-Addendum.pdf"

# Key facts from the PDF for faithfulness evaluation
PDF_CONTEXT = [
    "This is the Model Card Addendum for Claude 3.5 Haiku and upgraded Claude 3.5 Sonnet, "
    "published by Anthropic in October 2024.",
    "The upgraded Claude 3.5 Sonnet introduces computer use capability - the ability to "
    "interpret screenshots and generate GUI commands to control computers. This allows "
    "the model to navigate websites, interact with user interfaces, and complete complex "
    "multi-step tasks autonomously.",
    "On OSWorld benchmark, Claude 3.5 Sonnet achieved 14.9% success rate with 15 steps "
    "and 22% with 50 steps, compared to human performance of 72.36%. This is state-of-the-art "
    "for AI models on this benchmark.",
    "SWE-bench Verified: Claude 3.5 Sonnet achieved 49.0% pass rate (state-of-the-art), "
    "Claude 3.5 Haiku achieved 40.6% which exceeds the original Claude 3.5 Sonnet.",
    "TAU-bench results: 69.2% on retail domain, 46.0% on airline domain for agentic "
    "customer service scenarios.",
    "Both models classified as ASL-2 (AI Safety Level 2) under Anthropic's Responsible "
    "Scaling Policy (RSP), indicating no catastrophic risk indicators were found.",
    "Safety evaluations included CBRN (Chemical, Biological, Radiological, Nuclear), "
    "cybersecurity vulnerability testing, and autonomous capability assessments. "
    "Multimodal red-teaming was conducted including specific evaluations for computer use.",
    "Independent pre-deployment assessments were conducted by US AI Safety Institute (AISI), "
    "UK AI Safety Institute (AISI), and METR to validate safety findings.",
    "Knowledge cutoff: April 2024 for upgraded Sonnet, July 2024 for Haiku.",
    "Vision capabilities show state-of-the-art results on MathVista, ChartQA, and AI2D benchmarks.",
]


@pytest.fixture(scope="module")
def evaluation_model() -> AnthropicModel:
    """Create an Anthropic model for evaluation."""
    return AnthropicModel(model=get_eval_model_name(), temperature=0)


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


@pytest.fixture
def answer_relevancy_metric(evaluation_model: AnthropicModel) -> AnswerRelevancyMetric:
    """Create answer relevancy metric."""
    return AnswerRelevancyMetric(threshold=0.7, model=evaluation_model, include_reason=True)


@pytest.fixture
def faithfulness_metric(evaluation_model: AnthropicModel) -> FaithfulnessMetric:
    """Create faithfulness metric.

    Note: Threshold is set to 0.5 because the agent reads the full PDF
    but we only provide partial retrieval_context for evaluation.
    The agent's responses may include accurate details not in our context.
    """
    return FaithfulnessMetric(threshold=0.5, model=evaluation_model, include_reason=True)


@pytest.fixture
def helpfulness_metric(evaluation_model: AnthropicModel) -> GEval:
    """Create helpfulness metric using GEval."""
    return GEval(
        name="Helpfulness",
        criteria=(
            "Evaluate if the response is helpful for understanding PDF content. "
            "Consider: Does it directly address the question? "
            "Is the information accurate and well-structured? "
            "Does it provide specific details from the document?"
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        model=evaluation_model,
        threshold=0.7,
    )


def invoke_agent(agent, question: str) -> str:
    """Invoke the PDF agent and return the final response."""
    response = agent.invoke({"messages": [{"role": "user", "content": question}]})
    # Get the last AI message content
    final_message = response["messages"][-1]
    return final_message.content


class TestPDFAgentIntegrationRelevancy:
    """Integration tests for answer relevancy with real PDF agent."""

    def test_document_overview_relevancy(
        self,
        pdf_agent,
        answer_relevancy_metric: AnswerRelevancyMetric,
    ) -> None:
        """Test that the agent provides relevant document overview."""
        question = (
            f"Please load this PDF: {TEST_PDF_URL} "
            "What is this document about? Give me a brief overview."
        )
        actual_output = invoke_agent(pdf_agent, question)

        test_case = LLMTestCase(
            input="What is this document about? Give me a brief overview.",
            actual_output=actual_output,
            retrieval_context=PDF_CONTEXT[:3],
        )
        assert_test(test_case, [answer_relevancy_metric])

    def test_specific_benchmark_query_relevancy(
        self,
        pdf_agent,
        answer_relevancy_metric: AnswerRelevancyMetric,
    ) -> None:
        """Test relevancy when asking about specific benchmarks."""
        question = (
            f"Load this PDF: {TEST_PDF_URL} "
            "What benchmark results are mentioned for the SWE-bench evaluation?"
        )
        actual_output = invoke_agent(pdf_agent, question)

        test_case = LLMTestCase(
            input="What benchmark results are mentioned for the SWE-bench evaluation?",
            actual_output=actual_output,
            retrieval_context=[PDF_CONTEXT[3]],
        )
        assert_test(test_case, [answer_relevancy_metric])


class TestPDFAgentIntegrationFaithfulness:
    """Integration tests for faithfulness with real PDF agent."""

    def test_safety_information_faithfulness(
        self,
        pdf_agent,
        faithfulness_metric: FaithfulnessMetric,
    ) -> None:
        """Test that safety-related responses are grounded in the PDF."""
        question = (
            f"Load this PDF: {TEST_PDF_URL} What safety evaluations were conducted on these models?"
        )
        actual_output = invoke_agent(pdf_agent, question)

        test_case = LLMTestCase(
            input="What safety evaluations were conducted on these models?",
            actual_output=actual_output,
            retrieval_context=PDF_CONTEXT[5:8],
        )
        assert_test(test_case, [faithfulness_metric])

    def test_numerical_data_faithfulness(
        self,
        pdf_agent,
        faithfulness_metric: FaithfulnessMetric,
    ) -> None:
        """Test that numerical data is accurately reported."""
        question = (
            f"Load this PDF: {TEST_PDF_URL} "
            "What is the OSWorld benchmark performance mentioned in the document?"
        )
        actual_output = invoke_agent(pdf_agent, question)

        test_case = LLMTestCase(
            input="What is the OSWorld benchmark performance?",
            actual_output=actual_output,
            retrieval_context=[PDF_CONTEXT[2]],
        )
        assert_test(test_case, [faithfulness_metric])


class TestPDFAgentIntegrationHelpfulness:
    """Integration tests for helpfulness with real PDF agent."""

    def test_key_points_extraction_helpfulness(
        self,
        pdf_agent,
        helpfulness_metric: GEval,
    ) -> None:
        """Test that key points extraction is helpful and well-structured."""
        question = (
            f"Load this PDF: {TEST_PDF_URL} "
            "List the 3 most important capabilities or features mentioned."
        )
        actual_output = invoke_agent(pdf_agent, question)

        test_case = LLMTestCase(
            input="List the 3 most important capabilities or features mentioned.",
            actual_output=actual_output,
        )
        assert_test(test_case, [helpfulness_metric])

    def test_comparison_query_helpfulness(
        self,
        pdf_agent,
        helpfulness_metric: GEval,
    ) -> None:
        """Test helpfulness when comparing models in the document."""
        question = (
            f"Load this PDF: {TEST_PDF_URL} "
            "How does Claude 3.5 Haiku compare to Claude 3.5 Sonnet based on this document?"
        )
        actual_output = invoke_agent(pdf_agent, question)

        test_case = LLMTestCase(
            input="How does Claude 3.5 Haiku compare to Claude 3.5 Sonnet?",
            actual_output=actual_output,
        )
        assert_test(test_case, [helpfulness_metric])


class TestPDFAgentIntegrationCombined:
    """Integration tests evaluating multiple metrics together."""

    def test_comprehensive_analysis(
        self,
        pdf_agent,
        answer_relevancy_metric: AnswerRelevancyMetric,
        faithfulness_metric: FaithfulnessMetric,
        helpfulness_metric: GEval,
    ) -> None:
        """Test comprehensive document analysis against all metrics."""
        question = (
            f"Load this PDF: {TEST_PDF_URL} "
            "Summarize the main findings about computer use capability, "
            "including specific benchmark results and safety considerations."
        )
        actual_output = invoke_agent(pdf_agent, question)

        test_case = LLMTestCase(
            input=(
                "Summarize the main findings about computer use capability, "
                "including specific benchmark results and safety considerations."
            ),
            actual_output=actual_output,
            retrieval_context=PDF_CONTEXT,
        )
        assert_test(
            test_case,
            [answer_relevancy_metric, faithfulness_metric, helpfulness_metric],
        )


class TestPDFAgentNegativeCases:
    """Negative test cases - agent should acknowledge when it doesn't know."""

    @pytest.fixture
    def appropriate_uncertainty_metric(self, evaluation_model: AnthropicModel) -> GEval:
        """Create metric for evaluating appropriate uncertainty acknowledgment."""
        return GEval(
            name="AppropriateUncertainty",
            criteria=(
                "Evaluate if the response appropriately acknowledges uncertainty or "
                "lack of information. The response should NOT make up information. "
                "Consider: Does it clearly state when information is not available? "
                "Does it avoid hallucinating or fabricating details? "
                "Does it suggest alternatives (like loading a PDF or checking the document)?"
            ),
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
            ],
            model=evaluation_model,
            threshold=0.7,
        )

    def test_question_about_missing_content(
        self,
        pdf_agent,
        appropriate_uncertainty_metric: GEval,
    ) -> None:
        """Test that agent acknowledges when asked about content NOT in the PDF."""
        # Load the PDF first
        question_load = f"Load this PDF: {TEST_PDF_URL}"
        invoke_agent(pdf_agent, question_load)

        # Ask about something definitely NOT in the Claude model card
        question = "What is the recipe for chocolate cake mentioned in this document?"
        actual_output = invoke_agent(pdf_agent, question)

        test_case = LLMTestCase(
            input=question,
            actual_output=actual_output,
        )
        assert_test(test_case, [appropriate_uncertainty_metric])

    def test_question_without_pdf_loaded(
        self,
        pdf_agent,
        appropriate_uncertainty_metric: GEval,
    ) -> None:
        """Test that agent acknowledges when no PDF is loaded."""
        # Don't load any PDF - cache is cleared by autouse fixture
        question = "What are the main findings in the document?"
        actual_output = invoke_agent(pdf_agent, question)

        test_case = LLMTestCase(
            input=question,
            actual_output=actual_output,
        )
        assert_test(test_case, [appropriate_uncertainty_metric])

    def test_question_about_different_topic(
        self,
        pdf_agent,
        appropriate_uncertainty_metric: GEval,
    ) -> None:
        """Test that agent doesn't fabricate info about unrelated topics."""
        # Load the PDF (about Claude models)
        question_load = f"Load this PDF: {TEST_PDF_URL}"
        invoke_agent(pdf_agent, question_load)

        # Ask about completely unrelated topic
        question = "According to this document, what is the population of Tokyo?"
        actual_output = invoke_agent(pdf_agent, question)

        test_case = LLMTestCase(
            input=question,
            actual_output=actual_output,
        )
        assert_test(test_case, [appropriate_uncertainty_metric])
