# Search-First-Agent

Search Everything in Internet First

-   src > simple_agent: 간단한 에이전트 (A2A wrapping 완료)
-   src > agent: 진짜 만들고자 하는 에이전트

### 환경 설정

0. 의존성 설치

```bash
    uv venv --python 3.13.0
    source .venv/bin/activate
    uv pip install -r requirements.txt
```

1. **Langgraph Platform**을 통한 실행

```bash
    uv run langgraph dev
```

2. **A2A** 서빙

```bash
    uv run run_search_agent.py
```
