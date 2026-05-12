"""Cursor Cloud Agents API v1 (HTTPS + SSE)."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from typing import Any

import httpx

API_BASE = "https://api.cursor.com"


def _basic_auth(api_key: str) -> tuple[str, str]:
    return (api_key, "")


def create_cloud_agent(
    client: httpx.Client,
    *,
    api_key: str,
    prompt_text: str,
    repo_url: str,
    starting_ref: str,
    model_id: str | None,
    auto_create_pr: bool,
) -> tuple[str, str]:
    body: dict[str, Any] = {
        "prompt": {"text": prompt_text},
        "repos": [{"url": repo_url, "startingRef": starting_ref}],
        "autoCreatePR": auto_create_pr,
    }
    if auto_create_pr:
        body["skipReviewerRequest"] = True
    if model_id:
        body["model"] = {"id": model_id}

    r = client.post(
        f"{API_BASE}/v1/agents",
        auth=_basic_auth(api_key),
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=httpx.Timeout(120.0, connect=30.0),
    )
    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = r.json()
        except json.JSONDecodeError:
            detail = r.text[:500]
        raise RuntimeError(f"Create agent failed ({r.status_code}): {detail}") from e

    data = r.json()
    agent_id = data["agent"]["id"]
    run_id = data["run"]["id"]
    return agent_id, run_id


def _parse_sse_stream(resp: httpx.Response) -> Iterator[tuple[str, dict[str, Any] | None]]:
    event_type = "message"
    data_lines: list[str] = []
    for raw in resp.iter_lines():
        if raw is None:
            continue
        line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        line = line.rstrip("\r")
        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event_type = line[len("event:") :].strip()
            continue
        if line.startswith("data:"):
            data_lines.append(line[len("data:") :].lstrip())
            continue
        if line.startswith("id:"):
            continue
        if line == "":
            if data_lines:
                raw_json = "\n".join(data_lines)
                try:
                    payload: dict[str, Any] | None = json.loads(raw_json) if raw_json else None
                except json.JSONDecodeError:
                    payload = {"raw": raw_json}
                yield event_type, payload
            event_type = "message"
            data_lines = []
            continue


def stream_run_to_stdout(
    client: httpx.Client,
    *,
    api_key: str,
    agent_id: str,
    run_id: str,
) -> str | None:
    """Stream SSE events; print assistant deltas to stdout. Returns terminal status if seen."""
    url = f"{API_BASE}/v1/agents/{agent_id}/runs/{run_id}/stream"
    terminal_status: str | None = None
    with client.stream(
        "GET",
        url,
        auth=_basic_auth(api_key),
        headers={"Accept": "text/event-stream"},
        timeout=httpx.Timeout(600.0, connect=60.0),
    ) as resp:
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = ""
            try:
                detail = resp.json()
            except json.JSONDecodeError:
                detail = resp.text[:500]
            raise RuntimeError(f"Stream failed ({resp.status_code}): {detail}") from e

        for event_type, payload in _parse_sse_stream(resp):
            if event_type == "assistant" and payload:
                chunk = payload.get("text", "")
                if chunk:
                    sys.stdout.write(chunk)
                    sys.stdout.flush()
            elif event_type == "thinking" and payload:
                chunk = payload.get("text", "")
                if chunk:
                    sys.stderr.write(chunk)
                    sys.stderr.flush()
            elif event_type == "error" and payload:
                msg = payload.get("message", payload)
                sys.stderr.write(f"\n[stream error] {msg}\n")
            elif event_type == "result" and payload:
                st = payload.get("status")
                if isinstance(st, str):
                    terminal_status = st
            elif event_type == "status" and payload:
                st = payload.get("status")
                if isinstance(st, str):
                    terminal_status = st

    sys.stdout.write("\n")
    sys.stdout.flush()
    return terminal_status


def get_run(client: httpx.Client, *, api_key: str, agent_id: str, run_id: str) -> dict[str, Any]:
    r = client.get(
        f"{API_BASE}/v1/agents/{agent_id}/runs/{run_id}",
        auth=_basic_auth(api_key),
        timeout=httpx.Timeout(60.0, connect=30.0),
    )
    r.raise_for_status()
    return r.json()
