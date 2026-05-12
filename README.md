# devops-sre-agent

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

## How it works

1. Loads the system charter from packaged `prompts/sre-system.md`.
2. Appends your task (and optional `--context`).
3. `POST /v1/agents` with `repos[0].url` pointing at GitHub.
4. Streams `GET /v1/agents/{id}/runs/{runId}/stream` (SSE) and prints assistant output to stdout.

This uses the **cloud** agent runtime (not the TypeScript SDK’s local `cwd` mode). Your repo must exist on GitHub and be accessible to Cursor.

## Publish to GitHub

Tracked as [KAN-2](https://gabay.atlassian.net/browse/KAN-2). One-time setup:

1. Install the [GitHub CLI](https://cli.github.com/) (`brew install gh` on macOS).
2. Authenticate: `gh auth login` (choose HTTPS, authenticate in the browser or paste a PAT with `repo` scope).
3. From this repository root, create the public remote and push `main`:

```bash
cd /path/to/devops-sre-agent
gh repo create devops-sre-agent --public --source=. --remote=origin --push \
  --description "Python CLI: SRE-focused prompts via Cursor Cloud Agents API"
```

4. After the push, add the canonical URL under `[project.urls]` in `pyproject.toml` (optional but recommended).

Verify with `git clone https://github.com/<you>/devops-sre-agent.git` in a clean directory.

## License

MIT
