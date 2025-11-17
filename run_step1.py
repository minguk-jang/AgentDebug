#!/usr/bin/env python3
"""
Step 1: Langfuse Trace → AgentDebug 형식 변환

로컬 JSON 파일에 저장된 Langfuse trace를 읽어서
AgentDebug가 원하는 형식으로 변환하고 결과를 출력합니다.

사용법:
    uv run python run_step1.py traces/my_trace.json
    uv run python run_step1.py traces/my_trace.json --output converted/output.json
"""

import sys
import os
import json
import logging
from pathlib import Path
from langfuse_adapter import convert_langfuse_to_agentdebug

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def load_trace_from_file(file_path: str) -> dict:
    """JSON 파일에서 Langfuse trace를 로드합니다."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        trace = json.load(f)

    return trace


def print_conversion_result(converted: dict):
    """변환 결과를 터미널에 보기 좋게 출력합니다."""

    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "Step 1: Langfuse → AgentDebug 변환 결과" + " " * 19 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Metadata 출력
    metadata = converted.get('metadata', {})

    print("━" * 80)
    print("📋 METADATA")
    print("━" * 80)
    print()
    print(f"  Task ID     : {metadata.get('task_id', 'N/A')}")
    print(f"  Environment : {metadata.get('environment', 'N/A')}")
    print(f"  Success     : {'✓ Yes' if metadata.get('success') else '✗ No'}")
    print(f"  Task        : {metadata.get('task', 'N/A')}")
    print()

    # Messages 출력
    messages = converted.get('messages', [])

    print("━" * 80)
    print(f"💬 MESSAGES (총 {len(messages)}개)")
    print("━" * 80)
    print()

    for i, msg in enumerate(messages, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')

        if role == 'user':
            print(f"[Message {i}] 👤 USER")
            print("─" * 80)
            # User 메시지는 간단히 출력
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"  {preview}")
            print()

        elif role == 'assistant':
            print(f"[Message {i}] 🤖 ASSISTANT")
            print("─" * 80)

            # XML 태그 파싱하여 모듈별로 출력
            modules = _parse_modules(content)

            if modules['memory']:
                print("  📝 Memory:")
                print(f"     {_truncate(modules['memory'], 150)}")
                print()

            if modules['reflection']:
                print("  🤔 Reflection:")
                print(f"     {_truncate(modules['reflection'], 150)}")
                print()

            if modules['plan']:
                print("  📋 Plan:")
                print(f"     {_truncate(modules['plan'], 150)}")
                print()

            if modules['action']:
                print("  ⚡ Action:")
                print(f"     {_truncate(modules['action'], 150)}")
                print()

            # 모듈이 없으면 원본 출력
            if not any(modules.values()):
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"  {preview}")
                print()

    # 통계 정보
    print("━" * 80)
    print("📊 통계")
    print("━" * 80)
    print()

    user_msgs = sum(1 for m in messages if m.get('role') == 'user')
    assistant_msgs = sum(1 for m in messages if m.get('role') == 'assistant')

    print(f"  총 메시지 수       : {len(messages)}")
    print(f"  User 메시지        : {user_msgs}")
    print(f"  Assistant 메시지   : {assistant_msgs}")

    # Agent 스텝 수 (assistant 메시지 = agent 스텝)
    print(f"  Agent 스텝 수      : {assistant_msgs}")
    print()

    # 모듈 통계
    module_counts = {
        'memory': 0,
        'reflection': 0,
        'plan': 0,
        'action': 0
    }

    for msg in messages:
        if msg.get('role') == 'assistant':
            modules = _parse_modules(msg.get('content', ''))
            for module_name, module_content in modules.items():
                if module_content:
                    module_counts[module_name] += 1

    print("  모듈별 출현 횟수:")
    print(f"    Memory     : {module_counts['memory']}/{assistant_msgs}")
    print(f"    Reflection : {module_counts['reflection']}/{assistant_msgs}")
    print(f"    Plan       : {module_counts['plan']}/{assistant_msgs}")
    print(f"    Action     : {module_counts['action']}/{assistant_msgs}")
    print()

    print("=" * 80)
    print()


def _parse_modules(content: str) -> dict:
    """XML 태그에서 모듈을 추출합니다."""
    import re

    modules = {
        'memory': '',
        'reflection': '',
        'plan': '',
        'action': ''
    }

    for module_name in modules.keys():
        pattern = f'<{module_name}>(.*?)</{module_name}>'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            modules[module_name] = match.group(1).strip()

    return modules


def _truncate(text: str, max_length: int) -> str:
    """텍스트를 자르고 ...을 추가합니다."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def save_converted(converted: dict, output_path: str):
    """변환 결과를 파일로 저장합니다."""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(converted, f, indent=2, ensure_ascii=False)

    print(f"💾 변환 결과 저장: {output_path}")
    print()


def main():
    """Main function"""

    if len(sys.argv) < 2:
        print()
        print("Usage: uv run python run_step1.py <trace-json-file> [--output <output-file>]")
        print()
        print("Examples:")
        print("  uv run python run_step1.py traces/my_trace.json")
        print("  uv run python run_step1.py traces/my_trace.json --output converted/result.json")
        print()
        print("Step 1: Langfuse trace를 AgentDebug 형식으로 변환합니다.")
        print()
        print("입력:")
        print("  - Langfuse trace JSON 파일 (traces/ 디렉토리에 저장)")
        print()
        print("출력:")
        print("  - 변환 결과를 터미널에 출력")
        print("  - --output 옵션으로 파일로도 저장 가능")
        print()
        sys.exit(1)

    input_file = sys.argv[1]

    # Check for output option
    output_file = None
    if len(sys.argv) > 2 and sys.argv[2] == '--output' and len(sys.argv) > 3:
        output_file = sys.argv[3]

    try:
        # Load trace from file
        print()
        print(f"📂 Langfuse trace 로딩 중: {input_file}")
        trace = load_trace_from_file(input_file)
        print(f"✓ 로드 완료")

        # Convert to AgentDebug format
        print(f"🔄 AgentDebug 형식으로 변환 중...")
        converted = convert_langfuse_to_agentdebug(trace)
        print(f"✓ 변환 완료")

        # Print result
        print_conversion_result(converted)

        # Save if output path specified
        if output_file:
            save_converted(converted, output_file)

        print("✅ Step 1 완료!")
        print()

    except FileNotFoundError as e:
        print(f"\n❌ 오류: {e}")
        print()
        print("traces/ 디렉토리에 Langfuse trace JSON 파일을 저장했는지 확인하세요.")
        print()
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"\n❌ JSON 파싱 오류: {e}")
        print()
        print("파일이 올바른 JSON 형식인지 확인하세요.")
        print()
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
