from __future__ import annotations

import re
import subprocess


def get_origin_url() -> str | None:
    try:
        r = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
            timeout=8,
        )
        out = r.stdout.strip()
        return out if out else None
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None


def to_github_https(remote: str) -> str | None:
    """Normalize git remote URLs to https://github.com/org/repo for the Cloud Agents API."""
    remote = remote.strip()
    if remote.startswith("git@github.com:"):
        rest = remote.split(":", maxsplit=1)[1].removesuffix(".git")
        return f"https://github.com/{rest}"
    m = re.match(r"ssh://git@github\.com/(.+?)(?:\.git)?/?$", remote)
    if m:
        return f"https://github.com/{m.group(1)}"
    if remote.startswith("https://github.com/"):
        return remote.removesuffix(".git").rstrip("/")
    return None


def resolve_github_repo_url(explicit: str | None) -> str | None:
    if explicit:
        url = explicit.strip()
        if url.startswith("git@"):
            return to_github_https(url)
        if url.startswith("https://github.com/"):
            return url.removesuffix(".git").rstrip("/")
        return url if "github.com" in url else None
    origin = get_origin_url()
    if not origin:
        return None
    return to_github_https(origin)
