from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, Field


class ExecutionRequest(BaseModel):
    base_url: str
    allowed_hosts: list[str] = Field(min_length=1)
    approval: str
    generated_dir: Path


class PolicyViolation(ValueError):
    pass


def validate_execution(request: ExecutionRequest, workspace_root: Path) -> Path:
    if request.approval != "APPROVED":
        raise PolicyViolation("Explicit human approval is required")
    parsed = urlparse(request.base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise PolicyViolation("Base URL must use HTTP or HTTPS and include a host")
    normalized_hosts = {host.strip().lower() for host in request.allowed_hosts}
    if parsed.hostname.lower() not in normalized_hosts:
        raise PolicyViolation(f"Host is not allowed: {parsed.hostname}")
    root = workspace_root.resolve()
    generated_dir = request.generated_dir.resolve()
    if not generated_dir.is_relative_to(root):
        raise PolicyViolation("Execution directory escapes the workspace")
    test_file = generated_dir / "test_generated_api.py"
    if not test_file.is_file():
        raise PolicyViolation("Generated test file was not found")
    return test_file


def build_test_command(test_file: Path) -> list[str]:
    return ["python", "-m", "pytest", str(test_file), "-q"]
