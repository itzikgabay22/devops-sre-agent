from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextCommandResult:
    command: list[str]
    ok: bool
    output: str
