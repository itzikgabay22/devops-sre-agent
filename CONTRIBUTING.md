# Contributing

## One Jira task, one pull request

Deliver work from [Jira](https://gabay.atlassian.net/jira/software/projects/KAN) as **small, reviewable PRs**:

1. Create a branch from an up to date `main`:

   ```bash
   git checkout main && git pull origin main
   git checkout -b kan-<id>-short-description
   ```

   Example: `kan-4-custom-system-prompt`.

2. Commit with the Jira key in the subject when possible:

   ```text
   feat(KAN-4): allow custom SRE charter file
   ```

3. Open a PR into `main`. Put **KAN-&lt;id&gt;** in the title or body (the PR template reminds you).

4. Wait for CI (see `.github/workflows/ci.yml`) to pass before merge.

## Stacked PRs

If a change depends on another open PR, open the second PR **into the first branch** (GitHub base = feature branch). After the parent merges, rebase onto `main` or retarget the child PR as needed.

## Local checks (same as CI)

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install ".[dev]"
ruff check src tests
pytest
python -m compileall -q src
devops-sre-agent run --help
```

## Merge and Jira discipline

- Add or update unit tests for every behavior change.
- Open a PR for every implementation branch; do not push feature work directly to `main`.
- Merge only after local checks and GitHub Actions are green.
- Move Jira issues to **Done** only after the relevant PR is formally merged.
