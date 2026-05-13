from __future__ import annotations

from dataclasses import dataclass

import httpx

from devops_sre_agent.kubernetes import collect_kubernetes_context
from devops_sre_agent.observability import (
    collect_loki_context,
    collect_prometheus_context,
    collect_tempo_context,
)
from devops_sre_agent.scenarios import SCENARIOS, scenario_guidance


@dataclass(frozen=True)
class ReviewContextOptions:
    kube_context: str | None = None
    namespace: str | None = None
    workload: str | None = None
    since: str = "30m"
    prometheus_url: str | None = None
    loki_url: str | None = None
    tempo_url: str | None = None
    trace_id: str | None = None
    scenario: str | None = None


@dataclass(frozen=True)
class ContextSection:
    title: str
    body: str


def has_live_context(options: ReviewContextOptions) -> bool:
    return any(
        (
            options.kube_context,
            options.namespace,
            options.workload,
            options.prometheus_url,
            options.loki_url,
            options.tempo_url,
            options.trace_id,
            options.scenario,
        )
    )


def render_context_sections(sections: list[ContextSection]) -> str:
    rendered: list[str] = []
    for section in sections:
        body = section.body.strip()
        if body:
            rendered.append(f"### {section.title}\n{body}")
    return "\n\n".join(rendered)


def collect_review_context(
    options: ReviewContextOptions,
    *,
    http_client: httpx.Client | None = None,
) -> str | None:
    sections: list[ContextSection] = []

    if options.scenario:
        sections.append(
            ContextSection("Requested SRE scenario", scenario_guidance(options.scenario))
        )

    if options.namespace or options.workload or options.kube_context:
        sections.append(collect_kubernetes_context(options))

    owns_client = http_client is None
    client = http_client or httpx.Client(timeout=httpx.Timeout(20.0, connect=5.0))
    try:
        if options.prometheus_url:
            sections.append(collect_prometheus_context(client, options))
        if options.loki_url:
            sections.append(collect_loki_context(client, options))
        if options.tempo_url or options.trace_id:
            sections.append(collect_tempo_context(client, options))
    finally:
        if owns_client:
            client.close()

    rendered = render_context_sections(sections)
    return rendered if rendered else None


def validate_scenario(value: str | None) -> str | None:
    if value is None:
        return None
    if value not in SCENARIOS:
        allowed = ", ".join(sorted(SCENARIOS))
        raise ValueError(f"Unknown scenario {value!r}. Choose one of: {allowed}")
    return value
