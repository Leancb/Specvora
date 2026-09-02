from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from pydantic import BaseModel, Field

from specvora.policy import ExecutionRequest, validate_execution

MAX_OUTPUT_CHARS = 20_000


class RunnerRequest(BaseModel):
    workspace_root: Path
    generated_dir: Path
    report_path: Path
    base_url: str
    allowed_hosts: list[str] = Field(min_length=1)
    approval: str
    timeout_seconds: int = Field(default=60, ge=1, le=300)


class RunnerOutcome(BaseModel):
    command: list[str]
    exit_code: int
    report_path: Path
    stdout: str
    stderr: str
    duration_seconds: float
    started_at: datetime
    timed_out: bool = False


class RunnerError(RuntimeError):
    pass


def run_generated_tests(request: RunnerRequest) -> RunnerOutcome:
    test_file = validate_execution(
        ExecutionRequest(
            base_url=request.base_url,
            allowed_hosts=request.allowed_hosts,
            approval=request.approval,
            generated_dir=request.generated_dir,
        ),
        request.workspace_root,
    )
    report_path = _confined_report_path(request.report_path, request.workspace_root)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        "-q",
        "--json-report",
        f"--json-report-file={report_path}",
    ]
    environment = _safe_environment(request.base_url)
    started_at = datetime.now(UTC)
    started = monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=request.generated_dir.resolve(),
            env=environment,
            capture_output=True,
            text=True,
            timeout=request.timeout_seconds,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RunnerError(
            f"Controlled test run timed out after {request.timeout_seconds} seconds"
        ) from exc
    duration = monotonic() - started
    if not report_path.is_file():
        details = _bounded(completed.stderr or completed.stdout).strip()
        suffix = f": {details}" if details else ""
        raise RunnerError(f"Pytest did not produce the required JSON report{suffix}")
    return RunnerOutcome(
        command=command,
        exit_code=completed.returncode,
        report_path=report_path,
        stdout=_bounded(completed.stdout),
        stderr=_bounded(completed.stderr),
        duration_seconds=duration,
        started_at=started_at,
    )


def _confined_report_path(report_path: Path, workspace_root: Path) -> Path:
    root = workspace_root.resolve()
    resolved = report_path.resolve()
    if not resolved.is_relative_to(root):
        raise RunnerError("Runner report path escapes the workspace")
    return resolved


def _safe_environment(base_url: str) -> dict[str, str]:
    environment = {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
        "SPECVORA_BASE_URL": base_url,
    }
    for name in ("APPDATA", "LOCALAPPDATA", "PATH", "SYSTEMROOT", "TEMP", "TMP"):
        if value := os.environ.get(name):
            environment[name] = value
    return environment


def _bounded(value: str | None) -> str:
    text = value or ""
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + "\n...[output truncated by Specvora]"
