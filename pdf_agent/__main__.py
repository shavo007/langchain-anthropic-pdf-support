"""CLI entry point for the PDF Agent.

Run with: python -m pdf_agent
"""

import argparse
import logging

from dotenv import load_dotenv

from .agent import create_pdf_agent, log_agent_messages
from .core import analyze_pdf_from_url

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

# Sample PDF for demo
SAMPLE_PDF_URL = (
    "https://assets.anthropic.com/m/1cd9d098ac3e6467/"
    "original/Claude-3-Model-Card-October-Addendum.pdf"
)


def run_agent_demo() -> None:
    """Run the PDF agent demo."""
    print("=" * 60)
    print("PDF Agent Demo")
    print("=" * 60)

    agent = create_pdf_agent()

    print(f"\nAnalyzing PDF: {SAMPLE_PDF_URL[:50]}...")
    print("-" * 60)

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Please load this PDF: {SAMPLE_PDF_URL} "
                        "Then tell me what the document is about and list 3 key points."
                    ),
                }
            ]
        }
    )

    log_agent_messages(response["messages"])

    final_message = response["messages"][-1].content
    print(f"\nAgent Response:\n{final_message}")
    print("\n" + "=" * 60)


def run_direct_demo() -> None:
    """Run direct PDF analysis demo (without agent)."""
    print("=" * 60)
    print("Direct PDF Analysis Demo (no agent)")
    print("=" * 60)

    print(f"\nAnalyzing PDF: {SAMPLE_PDF_URL[:50]}...")
    print("-" * 60)

    result = analyze_pdf_from_url(
        url=SAMPLE_PDF_URL,
        question="What are the key findings in this document? Please summarize in 3-5 bullet points.",
    )
    print(f"Response:\n{result}")
    print("\n" + "=" * 60)


def main() -> None:
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="PDF Document Analysis Agent powered by Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m pdf_agent              # Run agent demo (default)
  python -m pdf_agent --direct     # Run direct analysis demo
        """,
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Run direct PDF analysis instead of using the agent",
    )

    args = parser.parse_args()

    try:
        if args.direct:
            run_direct_demo()
        else:
            run_agent_demo()
    except Exception as e:
        print(f"Error: {e}")
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
