from __future__ import annotations

from importlib import resources

from devops_sre_agent import prompts as prompts_pkg


def load_sre_system_prompt() -> str:
    return resources.files(prompts_pkg).joinpath("sre-system.md").read_text(encoding="utf8")


def build_user_prompt(task: str, extra_context: str | None = None) -> str:
    parts = [f"## Task\n{task.strip()}"]
    if extra_context and extra_context.strip():
        parts.append(f"## Additional context\n{extra_context.strip()}")
    return "\n\n".join(parts)


def compose_prompt(task: str, extra_context: str | None = None) -> str:
    system = load_sre_system_prompt()
    user = build_user_prompt(task, extra_context)
    return f"{system}\n\n---\n\n{user}"
