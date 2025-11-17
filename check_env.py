#!/usr/bin/env python3
"""
환경 변수 로드 확인 스크립트

.env 파일이 제대로 로드되는지 확인하고,
모든 필수 환경 변수가 설정되어 있는지 검사합니다.
"""

import os
from dotenv import load_dotenv

# .env 파일 로드
print("=" * 72)
print("환경 변수 로드 확인")
print("=" * 72)
print()

# 현재 디렉토리와 .env 파일 위치 확인
cwd = os.getcwd()
env_file = os.path.join(cwd, '.env')

print(f"현재 디렉토리: {cwd}")
print(f".env 파일 경로: {env_file}")
print(f".env 파일 존재 여부: {os.path.exists(env_file)}")
print()

if os.path.exists(env_file):
    # 파일 내용 확인 (민감한 정보는 마스킹)
    print("━" * 72)
    print(".env 파일 내용 (값은 마스킹됨):")
    print("━" * 72)
    with open(env_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    # 값 마스킹
                    if value:
                        masked_value = value[:10] + '...' if len(value) > 10 else value
                        print(f"  {line_num:3d}: {key}={masked_value}")
                    else:
                        print(f"  {line_num:3d}: {key}= (빈 값)")
                else:
                    print(f"  {line_num:3d}: {line}")
    print()

# .env 로드
print("━" * 72)
print("dotenv로 .env 파일 로드 중...")
print("━" * 72)
load_dotenv()
print("✓ load_dotenv() 완료")
print()

# 필수 환경 변수 확인
print("━" * 72)
print("필수 환경 변수 확인:")
print("━" * 72)

env_vars = {
    'OpenAI 관련': [
        ('OPENAI_API_KEY', True),
        ('OPENAI_BASE_URL', False),
        ('OPENAI_MODEL', False),
    ],
    'Langfuse 관련': [
        ('LANGFUSE_PUBLIC_KEY', True),
        ('LANGFUSE_SECRET_KEY', True),
        ('LANGFUSE_HOST', False),
    ],
    '기타': [
        ('HTTPS_PROXY', False),
        ('ENABLE_MODULE_DECOMPOSER', False),
    ]
}

all_ok = True

for category, vars_list in env_vars.items():
    print(f"\n{category}:")
    for var_name, is_required in vars_list:
        value = os.getenv(var_name)

        if value:
            # 값 마스킹
            if 'KEY' in var_name or 'key' in var_name.lower():
                masked = value[:10] + '...' if len(value) > 10 else value
            else:
                masked = value

            print(f"  ✓ {var_name:30s} = {masked}")
        else:
            if is_required:
                print(f"  ✗ {var_name:30s} = (없음) ← 필수!")
                all_ok = False
            else:
                default = {
                    'OPENAI_BASE_URL': 'https://api.openai.com/v1/chat/completions',
                    'OPENAI_MODEL': 'gpt-4o',
                    'LANGFUSE_HOST': 'https://cloud.langfuse.com',
                    'ENABLE_MODULE_DECOMPOSER': 'true'
                }.get(var_name, 'N/A')
                print(f"  - {var_name:30s} = (없음, 기본값: {default})")

print()
print("=" * 72)

if all_ok:
    print("✅ 모든 필수 환경 변수가 설정되어 있습니다!")
else:
    print("❌ 일부 필수 환경 변수가 누락되었습니다.")
    print()
    print("해결 방법:")
    print("1. .env 파일을 열어서 누락된 변수를 추가하세요")
    print("2. .env.example 파일을 참고하세요")
    print("3. 또는 export 명령으로 환경 변수를 직접 설정하세요:")
    print("   export OPENAI_API_KEY=sk-your-key-here")

print("=" * 72)
print()

# OPENAI_BASE_URL 값 검증
print("━" * 72)
print("OPENAI_BASE_URL 검증:")
print("━" * 72)

base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1/chat/completions')
print(f"현재 값: {base_url}")

if '/chat/completions' in base_url:
    print("✓ 올바른 형식입니다. (엔드포인트 포함)")
elif base_url.endswith('/v1'):
    print("⚠️  경고: 엔드포인트가 누락되었습니다.")
    print("   detector 코드는 '/chat/completions'까지 포함된 URL을 기대합니다.")
    print(f"   권장 값: {base_url}/chat/completions")
else:
    print("⚠️  경고: 예상하지 못한 형식입니다.")
    print("   권장 값: https://api.openai.com/v1/chat/completions")

print()
