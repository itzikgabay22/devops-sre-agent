from __future__ import annotations

import httpx

from devops_sre_agent.context import (
    ContextSection,
    ReviewContextOptions,
    collect_review_context,
    render_context_sections,
    validate_scenario,
)


def test_render_context_sections_skips_empty_sections() -> None:
    rendered = render_context_sections(
        [
            ContextSection("One", "body"),
            ContextSection("Empty", " "),
            ContextSection("Two", "more"),
        ]
    )

    assert "### One\nbody" in rendered
    assert "### Empty" not in rendered
    assert "### Two\nmore" in rendered


def test_validate_scenario_error_lists_allowed_values() -> None:
    try:
        validate_scenario("bad")
    except ValueError as exc:
        assert "Unknown scenario" in str(exc)
        assert "rollout-risk" in str(exc)
    else:
        raise AssertionError("expected invalid scenario to raise")


def test_collect_review_context_includes_scenario_only() -> None:
    rendered = collect_review_context(ReviewContextOptions(scenario="missing-probes"))

    assert rendered is not None
    assert "Requested SRE scenario" in rendered
    assert "readiness/liveness/startup" in rendered


def test_collect_review_context_uses_supplied_http_client() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "success", "data": {"result": []}})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test")
    rendered = collect_review_context(
        ReviewContextOptions(prometheus_url="http://prometheus:9090"),
        http_client=client,
    )

    assert rendered is not None
    assert "Prometheus kube-prometheus context" in rendered
    assert "pod restarts" in rendered
