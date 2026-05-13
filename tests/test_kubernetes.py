from __future__ import annotations

import subprocess

import devops_sre_agent.kubernetes as kubernetes
from devops_sre_agent.context import ReviewContextOptions
from devops_sre_agent.context_types import ContextCommandResult


def test_collect_kubernetes_context_runs_read_only_workload_commands(monkeypatch) -> None:
    commands: list[list[str]] = []

    def fake_run(args: list[str]) -> ContextCommandResult:
        commands.append(args)
        return ContextCommandResult(args, True, "ok")

    monkeypatch.setattr(kubernetes, "_run_kubectl", fake_run)

    section = kubernetes.collect_kubernetes_context(
        ReviewContextOptions(
            kube_context="prod-cluster",
            namespace="prod",
            workload="deployment/api",
        )
    )

    assert section.title == "Kubernetes read-only context"
    assert [
        "kubectl",
        "--context",
        "prod-cluster",
        "--namespace",
        "prod",
        "get",
        "pods",
        "-o",
        "wide",
    ] in commands
    assert [
        "kubectl",
        "--context",
        "prod-cluster",
        "--namespace",
        "prod",
        "get",
        "deployment/api",
        "-o",
        "yaml",
    ] in commands
    assert "ok" in section.body


def test_run_kubectl_reports_missing_binary(monkeypatch) -> None:
    def missing(*args, **kwargs):  # noqa: ANN002, ANN003
        raise FileNotFoundError

    monkeypatch.setattr(subprocess, "run", missing)

    result = kubernetes._run_kubectl(["kubectl", "get", "pods"])

    assert result.ok is False
    assert result.output == "kubectl not found"
