# Deep Agent Study

`deepagents` 패키지 + Azure OpenAI 로 에이전트 내부 동작을 실시간으로 훔쳐보는 스트리밍 디버그 환경.

---

## 구조

```
deep-agent-study/
├── main.py           # 진입점 (langchain.debug + stream)
├── .env              # Azure OpenAI 키 (git 제외)
├── .env.example      # 키 템플릿
├── pyproject.toml    # uv 의존성 관리
├── uv.lock           # 의존성 잠금 파일
├── Dockerfile
└── docker-compose.yml
```

---

## 핵심 개념

### deepagents란?
`langchain-ai`에서 만든 공식 패키지. `create_deep_agent()`를 호출하면 LangGraph 기반의 ReAct 에이전트가 반환된다. 내부에 아래 미들웨어가 자동 포함된다.

| 미들웨어 | 제공 도구 |
|---|---|
| `TodoListMiddleware` | `write_todos` — 작업 계획 |
| `FilesystemMiddleware` | `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep` |
| `SubAgentMiddleware` | `task` — 하위 에이전트 생성 |

### 에이전트 내부를 보는 3가지 방법

#### 1. 디버그 모드 (가장 빠름)
LLM에 넘기는 프롬프트·파라미터, 도구 입출력 등 날것의 로그가 터미널에 출력된다.

```python
import langchain
langchain.debug = True  # 이 한 줄이 핵심

from deepagents import create_deep_agent

agent = create_deep_agent()
agent.invoke({"messages": [{"role": "user", "content": "Research LangGraph"}]})
```

#### 2. 스트림 모드 (중간 과정 실시간 확인)
`.invoke()`는 끝날 때까지 기다렸다가 결과만 반환하지만,
`.stream()`은 에이전트가 한 단계를 마칠 때마다 그 상태(State)를 즉시 뱉는다.

```python
from deepagents import create_deep_agent

agent = create_deep_agent()
inputs = {"messages": [{"role": "user", "content": "Research LangGraph"}]}

for step in agent.stream(inputs):
    print("🔄 [현재 작업 단계]")
    print(step)
    print("---")
```

#### 3. LangSmith (가장 추천 — UI 트리 구조로 시각화)
코드 수정 없이 환경변수만 세팅하면 웹 대시보드에서 에이전트 실행 흐름을 볼 수 있다.

```bash
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_API_KEY="랭스미스_API_키"
```

---

## 스트림 출력 구조

`deepagents`의 스트림은 노드 단위로 쪼개져 나온다.

| Step | 노드 | 의미 |
|---|---|---|
| 1 | `PatchToolCallsMiddleware.before_agent` | 입력 전처리 |
| 2 | `model` | LLM 응답 (tool_call 또는 최종 답변) |
| 3 | `tools` | 도구 실행 결과 |
| … | 반복 | 다단계 추론 |

스트림 state에서 `messages` 값은 `Overwrite(value=[...])` 래퍼로 감싸져 있으므로
꺼낼 때 `.value`를 써야 한다.

```python
raw = state.get("messages", [])
msgs = raw.value if hasattr(raw, "value") else raw
```

---

## 설치 및 실행

### 요구사항
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

### 로컬 실행

```bash
# 의존성 설치 (가상환경 자동 생성)
uv sync

# 기본 쿼리 실행
uv run python main.py

# 커스텀 쿼리
uv run python main.py "LangGraph란 무엇인지 조사하고 요약해줘."
```

### Docker 실행

```bash
# 빌드 후 기본 쿼리 실행
docker compose run deep-agent

# 커스텀 쿼리
docker compose run deep-agent "GPT-4와 GPT-4o의 차이를 설명해줘."
```

---

## 환경변수 설정

`.env.example`을 복사해서 `.env`를 만들고 값을 채운다.

```bash
cp .env.example .env
```

| 변수 | 설명 | 기본값 |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 엔드포인트 URL | 필수 |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API 키 | 필수 |
| `AZURE_OPENAI_DEPLOYMENT` | 배포 이름 | `gpt-4o` |
| `AZURE_OPENAI_API_VERSION` | API 버전 | `2024-12-01-preview` |
| `DEBUG_MODE` | `langchain.debug` 활성화 여부 | `true` |
| `TAVILY_API_KEY` | 웹 검색 도구용 (선택) | — |
| `LANGCHAIN_TRACING_V2` | LangSmith 트레이싱 (선택) | — |
| `LANGCHAIN_API_KEY` | LangSmith API 키 (선택) | — |

### Azure OpenAI 사용 가능한 배포 이름

```
gpt-4.1 / gpt-4.1-mini
gpt-4o  / gpt-4o-mini
gpt-5   / gpt-5-mini
text-embedding-3-large / text-embedding-3-small
```
