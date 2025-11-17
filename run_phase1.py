#!/usr/bin/env python3
"""
Phase 1 독립 실행 스크립트

Langfuse trace를 로드하고 Phase 1 (Fine-grained error detection)만 실행합니다.
결과는 JSON 파일로 저장됩니다.

사용법:
    uv run run_phase1.py <trace_id>
    uv run run_phase1.py <trace_id> --output results/phase1_output.json
"""

import asyncio
import sys
import os
import json
import logging
from dotenv import load_dotenv
from agent.nodes import load_trace_node, convert_trajectory_node, phase1_analysis_node
from agent.state import AnalysisState

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


async def run_phase1_only(trace_id: str, output_file: str = None):
    """
    Phase 1만 실행합니다.

    Args:
        trace_id: Langfuse trace ID
        output_file: 결과를 저장할 JSON 파일 경로 (옵션)

    Returns:
        Phase 1 분석 결과
    """
    print()
    print("╔" + "═" * 70 + "╗")
    print("║" + " " * 20 + "Phase 1: Fine-Grained Error Detection" + " " * 13 + "║")
    print("╚" + "═" * 70 + "╝")
    print()
    print(f"🔍 Trace ID: {trace_id}")
    print()

    # Initialize state
    state: AnalysisState = {
        "trace_id": trace_id,
        "raw_trace": None,
        "converted_trajectory": None,
        "phase1_results": None,
        "phase2_results": None,
        "report": None,
        "errors": []
    }

    try:
        # Step 1: Load trace
        print("━" * 72)
        print("Step 1/3: Loading trace from Langfuse...")
        print("━" * 72)
        state = await load_trace_node(state)

        if state["errors"]:
            print(f"❌ Error: {state['errors'][-1]}")
            return None

        print(f"✓ Loaded {len(state['raw_trace'].get('observations', []))} observations")
        print()

        # Step 2: Convert to AgentDebug format
        print("━" * 72)
        print("Step 2/3: Converting to AgentDebug format...")
        print("━" * 72)
        state = await convert_trajectory_node(state)

        if state["errors"]:
            print(f"❌ Error: {state['errors'][-1]}")
            return None

        num_messages = len(state["converted_trajectory"].get("messages", []))
        task = state["converted_trajectory"].get("metadata", {}).get("task", "N/A")
        print(f"✓ Converted to {num_messages} messages")
        print(f"  Task: {task[:100]}...")
        print()

        # Step 3: Run Phase 1 analysis
        print("━" * 72)
        print("Step 3/3: Running Phase 1 analysis...")
        print("━" * 72)
        state = await phase1_analysis_node(state)

        if state["errors"]:
            print(f"❌ Error: {state['errors'][-1]}")
            return None

        results = state["phase1_results"]

        # Print summary
        print()
        print("=" * 72)
        print("📊 PHASE 1 RESULTS SUMMARY")
        print("=" * 72)
        print()

        total_steps = results.get('total_steps', 0)
        task_success = results.get('task_success', False)

        print(f"Total Steps: {total_steps}")
        print(f"Task Success: {'✓ Yes' if task_success else '✗ No'}")
        print()

        # Count errors
        steps_with_errors = 0
        total_errors = 0

        for step in results.get('step_analyses', []):
            step_has_error = False
            for module, error_info in step.get('errors', {}).items():
                if error_info and error_info.get('error_detected'):
                    total_errors += 1
                    step_has_error = True
            if step_has_error:
                steps_with_errors += 1

        print(f"Steps with Errors: {steps_with_errors}/{total_steps}")
        print(f"Total Errors Found: {total_errors}")
        print()

        # Show step-by-step errors
        if steps_with_errors > 0:
            print("━" * 72)
            print("⚠️  ERRORS BY STEP")
            print("━" * 72)
            print()

            for step_analysis in results.get('step_analyses', []):
                step_num = step_analysis.get('step')
                errors_dict = step_analysis.get('errors', {})

                step_has_error = False
                for module, error_info in errors_dict.items():
                    if error_info and error_info.get('error_detected'):
                        if not step_has_error:
                            print(f"Step {step_num}:")
                            step_has_error = True

                        error_type = error_info.get('error_type', 'unknown')
                        reasoning = error_info.get('reasoning', 'N/A')
                        print(f"  ⚠️  {module}: {error_type}")
                        print(f"      {reasoning[:150]}...")

                if step_has_error:
                    print()

        # Save to file if requested
        if output_file:
            os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

            output_data = {
                "trace_id": trace_id,
                "phase1_results": results,
                "converted_trajectory": state["converted_trajectory"]
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print("━" * 72)
            print(f"💾 Results saved to: {output_file}")
            print("━" * 72)
            print()

        return results

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """CLI main function."""

    if len(sys.argv) < 2:
        print()
        print("Usage: uv run run_phase1.py <trace_id> [--output <file>]")
        print()
        print("Example:")
        print("  uv run run_phase1.py trace-abc-123")
        print("  uv run run_phase1.py trace-abc-123 --output results/phase1.json")
        print()
        sys.exit(1)

    trace_id = sys.argv[1]

    # Check for output file option
    output_file = None
    if len(sys.argv) > 2 and sys.argv[2] == '--output' and len(sys.argv) > 3:
        output_file = sys.argv[3]
    elif len(sys.argv) == 2:
        # Default output location
        output_file = f"results/phase1_{trace_id}.json"

    # Validate environment variables
    required_vars = ['OPENAI_API_KEY', 'LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Please create a .env file or set these environment variables.")
        sys.exit(1)

    # Run Phase 1
    asyncio.run(run_phase1_only(trace_id, output_file))


if __name__ == "__main__":
    main()
