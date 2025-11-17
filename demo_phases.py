#!/usr/bin/env python3
"""
픽스처를 사용한 Phase 테스트 스크립트

실제 Langfuse API 호출 없이 테스트 픽스처로 Phase 1과 Phase 2를 테스트합니다.

사용법:
    # 성공 케이스 테스트
    uv run test_phases.py --fixture success

    # 실패 케이스 테스트
    uv run test_phases.py --fixture failure

    # Plain text 케이스 테스트
    uv run test_phases.py --fixture plaintext

    # Phase 1만 테스트
    uv run test_phases.py --fixture success --phase1-only
"""

import asyncio
import sys
import os
import json
import logging
from dotenv import load_dotenv
from agent.nodes import convert_trajectory_node, phase1_analysis_node, phase2_analysis_node
from agent.state import AnalysisState

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


FIXTURES = {
    'success': 'tests/fixtures/sample_trace_success.json',
    'failure': 'tests/fixtures/sample_trace_failure.json',
    'plaintext': 'tests/fixtures/sample_trace_plaintext.json'
}


async def test_with_fixture(fixture_name: str, phase1_only: bool = False):
    """
    픽스처로 Phase 테스트를 실행합니다.

    Args:
        fixture_name: 'success', 'failure', 또는 'plaintext'
        phase1_only: True면 Phase 1만 실행
    """
    if fixture_name not in FIXTURES:
        print(f"❌ Unknown fixture: {fixture_name}")
        print(f"Available fixtures: {', '.join(FIXTURES.keys())}")
        return

    fixture_path = FIXTURES[fixture_name]

    if not os.path.exists(fixture_path):
        print(f"❌ Fixture file not found: {fixture_path}")
        return

    print()
    print("╔" + "═" * 70 + "╗")
    print("║" + " " * 20 + "Phase Testing with Fixture" + " " * 24 + "║")
    print("╚" + "═" * 70 + "╝")
    print()
    print(f"📋 Fixture: {fixture_name}")
    print(f"📁 File: {fixture_path}")
    print()

    try:
        # Load fixture
        print("━" * 72)
        print("Loading fixture...")
        print("━" * 72)

        with open(fixture_path, 'r', encoding='utf-8') as f:
            raw_trace = json.load(f)

        print(f"✓ Loaded fixture with {len(raw_trace.get('observations', []))} observations")
        print()

        # Initialize state
        state: AnalysisState = {
            "trace_id": raw_trace.get('id', 'fixture-test'),
            "raw_trace": raw_trace,
            "converted_trajectory": None,
            "phase1_results": None,
            "phase2_results": None,
            "report": None,
            "errors": []
        }

        # Step 1: Convert to AgentDebug format
        print("━" * 72)
        print("Step 1: Converting to AgentDebug format...")
        print("━" * 72)
        state = await convert_trajectory_node(state)

        if state["errors"]:
            print(f"❌ Conversion error: {state['errors'][-1]}")
            return

        num_messages = len(state["converted_trajectory"].get("messages", []))
        task = state["converted_trajectory"].get("metadata", {}).get("task", "N/A")
        print(f"✓ Converted to {num_messages} messages")
        print(f"  Task: {task[:100]}...")
        print()

        # Step 2: Run Phase 1
        print("━" * 72)
        print("Step 2: Running Phase 1 analysis...")
        print("━" * 72)
        state = await phase1_analysis_node(state)

        if state["errors"]:
            print(f"❌ Phase 1 error: {state['errors'][-1]}")
            return

        results = state["phase1_results"]

        # Print Phase 1 summary
        print()
        print("=" * 72)
        print("📊 PHASE 1 RESULTS")
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

        # Show errors
        if steps_with_errors > 0:
            print("━" * 72)
            print("⚠️  ERRORS FOUND")
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
                        print(f"      {reasoning[:200]}...")

                if step_has_error:
                    print()

        # Save Phase 1 results
        output_file = f"results/test_phase1_{fixture_name}.json"
        os.makedirs('results', exist_ok=True)

        output_data = {
            "trace_id": state["trace_id"],
            "fixture": fixture_name,
            "phase1_results": results,
            "converted_trajectory": state["converted_trajectory"]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print("━" * 72)
        print(f"💾 Phase 1 results saved to: {output_file}")
        print("━" * 72)
        print()

        # Stop here if phase1_only
        if phase1_only:
            print("✓ Phase 1 testing complete!")
            return

        # Step 3: Run Phase 2
        print("━" * 72)
        print("Step 3: Running Phase 2 analysis...")
        print("━" * 72)
        state = await phase2_analysis_node(state)

        if state["errors"]:
            print(f"❌ Phase 2 error: {state['errors'][-1]}")
            return

        phase2_results = state["phase2_results"]

        # Print Phase 2 results
        print()
        print("=" * 72)
        print("🔴 PHASE 2 RESULTS")
        print("=" * 72)
        print()

        if phase2_results.get('task_success'):
            print("✅ TASK SUCCEEDED")
            print()
            print("No critical error to identify - task completed successfully!")
        elif phase2_results.get('critical_error'):
            critical = phase2_results['critical_error']

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

        # Save Phase 2 results
        output_file = f"results/test_phase2_{fixture_name}.json"

        output_data = {
            "trace_id": state["trace_id"],
            "fixture": fixture_name,
            "phase1_results": state["phase1_results"],
            "phase2_results": phase2_results,
            "converted_trajectory": state["converted_trajectory"]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print("━" * 72)
        print(f"💾 Phase 2 results saved to: {output_file}")
        print("━" * 72)
        print()

        print("✓ Phase 1 + Phase 2 testing complete!")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """CLI main function."""

    if len(sys.argv) < 2:
        print()
        print("Usage: uv run test_phases.py --fixture <fixture_name> [--phase1-only]")
        print()
        print("Available fixtures:")
        for name, path in FIXTURES.items():
            print(f"  - {name}: {path}")
        print()
        print("Examples:")
        print("  uv run test_phases.py --fixture success")
        print("  uv run test_phases.py --fixture failure")
        print("  uv run test_phases.py --fixture plaintext --phase1-only")
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
    fixture_name = None
    phase1_only = False

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--fixture' and i + 1 < len(sys.argv):
            fixture_name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--phase1-only':
            phase1_only = True
            i += 1
        else:
            print(f"❌ Unknown argument: {sys.argv[i]}")
            sys.exit(1)

    if not fixture_name:
        print("❌ Error: --fixture option is required")
        sys.exit(1)

    # Run test
    asyncio.run(test_with_fixture(fixture_name, phase1_only))


if __name__ == "__main__":
    main()
