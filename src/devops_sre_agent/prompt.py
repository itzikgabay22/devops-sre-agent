from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

from devops_sre_agent import prompts as prompts_pkg

SYSTEM_PROMPT_FILE_ENV = "DEVOPS_SRE_AGENT_SYSTEM_PROMPT_FILE"


def load_sre_system_prompt(*, override_path: str | None = None) -> str:
    """Load the SRE charter: CLI path, env file path, then packaged default."""
    if override_path:
        return Path(override_path).expanduser().read_text(encoding="utf8")
    env_path = os.environ.get(SYSTEM_PROMPT_FILE_ENV, "").strip()
    if env_path:
        return Path(env_path).expanduser().read_text(encoding="utf8")
    return resources.files(prompts_pkg).joinpath("sre-system.md").read_text(encoding="utf8")


def build_user_prompt(task: str, extra_context: str | None = None) -> str:
    parts = [f"## Task\n{task.strip()}"]
    if extra_context and extra_context.strip():
        parts.append(f"## Additional context\n{extra_context.strip()}")
    return "\n\n".join(parts)


def compose_prompt(
    task: str,
    extra_context: str | None = None,
    *,
    system_prompt_path: str | None = None,
) -> str:
    system = load_sre_system_prompt(override_path=system_prompt_path)
    user = build_user_prompt(task, extra_context)
    return f"{system}\n\n---\n\n{user}"
