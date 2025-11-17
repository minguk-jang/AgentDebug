# 환경 변수 설정 가이드

## 개요

이 프로젝트는 `python-dotenv`를 사용하여 `.env` 파일에서 환경 변수를 로드합니다.

## 빠른 시작

### 1. .env 파일 생성

```bash
# .env.example을 .env로 복사
cp .env.example .env
```

### 2. .env 파일 편집

```bash
# 편집기로 .env 파일 열기
vi .env
# 또는
nano .env
```

### 3. 필수 값 설정

```bash
# OpenAI API 설정 (필수)
OPENAI_API_KEY=sk-your-actual-openai-key-here
OPENAI_BASE_URL=https://api.openai.com/v1/chat/completions
OPENAI_MODEL=gpt-4o

# Langfuse API 설정 (필수)
LANGFUSE_PUBLIC_KEY=pk-lf-your-actual-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-actual-secret-key-here
LANGFUSE_HOST=https://cloud.langfuse.com

# 선택 사항
ENABLE_MODULE_DECOMPOSER=true
```

### 4. 설정 확인

```bash
uv run check_env.py
```

## 환경 변수 상세 설명

### OpenAI API 관련

#### OPENAI_API_KEY (필수)
- **설명**: OpenAI API 키
- **형식**: `sk-` 로 시작하는 문자열
- **예시**: `sk-proj-abc123...`
- **용도**: Phase 1, Phase 2 에러 분석에 사용되는 LLM API 호출

#### OPENAI_BASE_URL (선택)
- **설명**: OpenAI API 엔드포인트 URL
- **기본값**: `https://api.openai.com/v1/chat/completions`
- **형식**: `/chat/completions` 엔드포인트까지 포함된 전체 URL
- **주의**:
  - ✅ 올바름: `https://api.openai.com/v1/chat/completions`
  - ❌ 잘못됨: `https://api.openai.com/v1`
- **용도**: OpenAI 호환 API (예: Azure OpenAI, self-hosted) 사용 시

#### OPENAI_MODEL (선택)
- **설명**: 사용할 LLM 모델명
- **기본값**: `gpt-4o`
- **예시**: `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- **용도**: 에러 분석에 사용할 모델 지정

### Langfuse API 관련

#### LANGFUSE_PUBLIC_KEY (필수)
- **설명**: Langfuse public key
- **형식**: `pk-lf-` 로 시작하는 문자열
- **예시**: `pk-lf-abc123...`
- **용도**: Langfuse API 인증

#### LANGFUSE_SECRET_KEY (필수)
- **설명**: Langfuse secret key
- **형식**: `sk-lf-` 로 시작하는 문자열
- **예시**: `sk-lf-xyz789...`
- **용도**: Langfuse API 인증
- **주의**: ⚠️ 절대 git에 커밋하지 마세요!

#### LANGFUSE_HOST (선택)
- **설명**: Langfuse 서버 주소
- **기본값**: `https://cloud.langfuse.com`
- **예시**: `https://your-langfuse-instance.com`
- **용도**: Self-hosted Langfuse 사용 시

### 기타

#### HTTPS_PROXY (선택)
- **설명**: HTTP/HTTPS 프록시 서버
- **형식**: `http://host:port` 또는 `http://user:pass@host:port`
- **예시**: `http://proxy.company.com:8080`
- **용도**: 기업 방화벽 내에서 외부 API 호출 시

#### ENABLE_MODULE_DECOMPOSER (선택)
- **설명**: 모듈 분해 기능 활성화 여부
- **기본값**: `true`
- **가능한 값**: `true`, `false`
- **용도**: Plain text agent output을 LLM으로 분해하여 구조화

## load_dotenv() 동작 방식

### 모든 실행 스크립트에서 자동 로드

다음 스크립트들은 모두 시작 시 자동으로 `.env` 파일을 로드합니다:

1. **main.py** (전체 파이프라인)
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # 16번째 줄
   ```

2. **run_phase1.py** (Phase 1 독립 실행)
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # 23번째 줄
   ```

3. **run_phase2.py** (Phase 2 독립 실행)
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # 34번째 줄
   ```

4. **demo_phases.py** (픽스처 테스트)
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # 31번째 줄
   ```

5. **check_env.py** (환경 변수 확인)
   ```python
   from dotenv import load_dotenv
   load_dotenv()  # 52번째 줄
   ```

### 로드 우선순위

1. 환경 변수가 이미 설정되어 있으면 그 값 사용
2. `.env` 파일의 값으로 설정
3. 코드 내 기본값 사용

