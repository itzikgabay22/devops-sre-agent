SCENARIOS: dict[str, str] = {
    "rollout-risk": (
        "Review deployment safety: rollout strategy, canary/rollback plan, "
        "health checks, error budget impact, and post-deploy verification."
    ),
    "missing-probes": (
        "Find Kubernetes workloads missing readiness/liveness/startup probes "
        "and propose minimal safe probes with clear defaults."
    ),
    "resource-safety": (
        "Review CPU/memory requests, limits, throttling, OOM risk, HPA settings, "
        "and safe resource recommendations."
    ),
    "latency": (
        "Investigate latency regression using p95/p99, slow traces, dependency spans, "
        "saturation, and recent rollout signals."
    ),
    "errors": (
        "Investigate elevated errors using 5xx metrics, recent logs, pod health, "
        "and recent deployment changes."
    ),
    "restarts": (
        "Investigate CrashLoopBackOff, restart spikes, probe failures, OOMKilled events, "
        "and remediation steps."
    ),
    "observability-review": (
        "Review whether the workload has usable metrics, logs, traces, dashboards, "
        "alerts, and runbook signals."
    ),
}


def scenario_guidance(name: str) -> str:
    return SCENARIOS[name]
