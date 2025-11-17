#!/usr/bin/env python3
"""
Langfuse Agent Debugger - Main CLI

Analyzes Langfuse agent trajectories using AgentDebug error detection.
"""

import asyncio
import sys
import os
import logging
from dotenv import load_dotenv
from agent.graph import create_analysis_graph

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simple format for CLI output
)
logger = logging.getLogger(__name__)


async def main():
    """Main CLI function."""

    # Check for trace_id argument
    if len(sys.argv) < 2:
        print("╔" + "═" * 70 + "╗")
        print("║" + " " * 15 + "Langfuse Agent Debugger - AgentDebug System" + " " * 12 + "║")
        print("╚" + "═" * 70 + "╝")
        print()
        print("Usage: uv run main.py <trace_id>")
        print("       python main.py <trace_id>")
        print()
        print("Example:")
        print("  uv run main.py trace-abc-123-def")
        print()
        print("Environment variables required:")
        print("  OPENAI_API_KEY       - OpenAI API key for error analysis")
        print("  LANGFUSE_PUBLIC_KEY  - Langfuse public key")
        print("  LANGFUSE_SECRET_KEY  - Langfuse secret key")
        print()
        print("Optional:")
        print("  OPENAI_BASE_URL      - Custom OpenAI-compatible API endpoint")
        print("  OPENAI_MODEL         - Model to use (default: gpt-4o)")
        print("  LANGFUSE_HOST        - Langfuse host (default: https://cloud.langfuse.com)")
        print("  HTTPS_PROXY          - HTTP proxy for API calls")
        print()
        sys.exit(1)

    trace_id = sys.argv[1]

    # Validate environment variables
    required_vars = [
        'OPENAI_API_KEY',
        'LANGFUSE_PUBLIC_KEY',
        'LANGFUSE_SECRET_KEY'
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Please create a .env file or set these environment variables.")
        print("See .env.example for reference.")
        sys.exit(1)

    # Print header
    print()
    print("╔" + "═" * 70 + "╗")
    print("║" + " " * 15 + "Langfuse Agent Debugger - AgentDebug System" + " " * 12 + "║")
    print("╚" + "═" * 70 + "╝")
    print()
    print(f"🔍 Analyzing Langfuse trace: {trace_id}")
    print()

    # Create graph
    logger.info("Initializing analysis pipeline...")
    graph = create_analysis_graph()

    # Initial state
    initial_state = {
        "trace_id": trace_id,
        "raw_trace": None,
        "converted_trajectory": None,
        "phase1_results": None,
        "phase2_results": None,
        "report": None,
        "errors": []
    }

    # Run analysis
    try:
        logger.info("Starting analysis...\n")
        result = await graph.ainvoke(initial_state)

        print()
        print("=" * 72)
        print()

        # Print report
        if result.get("report"):
            print(result["report"])
        else:
            print("❌ Analysis failed - no report generated")

        # Print errors if any occurred
        if result.get("errors"):
            print()
            print("=" * 72)
            print("⚠️  ERRORS DURING ANALYSIS:")
            print("=" * 72)
            for i, error in enumerate(result["errors"], 1):
                print(f"{i}. {error}")

        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cli():
    """Entry point for uv script."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(130)


if __name__ == "__main__":
    cli()