예시:
```python
# .env 파일에 OPENAI_MODEL=gpt-4o 라고 설정했다면
model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')  # 'gpt-4o' 반환

# .env 파일에 없는 값이면
timeout = os.getenv('API_TIMEOUT', '60')  # '60' 반환 (기본값)
```

## 문제 해결

### .env 파일이 로드되지 않는 경우

```bash
# 1. .env 파일 존재 확인
ls -la .env

# 2. .env 파일 위치 확인 (프로젝트 루트에 있어야 함)
pwd
# /home/user/AgentDebug 이어야 함

# 3. 환경 변수 확인
uv run check_env.py
```

### "Missing required environment variables" 오류

```bash
# 1. .env 파일이 있는지 확인
ls -la .env

# 2. 없다면 생성
cp .env.example .env

# 3. 필수 값 입력
vi .env

# 4. 확인
uv run check_env.py
```

### OPENAI_BASE_URL 형식 오류

```bash
# ❌ 잘못된 형식
OPENAI_BASE_URL=https://api.openai.com/v1

# ✅ 올바른 형식
OPENAI_BASE_URL=https://api.openai.com/v1/chat/completions
```

detector 코드는 `/chat/completions` 엔드포인트까지 포함된 전체 URL을 사용합니다.

### 프록시 관련 오류

프록시 환경에서 작동하지 않는 경우:

```bash
# .env 파일에 프록시 설정 추가
HTTPS_PROXY=http://your-proxy:port

# 또는 환경 변수로 직접 설정
export HTTPS_PROXY=http://your-proxy:port
```

## 보안 주의사항

### ⚠️ .env 파일 관리

1. **절대 git에 커밋하지 마세요**
   - `.gitignore`에 `.env`가 포함되어 있는지 확인
   ```bash
   cat .gitignore | grep "^\.env$"
   ```

2. **권한 설정**
   ```bash
   chmod 600 .env  # 본인만 읽기/쓰기
   ```

3. **백업**
   - `.env` 파일은 안전한 곳에 별도 백업
   - 버전 관리는 하지 말고 암호화된 저장소 사용

### ✅ .env.example 파일

- `.env.example`은 git에 커밋 가능
- 실제 값이 아닌 플레이스홀더만 포함
- 다른 개발자를 위한 템플릿 역할

## 테스트 환경에서 사용

### pytest에서 환경 변수 모킹

```python
# tests/conftest.py 또는 개별 테스트 파일
import pytest
import os

@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-test-key')
    monkeypatch.setenv('LANGFUSE_PUBLIC_KEY', 'pk-lf-test')
    monkeypatch.setenv('LANGFUSE_SECRET_KEY', 'sk-lf-test')
```

### CI/CD 환경

GitHub Actions 등에서는 secrets로 관리:

```yaml
# .github/workflows/test.yml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  LANGFUSE_PUBLIC_KEY: ${{ secrets.LANGFUSE_PUBLIC_KEY }}
  LANGFUSE_SECRET_KEY: ${{ secrets.LANGFUSE_SECRET_KEY }}
```

## 자주 묻는 질문

### Q: .env 파일 없이 환경 변수를 직접 export 해도 되나요?

A: 네, 가능합니다!

```bash
export OPENAI_API_KEY=sk-your-key
export LANGFUSE_PUBLIC_KEY=pk-lf-your-key
export LANGFUSE_SECRET_KEY=sk-lf-your-key
uv run main.py trace-abc-123
```

하지만 `.env` 파일을 사용하는 것이 더 편리합니다.

### Q: .env 파일 위치를 바꿀 수 있나요?

A: 기본적으로 프로젝트 루트의 `.env` 파일을 찾습니다.
다른 위치를 사용하려면:

```python
from dotenv import load_dotenv
load_dotenv('/path/to/your/.env')
```

### Q: 여러 .env 파일을 사용할 수 있나요?

A: 네, 환경별로 분리 가능합니다:

```bash
.env.development
.env.production
.env.test
```

로드 시:
```python
import os
env = os.getenv('ENV', 'development')
load_dotenv(f'.env.{env}')
```

## 관련 도구

- **check_env.py**: 환경 변수 검증
  ```bash
  uv run check_env.py
  ```

- **setup_env.py**: .env 파일 생성 도우미
  ```bash
  uv run setup_env.py
  ```

## 참고 자료

- [python-dotenv 공식 문서](https://github.com/theskumar/python-dotenv)
- [12-Factor App - Config](https://12factor.net/config)
