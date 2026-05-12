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

### Custom SRE charter ([KAN-4](https://gabay.atlassian.net/browse/KAN-4))

You can tune the system instructions **without editing the installed package**:

1. **`--system-prompt /path/to/charter.md`** — highest priority when set.
2. **`DEVOPS_SRE_AGENT_SYSTEM_PROMPT_FILE`** — path to a charter file if `--system-prompt` is omitted.
3. Otherwise the built-in `sre-system.md` from the package is used.

If `CURSOR_API_KEY` is missing, the CLI exits with a clear error before calling the API.

## How it works

1. Loads the system charter (packaged default, or file from `--system-prompt` / env).
2. Appends your task (and optional `--context`).
3. `POST /v1/agents` with `repos[0].url` pointing at GitHub.
4. Streams `GET /v1/agents/{id}/runs/{runId}/stream` (SSE) and prints assistant output to stdout.

This uses the **cloud** agent runtime (not the TypeScript SDK’s local `cwd` mode). Your repo must exist on GitHub and be accessible to Cursor.

## Publish to GitHub

The canonical remote is **public** and uses **`main`** as the default branch:

```bash
git clone https://github.com/itzikgabay22/devops-sre-agent.git
```

Initial setup for maintainers (one-time) used [KAN-2](https://gabay.atlassian.net/browse/KAN-2): `gh auth login`, then `gh repo create … --push` from the project root.

## License

MIT
