from __future__ import annotations

from urllib.parse import quote

import httpx


def _request_json(client: httpx.Client, url: str, params: dict[str, str]) -> str:
    try:
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return f"query failed: {exc}"
    return _compact_json(data)


def _compact_json(data: object) -> str:
    text = str(data)
    if len(text) > 2000:
        return text[:2000] + "\n... truncated ..."
    return text


def _workload_labels(namespace: str | None, workload: str | None) -> tuple[str, str]:
    namespace_matcher = f'namespace="{namespace}"' if namespace else 'namespace!=""'
    workload_name = ""
    if workload and "/" in workload:
        _, workload_name = workload.split("/", maxsplit=1)
    elif workload:
        workload_name = workload
    workload_matcher = f'pod=~"{workload_name}-.+"' if workload_name else 'pod!=""'
    return namespace_matcher, workload_matcher


def collect_prometheus_context(client: httpx.Client, options: object) -> object:
    from devops_sre_agent.context import ContextSection, ReviewContextOptions

    if not isinstance(options, ReviewContextOptions):
        raise TypeError("options must be ReviewContextOptions")

    base = options.prometheus_url.rstrip("/")
    namespace_matcher, workload_matcher = _workload_labels(options.namespace, options.workload)
    pod_matchers = f"{namespace_matcher},{workload_matcher}"
    queries = {
        "pod restarts": (
            "sum by (pod) (increase("
            f"kube_pod_container_status_restarts_total{{{pod_matchers}}}[{options.since}]))"
        ),
        "not ready pods": (
            "sum by (pod) ("
            f'kube_pod_status_ready{{{namespace_matcher},condition="false"}})'
        ),
        "cpu throttling": (
            "sum by (pod) (rate("
            f"container_cpu_cfs_throttled_seconds_total{{{pod_matchers}}}[5m]))"
        ),
        "memory working set": (
            "sum by (pod) ("
            f"container_memory_working_set_bytes{{{pod_matchers}}})"
        ),
        "http 5xx rate": (
            "sum(rate("
            f'http_requests_total{{{namespace_matcher},status=~"5.."}}[5m]))'
        ),
        "p95 latency": (
            "histogram_quantile(0.95, sum by (le) (rate("
            f"http_request_duration_seconds_bucket{{{namespace_matcher}}}[5m])))"
        ),
    }
    lines = []
    for label, query in queries.items():
        result = _request_json(client, f"{base}/api/v1/query", {"query": query})
        lines.append(f"#### {label}\nPromQL: `{query}`\n{result}")
    return ContextSection("Prometheus kube-prometheus context", "\n\n".join(lines))


def collect_loki_context(client: httpx.Client, options: object) -> object:
    from devops_sre_agent.context import ContextSection, ReviewContextOptions

    if not isinstance(options, ReviewContextOptions):
        raise TypeError("options must be ReviewContextOptions")

    base = options.loki_url.rstrip("/")
    namespace = options.namespace or ".+"
    selector = f'{{namespace=~"{namespace}"}} |~ "(?i)error|exception|panic|fail|timeout"'
    result = _request_json(
        client,
        f"{base}/loki/api/v1/query_range",
        {"query": selector, "limit": "20"},
    )
    return ContextSection("Loki recent error logs", f"LogQL: `{selector}`\n{result}")


def collect_tempo_context(client: httpx.Client, options: object) -> object:
    from devops_sre_agent.context import ContextSection, ReviewContextOptions

    if not isinstance(options, ReviewContextOptions):
        raise TypeError("options must be ReviewContextOptions")

    if not options.trace_id:
        return ContextSection(
            "Tempo trace context",
            "No trace ID supplied; skip live trace lookup.",
        )

    if not options.tempo_url:
        return ContextSection(
            "Tempo trace context",
            "Trace ID supplied but --tempo-url is missing.",
        )

    base = options.tempo_url.rstrip("/")
    trace_id = quote(options.trace_id, safe="")
    result = _request_json(client, f"{base}/api/traces/{trace_id}", {})
    return ContextSection("Tempo trace context", result)
