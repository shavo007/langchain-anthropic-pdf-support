"""CLI entry point for the PDF Agent.

Run with: python -m pdf_agent
"""

import argparse
import logging

from dotenv import load_dotenv

from .agent import create_pdf_agent
from .core import analyze_pdf_from_url
from .logging_utils import (
    log_agent_messages,
    log_analyzing,
    log_error,
    log_header,
    log_response,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

# Sample PDF for demo
SAMPLE_PDF_URL = (
    "https://assets.anthropic.com/m/1cd9d098ac3e6467/"
    "original/Claude-3-Model-Card-October-Addendum.pdf"
)


def run_agent_demo(pdf_url: str) -> None:
    """Run the PDF agent demo.

    Args:
        pdf_url: URL of the PDF to analyze.
    """
    log_header("PDF Document Analyzer", use_agent=True)
    log_analyzing(pdf_url)

    agent = create_pdf_agent()

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Please load this PDF: {pdf_url} "
                        "Then tell me what the document is about and list 3 key points."
                    ),
                }
            ]
        }
    )

    log_agent_messages(response["messages"])

    final_message = response["messages"][-1].content
    log_response(str(final_message))


def run_direct_demo(pdf_url: str) -> None:
    """Run direct PDF analysis demo (without agent).

    Args:
        pdf_url: URL of the PDF to analyze.
    """
    log_header("PDF Document Analyzer", use_agent=False)
    log_analyzing(pdf_url)

    result = analyze_pdf_from_url(
        url=pdf_url,
        question="What are the key findings in this document? Please summarize in 3-5 bullet points.",
    )
    log_response(result)


def main() -> None:
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="PDF Document Analysis Agent powered by Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m pdf_agent                              # Run agent with default PDF
  python -m pdf_agent https://example.com/doc.pdf # Analyze custom PDF
  python -m pdf_agent --direct                    # Run direct analysis (no agent)
  python -m pdf_agent https://example.com/doc.pdf --direct  # Direct analysis on custom PDF
        """,
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=SAMPLE_PDF_URL,
        help="URL of the PDF to analyze (default: Claude 3 Model Card)",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Run direct PDF analysis instead of using the agent",
    )

    args = parser.parse_args()

    try:
        if args.direct:
            run_direct_demo(args.url)
        else:
            run_agent_demo(args.url)
    except Exception as e:
        log_error(str(e))
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
