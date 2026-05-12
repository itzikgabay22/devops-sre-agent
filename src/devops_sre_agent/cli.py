"""CLI entrypoint for devops-sre-agent."""

from __future__ import annotations

import argparse
import os
import sys

import httpx

from devops_sre_agent.cloud_client import create_cloud_agent, get_run, stream_run_to_stdout
from devops_sre_agent.git_remote import resolve_github_repo_url
from devops_sre_agent.prompt import SYSTEM_PROMPT_FILE_ENV, compose_prompt


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="devops-sre-agent",
        description=(
            "Run an SRE-focused prompt via the Cursor Cloud Agents API against a GitHub repo."
        ),
    )
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Create a cloud agent run with the SRE prompt pack")
    run.add_argument(
        "task",
        help='Instruction for the agent (quote multi-word tasks), e.g. "Review prod rollout risk"',
    )
    run.add_argument(
        "--context",
        "-c",
        default=None,
        help="Optional extra context (region, service name, incident window, etc.)",
    )
    run.add_argument(
        "--repo-url",
        "-r",
        default=None,
        help="GitHub repo HTTPS URL (default: git remote origin, normalized to HTTPS)",
    )
    run.add_argument(
        "--ref",
        default="main",
        help="Branch / tag / SHA for repos[].startingRef (default: main)",
    )
    run.add_argument(
        "--model",
        default=None,
        help='Optional model id (e.g. "composer-2"). Omit to use your Cursor default.',
    )
    run.add_argument(
        "--auto-pr",
        action="store_true",
        help="Ask Cursor to open a PR when the run finishes (default: off)",
    )
    run.add_argument(
        "--system-prompt",
        default=None,
        metavar="PATH",
        help=(
            "Markdown file that replaces the packaged SRE charter "
            f"(overrides {SYSTEM_PROMPT_FILE_ENV} when both are set)"
        ),
    )

    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command != "run":
        parser.print_help()
        sys.exit(1)

    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        sys.stderr.write("CURSOR_API_KEY is not set.\n")
        sys.stderr.write(
            "Create an API key under Cursor Dashboard → Integrations, then export it.\n"
        )
        sys.exit(1)

    repo_url = resolve_github_repo_url(args.repo_url)
    if not repo_url:
        sys.stderr.write(
            "Could not determine a GitHub repository URL.\n"
            "Pass --repo-url https://github.com/org/repo or run inside a git clone "
            "with an origin pointing at GitHub.\n"
        )
        sys.exit(1)

    prompt_text = compose_prompt(args.task, args.context, system_prompt_path=args.system_prompt)

    with httpx.Client() as client:
        try:
            agent_id, run_id = create_cloud_agent(
                client,
                api_key=api_key,
                prompt_text=prompt_text,
                repo_url=repo_url,
                starting_ref=args.ref,
                model_id=args.model,
                auto_create_pr=args.auto_pr,
            )
        except RuntimeError as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)

        sys.stderr.write(
            f"Started cloud agent {agent_id} run {run_id} on {repo_url} @ {args.ref}\n"
        )

        try:
            stream_run_to_stdout(client, api_key=api_key, agent_id=agent_id, run_id=run_id)
        except RuntimeError as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)

        final = get_run(client, api_key=api_key, agent_id=agent_id, run_id=run_id)
        status = final.get("status", "")
        if status == "ERROR":
            sys.exit(2)
        if status not in ("FINISHED", "CANCELLED"):
            sys.stderr.write(f"Warning: run ended with status {status!r}\n")


if __name__ == "__main__":
    main()
