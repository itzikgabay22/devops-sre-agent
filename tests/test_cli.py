from __future__ import annotations

from devops_sre_agent.cli import _build_parser


def test_run_parser_accepts_kubernetes_and_observability_flags() -> None:
    parser = _build_parser()

    args = parser.parse_args(
        [
            "run",
            "review rollout",
            "--namespace",
            "prod",
            "--workload",
            "deployment/api",
            "--since",
            "15m",
            "--prometheus-url",
            "http://prometheus:9090",
            "--loki-url",
            "http://loki:3100",
            "--tempo-url",
            "http://tempo:3200",
            "--trace-id",
            "abc123",
            "--scenario",
            "rollout-risk",
        ]
    )

    assert args.namespace == "prod"
    assert args.workload == "deployment/api"
    assert args.since == "15m"
    assert args.prometheus_url == "http://prometheus:9090"
    assert args.loki_url == "http://loki:3100"
    assert args.tempo_url == "http://tempo:3200"
    assert args.trace_id == "abc123"
    assert args.scenario == "rollout-risk"


def test_run_parser_rejects_unknown_scenario() -> None:
    parser = _build_parser()

    try:
        parser.parse_args(["run", "review", "--scenario", "nope"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser to reject invalid scenario")
