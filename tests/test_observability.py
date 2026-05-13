from __future__ import annotations

import httpx

from devops_sre_agent.context import ReviewContextOptions
from devops_sre_agent.observability import (
    collect_loki_context,
    collect_prometheus_context,
    collect_tempo_context,
)


def _client_with_json(payload: object) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_collect_prometheus_context_queries_expected_endpoint() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        assert "query=" in str(request.url)
        return httpx.Response(200, json={"status": "success", "data": {"result": []}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    section = collect_prometheus_context(
        client,
        ReviewContextOptions(
            namespace="prod",
            workload="deployment/api",
            prometheus_url="http://prometheus:9090",
        ),
    )

    assert section.title == "Prometheus kube-prometheus context"
    assert all(path == "/api/v1/query" for path in seen_paths)
    assert "http 5xx rate" in section.body


def test_collect_loki_context_handles_http_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="nope")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    section = collect_loki_context(
        client,
        ReviewContextOptions(namespace="prod", loki_url="http://loki:3100"),
    )

    assert section.title == "Loki recent error logs"
    assert "query failed" in section.body


def test_collect_tempo_context_requires_trace_id_and_url() -> None:
    client = _client_with_json({"trace": "ok"})

    no_trace = collect_tempo_context(client, ReviewContextOptions(tempo_url="http://tempo:3200"))
    no_url = collect_tempo_context(client, ReviewContextOptions(trace_id="abc"))
    with_trace = collect_tempo_context(
        client,
        ReviewContextOptions(tempo_url="http://tempo:3200", trace_id="abc"),
    )

    assert "No trace ID supplied" in no_trace.body
    assert "tempo-url is missing" in no_url.body
    assert "{'trace': 'ok'}" in with_trace.body
