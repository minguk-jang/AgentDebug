#!/usr/bin/env python3
"""
Langfuse Trace 내부 구조 상세 확인 도구

특히 action_llm_node 같은 특정 observation의 구조를 확인합니다.
"""

import sys
import json
import re


def inspect_trace(file_path: str):
    """Trace 파일을 열어서 observations를 상세히 분석합니다."""

    with open(file_path, 'r', encoding='utf-8') as f:
        trace = json.load(f)

    print()
    print("=" * 80)
    print(f"  TRACE 구조 상세 분석: {file_path}")
    print("=" * 80)
    print()

    # Trace 기본 정보
    print(f"Trace ID: {trace.get('id', 'N/A')}")
    print(f"Name: {trace.get('name', 'N/A')}")
    print()

    # Observations 분석
    observations = trace.get('observations', [])
    print(f"총 Observations: {len(observations)}개")
    print()

    # Observation을 이름별로 그룹화
    by_name = {}
    for obs in observations:
        name = obs.get('name', 'unnamed')
        if name not in by_name:
            by_name[name] = []
        by_name[name].append(obs)

    print("━" * 80)
    print("Observation 이름별 분류:")
    print("━" * 80)
    for name, obs_list in sorted(by_name.items()):
        print(f"  {name}: {len(obs_list)}개")
    print()

    # action_llm_node 찾기
    action_llm_nodes = by_name.get('action_llm_node', [])

    if action_llm_nodes:
        print("━" * 80)
        print(f"🎯 action_llm_node 발견! (총 {len(action_llm_nodes)}개)")
        print("━" * 80)
        print()

        for i, node in enumerate(action_llm_nodes, 1):
            print(f"[action_llm_node #{i}]")
            print("─" * 80)

            # Type
            print(f"Type: {node.get('type', 'N/A')}")

            # Input
            input_data = node.get('input')
            print(f"\nInput type: {type(input_data).__name__}")
            if input_data:
                if isinstance(input_data, dict):
                    print(f"Input keys: {list(input_data.keys())}")
                else:
                    preview = str(input_data)[:200]
                    print(f"Input preview: {preview}...")

            # Output (이게 중요!)
            output_data = node.get('output')
            print(f"\nOutput type: {type(output_data).__name__}")

            if output_data:
                if isinstance(output_data, dict):
                    print(f"Output keys: {list(output_data.keys())}")
                    print()

                    # 각 키의 내용 미리보기
                    for key, value in output_data.items():
                        value_str = str(value)
                        preview = value_str[:150] + "..." if len(value_str) > 150 else value_str
                        print(f"  {key}:")
                        print(f"    {preview}")
                        print()

                elif isinstance(output_data, str):
                    # XML 태그가 있는지 확인
                    has_memory = '<memory>' in output_data
                    has_reflection = '<reflection>' in output_data
                    has_plan = '<plan>' in output_data
                    has_action = '<action>' in output_data

                    print(f"XML 태그 포함 여부:")
                    print(f"  <memory>: {has_memory}")
                    print(f"  <reflection>: {has_reflection}")
                    print(f"  <plan>: {has_plan}")
                    print(f"  <action>: {has_action}")
                    print()

                    if any([has_memory, has_reflection, has_plan, has_action]):
                        # XML 파싱
                        modules = parse_xml_modules(output_data)

                        if modules['memory']:
                            print("  📝 Memory:")
                            print(f"     {modules['memory'][:150]}...")
                            print()

                        if modules['reflection']:
                            print("  🤔 Reflection:")
                            print(f"     {modules['reflection'][:150]}...")
                            print()

                        if modules['plan']:
                            print("  📋 Plan:")
                            print(f"     {modules['plan'][:150]}...")
                            print()

                        if modules['action']:
                            print("  ⚡ Action:")
                            print(f"     {modules['action'][:150]}...")
                            print()
                    else:
                        preview = output_data[:300] + "..." if len(output_data) > 300 else output_data
                        print(f"Output content preview:")
                        print(f"{preview}")
                        print()

            # Metadata
            metadata = node.get('metadata', {})
            if metadata:
                print(f"Metadata keys: {list(metadata.keys())}")
                print()

            print("=" * 80)
            print()

    else:
        print("⚠️  action_llm_node를 찾을 수 없습니다!")
        print()
        print("다른 이름의 observations:")
        for name in sorted(by_name.keys())[:10]:
            print(f"  - {name}")
        print()

    # 모든 observation 중 output이 XML 형식인 것 찾기
    print("━" * 80)
    print("XML 형식 output을 가진 observations:")
    print("━" * 80)
    print()

    found_xml = False
    for obs in observations:
        output = obs.get('output')
        if isinstance(output, str) and '<memory>' in output:
            found_xml = True
            name = obs.get('name', 'unnamed')
            obs_type = obs.get('type', 'N/A')
            print(f"  ✓ {name} (type: {obs_type})")

    if not found_xml:
        print("  (없음)")
    print()


def parse_xml_modules(content: str) -> dict:
    """XML 태그에서 모듈을 추출합니다."""
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


def main():
    if len(sys.argv) < 2:
        print()
        print("Usage: uv run python inspect_trace.py <trace-json-file>")
        print()
        print("Example:")
        print("  uv run python inspect_trace.py traces/my_trace.json")
        print()
        print("이 도구는 Langfuse trace에서 action_llm_node 등")
        print("특정 observation의 구조를 상세히 분석합니다.")
        print()
        sys.exit(1)

    inspect_trace(sys.argv[1])


if __name__ == "__main__":
    main()
