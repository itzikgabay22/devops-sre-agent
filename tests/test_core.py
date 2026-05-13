from __future__ import annotations

import httpx

from devops_sre_agent.cloud_client import create_cloud_agent
from devops_sre_agent.git_remote import to_github_https
from devops_sre_agent.prompt import compose_prompt


def test_to_github_https_normalizes_common_remote_forms() -> None:
    assert to_github_https("git@github.com:org/repo.git") == "https://github.com/org/repo"
    assert to_github_https("ssh://git@github.com/org/repo.git") == "https://github.com/org/repo"
    assert to_github_https("https://github.com/org/repo.git") == "https://github.com/org/repo"


def test_compose_prompt_appends_extra_context() -> None:
    prompt = compose_prompt("review", "cluster evidence")

    assert "## Task\nreview" in prompt
    assert "## Additional context\ncluster evidence" in prompt


def test_create_cloud_agent_raises_runtime_error_on_api_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "bad key"})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    try:
        create_cloud_agent(
            client,
            api_key="bad",
            prompt_text="hello",
            repo_url="https://github.com/org/repo",
            starting_ref="main",
            model_id=None,
            auto_create_pr=False,
        )
    except RuntimeError as exc:
        assert "Create agent failed (401)" in str(exc)
        assert "bad key" in str(exc)
    else:
        raise AssertionError("expected create_cloud_agent to raise")
