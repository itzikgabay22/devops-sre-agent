from __future__ import annotations

from pathlib import Path


def test_dockerfile_uses_target_platform_for_kubectl() -> None:
    dockerfile = Path("Dockerfile").read_text()

    assert "ARG TARGETOS=linux" in dockerfile
    assert "ARG TARGETARCH\n" in dockerfile
    assert "bin/${TARGETOS}/${TARGETARCH}/kubectl" in dockerfile
    assert "ARG TARGETARCH=amd64" not in dockerfile
