from __future__ import annotations

import subprocess

from devops_sre_agent.context_types import ContextCommandResult


def _kubectl_base_args(kube_context: str | None, namespace: str | None) -> list[str]:
    args = ["kubectl"]
    if kube_context:
        args.extend(["--context", kube_context])
    if namespace:
        args.extend(["--namespace", namespace])
    return args


def _run_kubectl(args: list[str]) -> ContextCommandResult:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except FileNotFoundError:
        return ContextCommandResult(command=args, ok=False, output="kubectl not found")
    except subprocess.TimeoutExpired:
        return ContextCommandResult(command=args, ok=False, output="kubectl command timed out")

    output = (result.stdout or result.stderr).strip()
    return ContextCommandResult(command=args, ok=result.returncode == 0, output=output)


def _format_result(result: ContextCommandResult) -> str:
    status = "ok" if result.ok else "failed"
    command = " ".join(result.command)
    output = result.output or "(no output)"
    return f"$ {command}\n# {status}\n{output}"


def collect_kubernetes_context(options: object) -> object:
    from devops_sre_agent.context import ContextSection, ReviewContextOptions

    if not isinstance(options, ReviewContextOptions):
        raise TypeError("options must be ReviewContextOptions")

    base = _kubectl_base_args(options.kube_context, options.namespace)
    commands: list[list[str]] = []
    if options.namespace:
        commands.append([*base, "get", "events", "--sort-by=.lastTimestamp"])
        commands.append([*base, "get", "pods", "-o", "wide"])

    if options.workload:
        commands.extend(
            [
                [*base, "get", options.workload, "-o", "yaml"],
                [*base, "describe", options.workload],
            ]
        )

    if not commands:
        commands.append([*base, "version", "--client=true"])

    rendered = "\n\n".join(_format_result(_run_kubectl(command)) for command in commands)
    return ContextSection("Kubernetes read-only context", rendered)
