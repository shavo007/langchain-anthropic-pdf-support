"""DeepEval evaluations for the PDF Agent.

This module contains LLM-based evaluations for testing the quality
of the PDF agent's responses using DeepEval metrics.

Run with: deepeval test run evals/test_pdf_agent_evals.py
Or with pytest: pytest evals/test_pdf_agent_evals.py -v
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

from pdf_agent import DEFAULT_MODEL, SONNET_MODEL


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


@pytest.fixture
def evaluation_model() -> AnthropicModel:
    """Create an Anthropic model for evaluation."""
    return AnthropicModel(model=get_eval_model_name(), temperature=0)


@pytest.fixture
def answer_relevancy_metric(evaluation_model: AnthropicModel) -> AnswerRelevancyMetric:
    """Create answer relevancy metric with Anthropic model."""
    return AnswerRelevancyMetric(threshold=0.7, model=evaluation_model, include_reason=True)


@pytest.fixture
def faithfulness_metric(evaluation_model: AnthropicModel) -> FaithfulnessMetric:
    """Create faithfulness metric with Anthropic model."""
    return FaithfulnessMetric(threshold=0.7, model=evaluation_model, include_reason=True)


@pytest.fixture
def helpfulness_metric(evaluation_model: AnthropicModel) -> GEval:
    """Create custom helpfulness metric using GEval."""
    return GEval(
        name="Helpfulness",
        criteria=(
            "Evaluate if the response is helpful and provides actionable information. "
            "Consider: Does it directly address the user's question? "
            "Is the information clear and well-structured? "
            "Does it provide specific details rather than vague generalities?"
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        model=evaluation_model,
        threshold=0.7,
    )


class TestPDFAgentAnswerRelevancy:
    """Test cases for answer relevancy evaluation."""

    def test_document_summary_relevancy(
        self, answer_relevancy_metric: AnswerRelevancyMetric
    ) -> None:
        """Test that document summaries are relevant to the summary request."""
        test_case = LLMTestCase(
            input="What is the main topic of this research paper?",
            actual_output=(
                "The main topic of this research paper is machine learning optimization "
                "techniques. The paper explores various gradient descent algorithms and "
                "their convergence properties, with a focus on adaptive learning rate methods "
                "such as Adam and RMSprop."
            ),
            retrieval_context=[
                "Abstract: This paper presents a comprehensive study of optimization "
                "algorithms used in deep learning. We analyze gradient descent variants "
                "including SGD, Adam, and RMSprop, comparing their convergence rates.",
                "Introduction: Machine learning models require efficient optimization "
                "techniques to train effectively on large datasets.",
            ],
        )
        assert_test(test_case, [answer_relevancy_metric])

    def test_specific_data_extraction_relevancy(
        self, answer_relevancy_metric: AnswerRelevancyMetric
    ) -> None:
        """Test that specific data extraction is relevant to the query."""
        test_case = LLMTestCase(
            input="What was the company's revenue in Q3 2024?",
            actual_output=(
                "According to the financial report, the company's revenue in Q3 2024 "
                "was $45.2 million, representing a 12% increase compared to the same "
                "quarter in the previous year."
            ),
            retrieval_context=[
                "Q3 2024 Financial Highlights: Revenue reached $45.2M, up 12% YoY. "
                "Operating margin improved to 18.5%.",
                "The strong performance was driven by growth in the enterprise segment.",
            ],
        )
        assert_test(test_case, [answer_relevancy_metric])


class TestPDFAgentFaithfulness:
    """Test cases for faithfulness (groundedness) evaluation."""

    def test_response_grounded_in_context(self, faithfulness_metric: FaithfulnessMetric) -> None:
        """Test that responses are grounded in the PDF content."""
        test_case = LLMTestCase(
            input="What are the key findings of this study?",
            actual_output=(
                "The study found three key findings: "
                "1) Early intervention programs reduce dropout rates by 35%, "
                "2) Parental involvement correlates with improved academic performance, "
                "3) Access to technology in classrooms improves engagement by 40%."
            ),
            retrieval_context=[
                "Key Findings: Our research demonstrates that early intervention "
                "programs can reduce student dropout rates by up to 35%.",
                "Additionally, we found a strong correlation between parental "
                "involvement and improved academic performance across all grade levels.",
                "Technology integration in classrooms showed a 40% improvement in "
                "student engagement metrics.",
            ],
        )
        assert_test(test_case, [faithfulness_metric])

    def test_numerical_accuracy(self, faithfulness_metric: FaithfulnessMetric) -> None:
        """Test that numerical data is accurately extracted from context."""
        test_case = LLMTestCase(
            input="What are the project milestones and deadlines?",
            actual_output=(
                "The project has the following milestones: "
                "Phase 1 completion by March 15, 2025, "
                "Phase 2 review on June 1, 2025, "
                "and final delivery scheduled for September 30, 2025."
            ),
            retrieval_context=[
                "Project Timeline: Phase 1 must be completed by March 15, 2025. "
                "Phase 2 review is scheduled for June 1, 2025. "
                "Final project delivery: September 30, 2025.",
            ],
        )
        assert_test(test_case, [faithfulness_metric])


class TestPDFAgentHelpfulness:
    """Test cases for helpfulness evaluation using GEval."""

    def test_clear_structured_response(self, helpfulness_metric: GEval) -> None:
        """Test that responses are clear and well-structured."""
        test_case = LLMTestCase(
            input="Can you summarize the installation requirements?",
            actual_output=(
                "Here are the installation requirements:\n\n"
                "**System Requirements:**\n"
                "- Operating System: Windows 10+, macOS 12+, or Ubuntu 20.04+\n"
                "- RAM: Minimum 8GB, recommended 16GB\n"
                "- Storage: 50GB free space\n\n"
                "**Software Prerequisites:**\n"
                "- Python 3.9 or higher\n"
                "- Node.js 18+\n"
                "- Docker (optional, for containerized deployment)\n\n"
                "Run `./install.sh` to begin the automated installation process."
            ),
        )
        assert_test(test_case, [helpfulness_metric])

    def test_actionable_troubleshooting(self, helpfulness_metric: GEval) -> None:
        """Test that troubleshooting responses provide actionable steps."""
        test_case = LLMTestCase(
            input="The PDF failed to load. What should I do?",
            actual_output=(
                "Here are steps to troubleshoot PDF loading issues:\n\n"
                "1. **Check the URL/file path**: Ensure the PDF URL is publicly accessible "
                "or the file path is correct and readable.\n\n"
                "2. **Verify file format**: Confirm the file is a valid PDF (not corrupted).\n\n"
                "3. **Check file size**: Large PDFs (>50MB) may timeout. Try with a smaller file.\n\n"
                "4. **Network issues**: For URL-based PDFs, verify your internet connection.\n\n"
                "5. **Try loading from file**: If URL fails, download the PDF and use "
                "`load_pdf_from_file` instead.\n\n"
                "If issues persist, check the error message for specific details."
            ),
        )
        assert_test(test_case, [helpfulness_metric])


class TestPDFAgentCombinedMetrics:
    """Test cases that evaluate multiple metrics together."""

    def test_comprehensive_document_analysis(
        self,
        answer_relevancy_metric: AnswerRelevancyMetric,
        faithfulness_metric: FaithfulnessMetric,
        helpfulness_metric: GEval,
    ) -> None:
        """Test a comprehensive document analysis against all metrics."""
        test_case = LLMTestCase(
            input="What are the main recommendations from the audit report?",
            actual_output=(
                "Based on the audit report, here are the main recommendations:\n\n"
                "1. **Strengthen Access Controls**: Implement multi-factor authentication "
                "for all administrative accounts (Priority: High)\n\n"
                "2. **Update Security Policies**: Review and update the information security "
                "policy to align with ISO 27001 standards (Priority: Medium)\n\n"
                "3. **Improve Backup Procedures**: Increase backup frequency from weekly to "
                "daily and test recovery procedures quarterly (Priority: High)\n\n"
                "4. **Employee Training**: Conduct mandatory security awareness training "
                "for all staff within 90 days (Priority: Medium)\n\n"
                "These recommendations should be addressed according to their priority levels "
                "to improve the organization's security posture."
            ),
            retrieval_context=[
                "Audit Recommendations Summary: "
                "1. Strengthen access controls - implement MFA for admin accounts (High Priority). "
                "2. Update information security policy to ISO 27001 standards (Medium Priority). "
                "3. Improve backup procedures - daily backups, quarterly recovery tests (High Priority). "
                "4. Conduct security awareness training for all employees within 90 days (Medium Priority).",
            ],
        )
        assert_test(
            test_case,
            [answer_relevancy_metric, faithfulness_metric, helpfulness_metric],
        )
