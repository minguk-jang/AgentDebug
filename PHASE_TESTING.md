# Phase 별 독립 테스트 가이드

Phase 1과 Phase 2를 각각 독립적으로 실행하고 테스트할 수 있는 방법을 설명합니다.

## 빠른 시작: 픽스처로 테스트하기

실제 Langfuse API 없이 테스트 픽스처로 Phase를 테스트할 수 있습니다:

```bash
# 성공 케이스로 Phase 1 + Phase 2 테스트
uv run demo_phases.py --fixture success

# 실패 케이스로 테스트
uv run demo_phases.py --fixture failure

# Plain text 케이스로 테스트
uv run demo_phases.py --fixture plaintext

# Phase 1만 테스트
uv run demo_phases.py --fixture success --phase1-only
```

결과는 `results/` 디렉토리에 저장됩니다.

## 개요

- **Phase 1**: Fine-grained Error Detection (17가지 에러 타입 탐지)
- **Phase 2**: Critical Error Identification (가장 치명적인 에러 식별)

## 사용법

### 1. Phase 1만 실행하기

```bash
# 기본 사용법
uv run run_phase1.py <trace_id>

# 결과 파일 위치 지정
uv run run_phase1.py <trace_id> --output results/my_phase1.json
```

**출력 내용:**
- Trace 로딩 정보
- AgentDebug 포맷 변환 정보
- Phase 1 분석 결과:
  - 총 스텝 수
  - 태스크 성공 여부
  - 에러가 발견된 스텝 수
  - 각 스텝별 상세 에러 정보

**결과 파일:**
- `results/phase1_<trace_id>.json`에 자동 저장됩니다
- 포함 내용:
  - `trace_id`: Langfuse trace ID
  - `phase1_results`: Phase 1 분석 결과
  - `converted_trajectory`: 변환된 trajectory 데이터

### 2. Phase 2만 실행하기 (Phase 1 결과로부터)

Phase 1 결과 파일을 이용해서 Phase 2만 실행할 수 있습니다:

```bash
# Phase 1 결과 파일 사용
uv run run_phase2.py --phase1-results results/phase1_trace-abc-123.json

# 결과 파일 위치 지정
uv run run_phase2.py --phase1-results results/phase1_trace-abc-123.json --output results/my_phase2.json
```

**출력 내용:**
- Phase 1 결과 로딩 정보
- Phase 2 분석 결과:
  - Critical Step (어느 스텝에서 치명적 에러 발생)
  - Critical Module (어느 모듈에서 발생)
  - Error Type (에러 타입)
  - Root Cause (근본 원인)
  - Evidence (증거)
  - Correction Guidance (수정 가이드)
  - Cascading Effects (연쇄 효과)

### 3. Phase 1 + Phase 2 함께 실행하기

처음부터 끝까지 한 번에 실행:

```bash
# Trace ID로 Phase 1 + Phase 2 실행
uv run run_phase2.py <trace_id>

# 결과 파일 위치 지정
uv run run_phase2.py <trace_id> --output results/full_analysis.json
```

### 4. 전체 파이프라인 실행하기 (기존 방식)

전체 파이프라인 (Load → Convert → Phase1 → Phase2 → Report):

```bash
uv run main.py <trace_id>
```

## 테스트 워크플로우 예시

### 워크플로우 1: 단계별 디버깅

```bash
# 1. Phase 1 실행하여 에러 탐지
uv run run_phase1.py trace-abc-123

# 2. Phase 1 결과 확인
cat results/phase1_trace-abc-123.json | jq '.phase1_results.step_analyses[0]'

# 3. Phase 1 결과로 Phase 2 실행
uv run run_phase2.py --phase1-results results/phase1_trace-abc-123.json

# 4. Phase 2 결과 확인
cat results/phase2_trace-abc-123.json | jq '.phase2_results.critical_error'
```

### 워크플로우 2: Phase 1 결과 재사용

Phase 1은 시간이 걸리므로, 한 번 실행한 결과를 여러 번 재사용할 수 있습니다:

