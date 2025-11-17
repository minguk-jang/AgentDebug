#!/usr/bin/env python3
"""
Langfuse Trace 구조 디버깅 도구

실제 Langfuse trace의 구조를 자세히 출력하여 변환 로직 개선에 활용합니다.
"""

import asyncio
import sys
import os
import json
import logging
from dotenv import load_dotenv
from langfuse_adapter import load_trace

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def print_dict_structure(data, indent=0, max_depth=5):
    """재귀적으로 dict 구조를 출력합니다."""
    if indent > max_depth:
        print("  " * indent + "... (max depth reached)")
        return

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print("  " * indent + f"📁 {key}: {type(value).__name__}")
                print_dict_structure(value, indent + 1, max_depth)
            else:
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                print("  " * indent + f"📄 {key}: {type(value).__name__} = {value_str}")

    elif isinstance(data, list):
        print("  " * indent + f"📋 List with {len(data)} items")
        if data:
            print("  " * indent + f"   First item type: {type(data[0]).__name__}")
            if len(data) > 0:
                print("  " * indent + "   First item structure:")
                print_dict_structure(data[0], indent + 1, max_depth)
            if len(data) > 1:
                print("  " * indent + f"   (... and {len(data) - 1} more items)")


async def debug_trace(trace_id: str):
    """Trace를 로드하고 구조를 상세히 출력합니다."""

    print()
    print("=" * 80)
    print("  LANGFUSE TRACE 구조 디버깅")
    print("=" * 80)
    print()
    print(f"🔍 Trace ID: {trace_id}")
    print()

    try:
        # Load trace
        print("━" * 80)
        print("1. Trace 로딩 중...")
        print("━" * 80)

        trace = await load_trace(trace_id)

        print(f"✓ Trace 로드 완료")
        print()

        # Save raw trace to file for detailed inspection
        output_file = f"results/debug_trace_{trace_id}.json"
        os.makedirs('results', exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(trace, f, indent=2, ensure_ascii=False, default=str)

        print(f"💾 원본 trace를 파일로 저장: {output_file}")
        print()

        # Print trace structure
        print("━" * 80)
        print("2. Trace 최상위 구조")
        print("━" * 80)
        print()

        for key in trace.keys():
            value = trace[key]
            if isinstance(value, (dict, list)):
                print(f"📁 {key}: {type(value).__name__}")
            else:
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                print(f"📄 {key}: {value_str}")

        print()

        # Print metadata details
        if 'metadata' in trace:
            print("━" * 80)
            print("3. Metadata 상세")
            print("━" * 80)
            print()
            print_dict_structure(trace['metadata'], indent=0, max_depth=3)
            print()

        # Print observations summary
        observations = trace.get('observations', [])
        print("━" * 80)
        print(f"4. Observations 요약 (총 {len(observations)}개)")
        print("━" * 80)
        print()

        if observations:
            # Group by type
            by_type = {}
            for obs in observations:
                obs_type = obs.get('type', 'UNKNOWN')
                if obs_type not in by_type:
                    by_type[obs_type] = []
                by_type[obs_type].append(obs)

            print(f"Observation 타입별 개수:")
            for obs_type, obs_list in by_type.items():
                print(f"  {obs_type}: {len(obs_list)}개")
            print()

            # Show first observation of each type
            for obs_type, obs_list in by_type.items():
                print(f"─── {obs_type} 타입 첫 번째 observation ───")
                print()
                print_dict_structure(obs_list[0], indent=0, max_depth=2)
                print()

        else:
            print("⚠️  Observations가 없습니다!")
            print()

        # Print trace input/output
        print("━" * 80)
        print("5. Trace Input/Output")
        print("━" * 80)
        print()

        trace_input = trace.get('input')
        trace_output = trace.get('output')

        print("Input:")
        if trace_input:
            print_dict_structure(trace_input, indent=1, max_depth=2)
        else:
            print("  (없음)")
        print()

        print("Output:")
        if trace_output:
            print_dict_structure(trace_output, indent=1, max_depth=2)
        else:
            print("  (없음)")
        print()

        # Analyze observations for conversion hints
        print("━" * 80)
        print("6. 변환을 위한 분석")
        print("━" * 80)
        print()

        if observations:
            print("Agent 단계로 추정되는 observations:")
            agent_steps = 0
            for i, obs in enumerate(observations):
                obs_type = obs.get('type')
                obs_name = obs.get('name', 'unnamed')
                has_output = bool(obs.get('output'))

                # Check if this looks like an agent step
                is_generation = obs_type == 'GENERATION'
                has_agent_like_name = any(word in obs_name.lower() for word in ['agent', 'step', 'llm', 'chat'])

                if is_generation or has_agent_like_name:
                    agent_steps += 1
                    print(f"  Step {agent_steps} (obs #{i}):")
                    print(f"    Type: {obs_type}")
                    print(f"    Name: {obs_name}")
                    print(f"    Has output: {has_output}")

                    # Check output structure
                    output = obs.get('output')
                    if output:
                        if isinstance(output, dict):
                            print(f"    Output keys: {list(output.keys())}")
                        elif isinstance(output, str):
                            preview = output[:100] + "..." if len(output) > 100 else output
                            print(f"    Output preview: {preview}")
                    print()

            if agent_steps == 0:
                print("  ⚠️  Agent 단계로 명확히 보이는 observation이 없습니다.")
                print()

        print("━" * 80)
        print("7. 권장 사항")
        print("━" * 80)
        print()

        print(f"1. 상세 trace 데이터 확인:")
        print(f"   cat {output_file} | jq '.'")
        print()
        print(f"2. Observations 확인:")
        print(f"   cat {output_file} | jq '.observations'")
        print()
        print(f"3. 첫 번째 observation 상세:")
        print(f"   cat {output_file} | jq '.observations[0]'")
        print()

        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


def main():
    """CLI main function."""

    if len(sys.argv) < 2:
        print()
        print("Usage: uv run debug_trace.py <trace_id>")
        print()
        print("Example:")
        print("  uv run debug_trace.py trace-abc-123")
        print()
        print("이 도구는 Langfuse trace의 구조를 상세히 분석하여")
        print("변환 로직을 개선하는 데 도움을 줍니다.")
        print()
        sys.exit(1)

    trace_id = sys.argv[1]

    # Validate environment variables
    required_vars = ['LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Please create a .env file or set these environment variables.")
        sys.exit(1)

    # Run debug
    asyncio.run(debug_trace(trace_id))


if __name__ == "__main__":
    main()
