# devops-sre-agent

**Repository:** [github.com/itzikgabay22/devops-sre-agent](https://github.com/itzikgabay22/devops-sre-agent)

Python CLI that sends a **DevOps / SRE** prompt charter plus your task to the [Cursor Cloud Agents API](https://cursor.com/docs/cloud-agent/api/endpoints). The agent runs in Cursor’s cloud workspace against a **GitHub repository** you specify (or inferred from `git remote origin`).

## Prerequisites

- Python 3.11+
- `CURSOR_API_KEY` from [Cursor Dashboard → Integrations](https://cursor.com/dashboard/integrations)
- A GitHub repo wired for Cursor Cloud Agents (HTTPS URL, default branch/ref you pass)

## Install

```bash
pip install .
# or: pip install -e ".[dev]"
```

Requires **Python 3.11+**. Development checks (same as CI):

```bash
python3.12 -m venv .venv && source .venv/bin/activate   # or any 3.11+
pip install ".[dev]"
ruff check src && python -m compileall -q src
devops-sre-agent run --help
```

## Usage

```bash
export CURSOR_API_KEY="cursor_..."
cd /path/to/git/checkout   # optional; used to guess origin URL

devops-sre-agent run \
  "Review our Kubernetes rollout for production: risks, canary, rollback plan" \
  --ref main
```

Explicit repo and extra context:

```bash
devops-sre-agent run \
  "Why might latency have doubled?" \
  --repo-url https://github.com/org/service \
  --ref main \
  --context "Region eu-west-1, deploy ~2h ago"
```

Optional flags:

- `--model` — e.g. `composer-2`; omit to use your Cursor default model.
- `--auto-pr` — allow Cursor to open a PR when the run completes (default off).
- `--system-prompt PATH` — markdown file that replaces the packaged SRE charter (see below).
- `--kube-context`, `--namespace`, `--workload` — collect read-only Kubernetes context.
- `--prometheus-url`, `--loki-url`, `--tempo-url`, `--trace-id` — collect live observability context.
- `--scenario` — focus the review on a common SRE scenario.

### Custom SRE charter ([KAN-4](https://gabay.atlassian.net/browse/KAN-4))

You can tune the system instructions **without editing the installed package**:

1. **`--system-prompt /path/to/charter.md`** — highest priority when set.
2. **`DEVOPS_SRE_AGENT_SYSTEM_PROMPT_FILE`** — path to a charter file if `--system-prompt` is omitted.
3. Otherwise the built-in `sre-system.md` from the package is used.

If `CURSOR_API_KEY` is missing, the CLI exits with a clear error before calling the API.

### Kubernetes and observability review

The CLI can enrich the Cursor prompt with read-only Kubernetes, Prometheus, Loki, and Tempo
context. Kubernetes reads use `kubectl`; observability reads use HTTP APIs. Missing tools,
empty responses, or failed read-only calls are included in the prompt as evidence for the
agent instead of mutating the cluster.

```bash
devops-sre-agent run \
  "Review rollout safety and suggest fixes" \
  --repo-url https://github.com/org/service \
  --ref main \
  --namespace prod \
  --workload deployment/api \
  --scenario rollout-risk \
  --prometheus-url http://prometheus.monitoring:9090 \
  --loki-url http://loki.monitoring:3100 \
  --tempo-url http://tempo.monitoring:3200
```

Ask Cursor to create a PR with safe Kubernetes manifest fixes:

```bash
devops-sre-agent run \
  "Add missing readiness/liveness probes and safe resources if needed" \
  --repo-url https://github.com/org/service \
  --ref main \
  --namespace prod \
  --workload deployment/api \
  --scenario missing-probes \
  --auto-pr
```

Supported scenarios:

- `rollout-risk` — rollout strategy, rollback, health checks, and verification.
- `missing-probes` — readiness/liveness/startup probe gaps.
- `resource-safety` — requests, limits, throttling, OOM risk, and HPA posture.
- `latency` — p95/p99 latency, traces, saturation, and dependency signals.
- `errors` — 5xx, recent logs, pod health, and recent deployment changes.
- `restarts` — CrashLoopBackOff, restart spikes, probes, and OOMKilled events.
- `observability-review` — metrics, logs, traces, dashboards, alerts, and runbooks.

### Docker

Build and run the containerized CLI:

```bash
docker build -t devops-sre-agent .
docker run --rm \
  -e CURSOR_API_KEY \
  -v "$HOME/.kube:/home/sreagent/.kube:ro" \
  devops-sre-agent run \
  "Review production API reliability" \
  --repo-url https://github.com/org/service \
  --namespace prod \
  --workload deployment/api \
  --scenario observability-review
```

For in-cluster execution, see [`examples/kubernetes-job.yaml`](examples/kubernetes-job.yaml).

## How it works

1. Loads the system charter (packaged default, or file from `--system-prompt` / env).
2. Optionally collects read-only Kubernetes and observability context.
3. Appends your task, optional `--context`, scenario guidance, and collected evidence.
4. `POST /v1/agents` with `repos[0].url` pointing at GitHub.
5. Streams `GET /v1/agents/{id}/runs/{runId}/stream` (SSE) and prints assistant output to stdout.

This uses the **cloud** agent runtime (not the TypeScript SDK’s local `cwd` mode). Your repo must exist on GitHub and be accessible to Cursor.

## Publish to GitHub

The canonical remote is **public** and uses **`main`** as the default branch:

```bash
git clone https://github.com/itzikgabay22/devops-sre-agent.git
```

Initial setup for maintainers (one-time) used [KAN-2](https://gabay.atlassian.net/browse/KAN-2): `gh auth login`, then `gh repo create … --push` from the project root.

## Releases

Versioning follows **SemVer** (`MAJOR.MINOR.PATCH`). Git tags use a `v` prefix (e.g. `v0.1.0`).

After CI is green on `main` ([KAN-5](https://gabay.atlassian.net/browse/KAN-5)):

```bash
git checkout main && git pull
git tag -a v0.1.0 -m "devops-sre-agent 0.1.0"
git push origin v0.1.0
```

Optional: on GitHub, **Releases → Draft a new release** and attach the tag.

## License

MIT