```bash
# 1. Phase 1 한 번만 실행
uv run run_phase1.py trace-abc-123

# 2. 필요할 때마다 Phase 2만 재실행 (빠름!)
uv run run_phase2.py --phase1-results results/phase1_trace-abc-123.json
uv run run_phase2.py --phase1-results results/phase1_trace-abc-123.json
```

### 워크플로우 3: 배치 분석

여러 trace를 한꺼번에 분석:

```bash
# Phase 1만 여러 trace에 대해 실행
for trace_id in trace-001 trace-002 trace-003; do
    uv run run_phase1.py $trace_id
done

# 모든 Phase 1 결과를 Phase 2로 분석
for file in results/phase1_*.json; do
    uv run run_phase2.py --phase1-results $file
done
```

## 결과 파일 구조

### Phase 1 결과 (`results/phase1_<trace_id>.json`)

```json
{
  "trace_id": "trace-abc-123",
  "phase1_results": {
    "total_steps": 5,
    "task_success": false,
    "task_description": "Search for wireless headphones",
    "step_analyses": [
      {
        "step": 1,
        "errors": {
          "memory": {
            "error_detected": false,
            "error_type": null,
            "reasoning": "..."
          },
          "reflection": {...},
          "plan": {...},
          "action": {...}
        }
      }
    ]
  },
  "converted_trajectory": {
    "messages": [...],
    "metadata": {...}
  }
}
```

### Phase 2 결과 (`results/phase2_<trace_id>.json`)

```json
{
  "trace_id": "trace-abc-123",
  "phase1_results": {...},
  "phase2_results": {
    "task_success": false,
    "critical_error": {
      "critical_step": 3,
      "critical_module": "action",
      "error_type": "Incorrect Tool Use",
      "root_cause": "The agent used the wrong search parameters...",
      "evidence": "In step 3, the agent called search_products()...",
      "correction_guidance": "The agent should validate search parameters...",
      "cascading_effects": [
        {
          "step": 4,
          "effect": "Due to incorrect search results..."
        }
      ],
      "confidence": 0.95
    }
  },
  "converted_trajectory": {
    "messages": [...],
    "metadata": {...}
  }
}
```

## 환경 변수

### Phase 1 실행에 필요한 환경 변수:
- `OPENAI_API_KEY`: OpenAI API 키
- `LANGFUSE_PUBLIC_KEY`: Langfuse public key
- `LANGFUSE_SECRET_KEY`: Langfuse secret key
- `LANGFUSE_HOST` (선택): Langfuse 호스트 (기본값: https://cloud.langfuse.com)

### Phase 2 단독 실행 시 (Phase 1 결과 파일 사용):
- `OPENAI_API_KEY`: OpenAI API 키만 필요
- Langfuse 키는 불필요 (이미 데이터를 가지고 있으므로)

## 팁

1. **빠른 테스트**: Phase 1 결과를 저장해두고 Phase 2만 반복 실행하면 빠르게 테스트할 수 있습니다
2. **결과 비교**: 다른 설정으로 Phase 2를 여러 번 실행하고 결과를 비교할 수 있습니다
3. **오프라인 분석**: Phase 1 결과 파일만 있으면 Langfuse API 없이도 Phase 2를 실행할 수 있습니다
4. **JSON 분석**: `jq` 명령어를 사용하면 결과 파일을 쉽게 분석할 수 있습니다

## 문제 해결

### "Langfuse object has no attribute fetch_trace" 에러
- Langfuse SDK가 v2와 v3를 모두 지원하도록 수정되었습니다
- `uv sync`를 실행하여 최신 코드로 업데이트하세요

### Phase 2에서 "No Phase 1 results available" 에러
- Phase 1 결과 파일 경로가 올바른지 확인하세요
- `--phase1-results` 옵션을 사용했는지 확인하세요

### 결과 파일을 찾을 수 없음
- 기본적으로 `results/` 디렉토리에 저장됩니다
- `--output` 옵션으로 원하는 위치를 지정할 수 있습니다
