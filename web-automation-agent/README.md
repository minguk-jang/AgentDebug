# Web Automation Agent

LangGraph 기반 웹 자동화 및 가이드 생성 Agent

## Features

- **자연어 쿼리로 웹 액션 자동화**: 사용자가 자연어로 요청한 작업을 자동으로 수행
- **Multi-step plan 생성 및 구체화**: 추상적인 계획을 실행 가능한 구체적 액션으로 변환
- **실시간 가이드 생성**: Workarounds, parameter constraints, selector fallbacks 자동 문서화
- **Markdown 문서 자동 생성**: 전체 실행 과정과 가이드를 Markdown 파일로 저장

## Architecture

이 프로젝트는 LangGraph를 사용하여 7개의 노드로 구성된 워크플로우를 구현합니다:

```
init → planning → exploration → validation → execution → documentation → finalize
```

### Workflow Nodes

1. **init**: 상태 초기화 및 Markdown 문서 템플릿 생성
2. **planning**: LLM을 사용하여 high-level 계획 수립
3. **exploration**: 웹 페이지 탐색 및 계획 구체화
4. **validation**: 각 단계의 실행 가능성 검증 및 fallback 생성
5. **execution**: 계획된 액션 실행 및 결과 캡처
6. **documentation**: 모든 가이드 아이템 문서화
7. **finalize**: 최종 Markdown 파일 저장

## Installation

```bash
pip install -r requirements.txt
```

### Requirements

- Python 3.11+
- Chrome browser (for Selenium)
- Anthropic API Key

## Environment Setup

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Usage

```bash
python main.py
```

### Interactive Mode

실행 후 다음 정보를 입력:

```
Enter target URL: https://example.com
Enter query: 검색창에 'Python'을 입력하고 검색 버튼 클릭
```

### Programmatic Usage

```python
from src.agent.graph import run_agent

result = run_agent(
    url="https://example.com",
    query="검색창에 'Python'을 입력하고 검색 버튼 클릭"
)

print(f"Steps executed: {len(result['plan_steps'])}")
print(f"Guide items: {len(result['guide_items'])}")
```

## Project Structure

```
web-automation-agent/
├── src/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── state.py          # AgentState 및 데이터 모델 정의
│   │   ├── nodes.py          # LangGraph 노드 함수들
│   │   └── graph.py          # LangGraph 워크플로우 정의
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── planning.py       # 계획 수립 도구
│   │   ├── guide.py          # 가이드 생성 도구
│   │   ├── exploration.py    # 웹 페이지 탐색 도구
│   │   └── documentation.py  # 문서화 도구
│   └── utils/
│       ├── __init__.py
│       └── web_driver.py     # Selenium WebDriver 래퍼
├── tests/
│   └── __init__.py
├── outputs/                  # 생성된 가이드 문서 저장
│   └── .gitkeep
├── requirements.txt
├── README.md
└── main.py                   # 메인 실행 파일
```

## Example

### Input

```
URL: https://www.google.com
Query: 검색창에 'LangGraph'를 입력하고 검색
```

### Output

실행 결과는 `outputs/검색창에_LangGraph를_입력하고_검색.md` 파일로 저장됩니다:

```markdown
# Web Automation Guide

**Target URL**: https://www.google.com
**Query**: 검색창에 'LangGraph'를 입력하고 검색
**Generated**: 2025-01-15 10:30:45

---

## Plan

### Step 1: Navigate to Google
- **Action**: navigate
- **Selector**: N/A
- **Value**: https://www.google.com
- **Status**: success

### Step 2: Input search query
- **Action**: input
- **Selector**: [name='q']
- **Value**: LangGraph
- **Status**: success

### Step 3: Click search button
- **Action**: click
- **Selector**: [name='btnK']
- **Value**: N/A
- **Status**: success

## Guide

### Selector Fallback (Step 2)
**Primary**: `[name='q']`
**Fallbacks**: `#search`, `input[type='text']`, `.search-input`

### Parameter Constraint (Step 2)
**Parameter**: `value`
**Constraint**: Must provide a search term
**Example**: `LangGraph tutorial`
```

## Components

### State Management

`src/agent/state.py`에 정의된 3가지 주요 데이터 모델:

- **PlanStep**: 자동화 단계를 나타내는 모델
- **GuideItem**: 가이드 아이템 (workaround, constraint, fallback)
- **AgentState**: 전체 워크플로우 상태

### Tools

#### Planning Tools (`src/tools/planning.py`)

- `create_initial_plan()`: LLM을 사용하여 high-level 계획 생성
- `explore_and_refine_plan()`: 웹 페이지 분석 후 구체적 액션으로 변환
- `validate_step_feasibility()`: 단계 실행 가능성 검증

#### Guide Tools (`src/tools/guide.py`)

- `add_workaround()`: 문제 해결 방법 문서화
- `add_parameter_constraint()`: 파라미터 제약사항 문서화
- `add_selector_fallback()`: 대체 셀렉터 문서화

#### Exploration Tools (`src/tools/exploration.py`)

- `analyze_page_structure()`: 페이지 구조 분석 (버튼, 입력 필드 등)
- `test_action_dry_run()`: 액션 실행 전 가능성 테스트
- `capture_interaction_result()`: 인터랙션 결과 캡처

#### Documentation Tools (`src/tools/documentation.py`)

- `init_md_document()`: Markdown 템플릿 초기화
- `append_plan_step()`: 계획 단계 추가
- `append_guide_section()`: 가이드 섹션 추가
- `finalize_md()`: 최종 문서 저장

### Utilities

#### Web Driver (`src/utils/web_driver.py`)

- `get_driver()`: Chrome WebDriver 초기화 (headless 모드)
- `safe_find_element()`: 다중 전략으로 요소 찾기
- `safe_click()`: 안전한 클릭 (JavaScript fallback 포함)
- `safe_input()`: 안전한 입력 (JavaScript fallback 포함)
- `sanitize_filename()`: 파일명 정리

## Error Handling

- 모든 노드에서 예외 처리 구현
- 실패한 액션에 대해 자동으로 workaround 생성
- Error log를 state에 기록하고 최종 문서에 포함

## Limitations

- 현재 Chrome 브라우저만 지원
- JavaScript가 많이 사용된 복잡한 SPA는 추가 대기 시간 필요
- CAPTCHA나 로그인이 필요한 페이지는 수동 처리 필요

## Future Enhancements

- [ ] Firefox, Safari 등 다른 브라우저 지원
- [ ] 동적 대기 시간 자동 조정
- [ ] 스크린샷 자동 캡처
- [ ] 실행 결과 replay 기능
- [ ] Multi-page 자동화 지원
- [ ] 로그인 세션 관리

## License

MIT

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## Credits

- **LangGraph**: Workflow orchestration framework
- **LangChain**: LLM integration
- **Anthropic Claude**: Language model for planning and reasoning
- **Selenium**: Web automation framework

---

Built with ❤️ using LangGraph and Claude
