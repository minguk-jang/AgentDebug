#!/usr/bin/env python3
"""
.env 파일 설정 도우미

.env.example을 기반으로 .env 파일을 생성하거나,
기존 .env 파일을 검증합니다.
"""

import os
import sys

def main():
    print()
    print("=" * 72)
    print("  .env 파일 설정 도우미")
    print("=" * 72)
    print()

    env_file = '.env'
    example_file = '.env.example'

    # .env.example 확인
    if not os.path.exists(example_file):
        print(f"❌ 오류: {example_file} 파일이 없습니다.")
        return 1

    # .env 파일이 이미 존재하는지 확인
    if os.path.exists(env_file):
        print(f"⚠️  {env_file} 파일이 이미 존재합니다.")
        print()
        response = input("덮어쓰시겠습니까? (y/N): ").strip().lower()
        if response != 'y':
            print("취소되었습니다.")
            print()
            print("기존 .env 파일을 확인하려면:")
            print("  uv run check_env.py")
            return 0

    # .env.example 복사
    print()
    print(f"📋 {example_file}을 {env_file}로 복사 중...")

    with open(example_file, 'r') as f:
        content = f.read()

    with open(env_file, 'w') as f:
        f.write(content)

    print(f"✓ {env_file} 파일이 생성되었습니다!")
    print()
    print("━" * 72)
    print("다음 단계:")
    print("━" * 72)
    print()
    print("1. .env 파일을 편집기로 여세요:")
    print(f"   vi {env_file}")
    print(f"   nano {env_file}")
    print()
    print("2. 다음 값들을 실제 값으로 변경하세요:")
    print()

    # 필수 변수 표시
    required_vars = [
        ('OPENAI_API_KEY', 'sk-your-openai-api-key-here', 'OpenAI API 키'),
        ('LANGFUSE_PUBLIC_KEY', 'pk-lf-your-public-key-here', 'Langfuse public key'),
        ('LANGFUSE_SECRET_KEY', 'sk-lf-your-secret-key-here', 'Langfuse secret key'),
    ]

    for var_name, placeholder, description in required_vars:
        print(f"   {var_name}")
        print(f"   현재: {placeholder}")
        print(f"   설명: {description}")
        print()

    print("3. 선택 사항 (필요한 경우):")
    print()
    print("   OPENAI_BASE_URL")
    print("   - OpenAI 호환 API를 사용하는 경우 변경")
    print("   - 기본값: https://api.openai.com/v1/chat/completions")
    print()
    print("   OPENAI_MODEL")
    print("   - 사용할 LLM 모델")
    print("   - 기본값: gpt-4o")
    print()
    print("   LANGFUSE_HOST")
    print("   - Self-hosted Langfuse를 사용하는 경우 변경")
    print("   - 기본값: https://cloud.langfuse.com")
    print()

    print("━" * 72)
    print("4. 설정 확인:")
    print("━" * 72)
    print()
    print("   uv run check_env.py")
    print()
    print("=" * 72)

    return 0


if __name__ == "__main__":
    sys.exit(main())
