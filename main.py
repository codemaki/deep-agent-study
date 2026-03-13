"""Deep Agent — streaming debug mode with Azure OpenAI."""
import os
import sys
import langchain
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

load_dotenv()

# langchain.debug = True 로 LLM 입출력 날것의 로그를 터미널에 출력
if os.getenv("DEBUG_MODE", "true").lower() == "true":
    langchain.debug = True

from langchain_openai import AzureChatOpenAI
from deepagents import create_deep_agent

console = Console()

STEP_COLORS = {"agent": "cyan", "tools": "yellow"}


def print_step(step: dict, n: int) -> None:
    for node, state in step.items():
        if not state:
            continue
        color = STEP_COLORS.get(node, "white")
        lines = []
        raw = state.get("messages", [])
        msgs_list = raw.value if hasattr(raw, "value") else raw
        for msg in msgs_list:
            role = getattr(msg, "type", type(msg).__name__)
            content = str(getattr(msg, "content", ""))
            icon = {"human": "👤", "ai": "🤖", "tool": "🛠️"}.get(role, "📋")

            for tc in getattr(msg, "tool_calls", []):
                lines.append(f"[bold magenta]🔧 tool_call:[/] [yellow]{tc['name']}[/] args={tc.get('args')}")

            if content:
                preview = content[:400] + ("…" if len(content) > 400 else "")
                lines.append(f"[bold]{icon} {role}:[/] {preview}")

        console.print(
            Panel(
                Text.from_markup("\n".join(lines) or "(empty)"),
                title=f"[bold {color}]Step {n} → {node}[/bold {color}]",
                border_style=color,
                expand=False,
            )
        )


def run(query: str) -> None:
    console.print(Rule("[bold blue]🚀 Deep Agent — Stream Debug[/bold blue]"))
    console.print(f"[bold]Query:[/bold] {query}\n")

    model = AzureChatOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        temperature=0,
        streaming=True,
    )

    agent = create_deep_agent(model=model)
    inputs = {"messages": [{"role": "user", "content": query}]}

    step_num = 0
    final_answer = ""

    for step in agent.stream(inputs):
        step_num += 1
        print_step(step, step_num)

        for node, state in step.items():
            if not state:
                continue
            raw = state.get("messages", [])
            msgs = raw.value if hasattr(raw, "value") else raw
            for msg in msgs:
                # AIMessage 타입만 캡처 (HumanMessage 제외)
                if getattr(msg, "type", "") == "ai":
                    c = getattr(msg, "content", "")
                    if c:
                        final_answer = c

    console.print(Rule("[bold green]✅ Final Answer[/bold green]"))
    console.print(final_answer)


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Research LangGraph and write a summary"
    run(query)
