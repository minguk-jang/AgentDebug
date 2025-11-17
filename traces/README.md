# Langfuse Trace 저장소

이 디렉토리는 Langfuse trace JSON 파일을 저장하는 곳입니다.

## 사용법

### 1. Langfuse trace JSON 파일 저장

Langfuse에서 trace를 JSON으로 내보내서 이 디렉토리에 저장하세요:

```bash
# 예시
traces/
├── my_agent_trace_001.json
├── my_agent_trace_002.json
└── example_trace.json  (샘플)
```

### 2. Step 1 실행: Langfuse → AgentDebug 변환

```bash
# 기본 사용 (터미널에 출력)
uv run python run_step1.py traces/my_agent_trace_001.json

# 결과를 파일로 저장
uv run python run_step1.py traces/my_agent_trace_001.json --output converted/result.json
```

### 3. 출력 내용

Step 1 스크립트는 다음을 보여줍니다:

- **Metadata**: Task ID, 성공 여부, Task 설명
- **Messages**: User와 Assistant 메시지 목록
- **Module 구조**: Memory, Reflection, Plan, Action 모듈별 내용
- **통계**: 메시지 수, Agent 스텝 수, 모듈 출현 빈도

## Langfuse Trace 형식

Langfuse trace JSON 파일은 다음 구조를 가져야 합니다:

```json
{
  "id": "trace-id",
  "name": "trace-name",
  "metadata": {
    "task": "Task description",
    "success": true,
    "environment": "webshop"
  },
  "input": "Initial user input",
  "output": "Final output",
  "observations": [
    {
      "id": "obs-1",
      "type": "GENERATION",
      "name": "agent-step-1",
      "input": "User input or environment feedback",
      "output": "Agent response",
      "metadata": {},
      "start_time": "2025-01-01T00:00:00Z",
      "end_time": "2025-01-01T00:00:01Z"
    }
  ]
}
```

### Observations 타입

- **GENERATION**: LLM이 생성한 응답 (Agent의 단계)
- **SPAN**: 작업 단위 (여러 generation을 포함할 수 있음)
- **EVENT**: 이벤트 (도구 실행, 환경 응답 등)

## AgentDebug 형식

변환 후 다음 형식으로 출력됩니다:

```json
{
  "metadata": {
    "task_id": "trace-id",
    "environment": "webshop",
    "success": true,
    "task": "Task description"
  },
  "messages": [
    {
      "role": "user",
      "content": "Initial task or environment feedback"
    },
    {
      "role": "assistant",
      "content": "<memory>...</memory><reflection>...</reflection><plan>...</plan><action>...</action>"
    }
  ]
}
```

### Agent 메시지 구조 (4-module)

각 Assistant 메시지는 4개 모듈로 구성됩니다:

1. **Memory**: 이전 단계 요약 및 중요 정보 기억
2. **Reflection**: 현재 상황 평가 및 진행 상태 판단
3. **Plan**: 다음에 할 행동 계획
4. **Action**: 실제 수행할 행동

## 예시

### 예시 trace 테스트

이 디렉토리에는 `example_trace.json` 샘플 파일이 포함되어 있습니다:

```bash
uv run python run_step1.py traces/example_trace.json
```

이 예시는 다음을 보여줍니다:
- ✅ 성공한 agent 실행
- 3개의 agent 스텝
- 모든 모듈 (memory, reflection, plan, action) 포함

### 직접 trace 추가하기

1. Langfuse에서 trace를 JSON으로 export
2. `traces/` 디렉토리에 저장
3. `run_step1.py`로 변환 테스트

```bash
# Langfuse API로 trace 다운로드 (선택)
uv run debug_trace.py <trace-id>
# → results/debug_trace_<id>.json 생성

# traces/로 복사
cp results/debug_trace_<id>.json traces/my_trace.json

# 변환 테스트
uv run python run_step1.py traces/my_trace.json
```

## 문제 해결

### 변환이 제대로 안될 때

1. **Trace 구조 확인**:
   ```bash
   cat traces/my_trace.json | jq '.'
   ```

2. **Observations 확인**:
   ```bash
   cat traces/my_trace.json | jq '.observations'
   ```

3. **Debug 도구 사용**:
   ```bash
   # Langfuse API에서 직접 로드하여 구조 분석
   uv run debug_trace.py <trace-id>
   ```

### 일반적인 문제

**문제**: "No messages extracted"
- **원인**: observations가 비어있거나 GENERATION 타입이 없음
- **해결**: observations 배열에 GENERATION 타입 항목이 있는지 확인

**문제**: 모듈이 `<action>...</action>`만 있음
- **원인**: Agent 출력이 plain text 형식
- **해결**: Module decomposition 사용 (`convert_with_decomposition`)

**문제**: JSON 파싱 에러
- **원인**: 잘못된 JSON 형식
- **해결**: `jq` 또는 JSON validator로 형식 확인

## 다음 단계

Step 1 변환이 완료되면:

- **Step 2**: Phase 1 분석 (Fine-grained error detection)
  ```bash
  uv run run_phase1.py <trace-id>
  ```

- **Step 3**: Phase 2 분석 (Critical error identification)
  ```bash
  uv run run_phase2.py <trace-id>
  ```

- **전체 파이프라인**:
  ```bash
  uv run main.py <trace-id>
  ```
