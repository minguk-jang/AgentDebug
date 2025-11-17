#!/usr/bin/env python3
"""
Phase 2 독립 실행 스크립트

Phase 1 결과를 받아서 Phase 2 (Critical error identification)만 실행하거나,
trace_id를 받아서 Phase 1 + Phase 2를 모두 실행합니다.

사용법:
    # Trace ID로 Phase 1 + Phase 2 실행
    uv run run_phase2.py <trace_id>

    # Phase 1 결과 파일로 Phase 2만 실행
    uv run run_phase2.py --phase1-results results/phase1_trace-abc-123.json

    # 결과 저장 위치 지정
    uv run run_phase2.py <trace_id> --output results/phase2_output.json
"""

import asyncio
import sys
import os
import json
import logging
from dotenv import load_dotenv
from agent.nodes import (
    load_trace_node,
    convert_trajectory_node,
    phase1_analysis_node,
    phase2_analysis_node
)
from agent.state import AnalysisState

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


async def run_phase2_only(phase1_results_file: str, output_file: str = None):
    """
    Phase 1 결과를 로드하고 Phase 2만 실행합니다.

    Args:
        phase1_results_file: Phase 1 결과 JSON 파일 경로
        output_file: 결과를 저장할 JSON 파일 경로 (옵션)

    Returns:
        Phase 2 분석 결과
    """
    print()
    print("╔" + "═" * 70 + "╗")
    print("║" + " " * 18 + "Phase 2: Critical Error Identification" + " " * 13 + "║")
    print("╚" + "═" * 70 + "╝")
    print()

    try:
        # Load Phase 1 results
        print("━" * 72)
        print("Loading Phase 1 results...")
        print("━" * 72)

        with open(phase1_results_file, 'r', encoding='utf-8') as f:
            phase1_data = json.load(f)

        trace_id = phase1_data.get("trace_id", "unknown")
        print(f"✓ Loaded Phase 1 results for trace: {trace_id}")
        print()

        # Initialize state with Phase 1 results
        state: AnalysisState = {
            "trace_id": trace_id,
            "raw_trace": None,
            "converted_trajectory": phase1_data.get("converted_trajectory"),
            "phase1_results": phase1_data.get("phase1_results"),
            "phase2_results": None,
            "report": None,
            "errors": []
        }

        # Run Phase 2
        print("━" * 72)
        print("Running Phase 2 analysis...")
        print("━" * 72)
        state = await phase2_analysis_node(state)

        if state["errors"]:
            print(f"❌ Error: {state['errors'][-1]}")
            return None

        results = state["phase2_results"]

        # Print results
        print()
        print("=" * 72)
        print("🔴 PHASE 2 RESULTS")
        print("=" * 72)
        print()

        if results.get('task_success'):
            print("✅ TASK SUCCEEDED")
            print()
            print("No critical error to identify - task completed successfully!")
        elif results.get('critical_error'):
            critical = results['critical_error']

            print(f"Critical Step: {critical.get('critical_step')}")
            print(f"Module: {critical.get('critical_module')}")
            print(f"Error Type: {critical.get('error_type')}")
            print(f"Confidence: {critical.get('confidence', 0):.2f}")
            print()

            print("━" * 72)
            print("Root Cause:")
            print("━" * 72)
            print(critical.get('root_cause', 'N/A'))
            print()

            print("━" * 72)
            print("Evidence:")
            print("━" * 72)
            print(critical.get('evidence', 'N/A'))
            print()

            print("━" * 72)
            print("💡 Correction Guidance:")
            print("━" * 72)
            print(critical.get('correction_guidance', 'N/A'))
            print()

            cascading = critical.get('cascading_effects', [])
            if cascading:
                print("━" * 72)
                print("Cascading Effects:")
                print("━" * 72)
                for effect in cascading:
                    step = effect.get('step', 'N/A')
                    effect_desc = effect.get('effect', 'N/A')
                    print(f"  • Step {step}: {effect_desc}")
                print()
        else:
            print("⚠️  No critical error identified")
            print()

        # Save to file if requested
        if output_file:
            os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

            output_data = {
                "trace_id": trace_id,
                "phase1_results": state["phase1_results"],
                "phase2_results": results,
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


async def run_phase1_and_phase2(trace_id: str, output_file: str = None):
    """
    Trace ID로부터 Phase 1과 Phase 2를 모두 실행합니다.

    Args:
        trace_id: Langfuse trace ID
        output_file: 결과를 저장할 JSON 파일 경로 (옵션)

    Returns:
        Phase 2 분석 결과
    """
    print()
    print("╔" + "═" * 70 + "╗")
    print("║" + " " * 22 + "Phase 1 + Phase 2 Analysis" + " " * 22 + "║")
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
        print("Step 1/4: Loading trace from Langfuse...")
        print("━" * 72)
        state = await load_trace_node(state)

        if state["errors"]:
            print(f"❌ Error: {state['errors'][-1]}")
            return None

        print(f"✓ Loaded {len(state['raw_trace'].get('observations', []))} observations")
        print()

        # Step 2: Convert to AgentDebug format
        print("━" * 72)
        print("Step 2/4: Converting to AgentDebug format...")
        print("━" * 72)
        state = await convert_trajectory_node(state)

        if state["errors"]:
            print(f"❌ Error: {state['errors'][-1]}")
            return None

        num_messages = len(state["converted_trajectory"].get("messages", []))
        print(f"✓ Converted to {num_messages} messages")
        print()

        # Step 3: Run Phase 1
        print("━" * 72)
        print("Step 3/4: Running Phase 1 analysis...")
        print("━" * 72)
        state = await phase1_analysis_node(state)

        if state["errors"]:
            print(f"❌ Error: {state['errors'][-1]}")
            return None

        total_steps = state["phase1_results"].get('total_steps', 0)
        print(f"✓ Phase 1 complete: {total_steps} steps analyzed")
        print()

        # Step 4: Run Phase 2
        print("━" * 72)
        print("Step 4/4: Running Phase 2 analysis...")
        print("━" * 72)
        state = await phase2_analysis_node(state)

        if state["errors"]:
            print(f"❌ Error: {state['errors'][-1]}")
            return None

        results = state["phase2_results"]

        # Print results
        print()
        print("=" * 72)
        print("🔴 PHASE 2 RESULTS")
        print("=" * 72)
        print()

        if results.get('task_success'):
            print("✅ TASK SUCCEEDED")
            print()
            print("No critical error to identify - task completed successfully!")
        elif results.get('critical_error'):
            critical = results['critical_error']

            print(f"Critical Step: {critical.get('critical_step')}")
            print(f"Module: {critical.get('critical_module')}")
            print(f"Error Type: {critical.get('error_type')}")
            print(f"Confidence: {critical.get('confidence', 0):.2f}")
            print()

            print("━" * 72)
            print("Root Cause:")
            print("━" * 72)
            print(critical.get('root_cause', 'N/A'))
            print()

            print("━" * 72)
            print("Evidence:")
            print("━" * 72)
            print(critical.get('evidence', 'N/A'))
            print()

            print("━" * 72)
            print("💡 Correction Guidance:")
            print("━" * 72)
            print(critical.get('correction_guidance', 'N/A'))
            print()

            cascading = critical.get('cascading_effects', [])
            if cascading:
                print("━" * 72)
                print("Cascading Effects:")
                print("━" * 72)
                for effect in cascading:
                    step = effect.get('step', 'N/A')
                    effect_desc = effect.get('effect', 'N/A')
                    print(f"  • Step {step}: {effect_desc}")
                print()
        else:
            print("⚠️  No critical error identified")
            print()

        # Save to file if requested
        if output_file:
            os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

            output_data = {
                "trace_id": trace_id,
                "phase1_results": state["phase1_results"],
                "phase2_results": results,
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
        print("Usage:")
        print("  # Run Phase 1 + Phase 2 from trace ID:")
        print("  uv run run_phase2.py <trace_id>")
        print()
        print("  # Run Phase 2 only from Phase 1 results:")
        print("  uv run run_phase2.py --phase1-results <phase1_results.json>")
        print()
        print("  # Specify output file:")
        print("  uv run run_phase2.py <trace_id> --output results/phase2.json")
        print()
        print("Examples:")
        print("  uv run run_phase2.py trace-abc-123")
        print("  uv run run_phase2.py --phase1-results results/phase1_trace-abc-123.json")
        print()
        sys.exit(1)

    # Validate environment variables
    required_vars = ['OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Please create a .env file or set these environment variables.")
        sys.exit(1)

    # Parse arguments
    if sys.argv[1] == '--phase1-results':
        if len(sys.argv) < 3:
            print("❌ Error: --phase1-results requires a file path")
            sys.exit(1)

        phase1_results_file = sys.argv[2]

        if not os.path.exists(phase1_results_file):
            print(f"❌ Error: File not found: {phase1_results_file}")
            sys.exit(1)

        # Check for output file
        output_file = None
        if len(sys.argv) > 3 and sys.argv[3] == '--output' and len(sys.argv) > 4:
            output_file = sys.argv[4]
        else:
            # Default output location
            base_name = os.path.splitext(os.path.basename(phase1_results_file))[0]
            output_file = f"results/phase2_{base_name.replace('phase1_', '')}.json"

        # Run Phase 2 only
        asyncio.run(run_phase2_only(phase1_results_file, output_file))

    else:
        # Run from trace ID (Phase 1 + Phase 2)
        trace_id = sys.argv[1]

        # Additional validation for Langfuse keys
        langfuse_vars = ['LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY']
        missing_langfuse = [var for var in langfuse_vars if not os.getenv(var)]

        if missing_langfuse:
            print("❌ Error: Missing required Langfuse environment variables:")
            for var in missing_langfuse:
                print(f"  - {var}")
            print()
            sys.exit(1)

        # Check for output file
        output_file = None
        if len(sys.argv) > 2 and sys.argv[2] == '--output' and len(sys.argv) > 3:
            output_file = sys.argv[3]
        else:
            # Default output location
            output_file = f"results/phase2_{trace_id}.json"

        # Run Phase 1 + Phase 2
        asyncio.run(run_phase1_and_phase2(trace_id, output_file))


if __name__ == "__main__":
    main()
