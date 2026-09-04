from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from urllib.parse import urlparse

from pydantic import BaseModel, Field

from specvora.authorization import authorize_action, execution_action
from specvora.playwright import normalized_hosts
from specvora.policy import PolicyViolation
from specvora.runner import MAX_OUTPUT_CHARS, RunnerError
from specvora.signed_approval import SignedApproval


class PlaywrightRunnerRequest(BaseModel):
    project_id: str = ""
    signed_approval: SignedApproval | None = None
    workspace_root: Path
    generated_dir: Path
    report_path: Path
    web_base_url: str
    allowed_hosts: list[str] = Field(min_length=1)
    approval: str
    timeout_seconds: int = Field(default=120, ge=1, le=600)


class PlaywrightRunnerOutcome(BaseModel):
    approval_id: str | None = None
    command: list[str]
    exit_code: int
    report_path: Path
    stdout: str
    stderr: str
    duration_seconds: float
    started_at: datetime


def run_generated_playwright(request: PlaywrightRunnerRequest) -> PlaywrightRunnerOutcome:
    playwright_dir = _validate_playwright_execution(request)
    report_path = _confined_path(request.report_path, request.workspace_root, "report")
    generated_dir = request.generated_dir.resolve()
    if report_path.is_relative_to(generated_dir):
        raise PolicyViolation("Playwright report must not overwrite generated artifacts")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    executable = "npx.cmd" if os.name == "nt" else "npx"
    command = [
        executable,
        "playwright",
        "test",
        "test_generated_web.spec.ts",
        "--config=playwright.config.ts",
        "--reporter=json",
    ]
    approval_id = authorize_action(request.signed_approval, execution_action(request, "browser"),
                     request.project_id, "browser-execution")
    started_at = datetime.now(UTC)
    started = monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=playwright_dir,
            env=_safe_environment(request),
            capture_output=True,
            text=True,
            timeout=request.timeout_seconds,
            check=False,
            shell=False,
        )
    except FileNotFoundError as exc:
        raise RunnerError(
            "Playwright runtime was not found; install the generated project"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise RunnerError(
            f"Controlled Playwright run timed out after {request.timeout_seconds} seconds"
        ) from exc
    duration = monotonic() - started
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        details = _bounded(completed.stderr or completed.stdout).strip()
        suffix = f": {details}" if details else ""
        raise RunnerError(f"Playwright did not produce the required JSON report{suffix}") from exc
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return PlaywrightRunnerOutcome(
        approval_id=approval_id,
        command=command,
        exit_code=completed.returncode,
        report_path=report_path,
        stdout=_bounded(completed.stdout),
        stderr=_bounded(completed.stderr),
        duration_seconds=duration,
        started_at=started_at,
    )


def _validate_playwright_execution(request: PlaywrightRunnerRequest) -> Path:
    if request.approval != "APPROVED_PLAYWRIGHT":
        raise PolicyViolation("Explicit Playwright approval is required")
    parsed = urlparse(request.web_base_url)
    allowed = {host.strip().lower() for host in request.allowed_hosts}
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise PolicyViolation("Web base URL must use HTTP or HTTPS and include a host")
    if parsed.hostname.lower() not in allowed:
        raise PolicyViolation(f"Host is not allowed: {parsed.hostname}")
    generated_dir = _confined_path(request.generated_dir, request.workspace_root, "generated")
    playwright_dir = _confined_path(
        generated_dir / "playwright", request.workspace_root, "Playwright"
    )
    for name in (
        "test_generated_web.spec.ts",
        "playwright.config.ts",
        "playwright-plan.json",
        "package.json",
    ):
        artifact = _confined_path(playwright_dir / name, request.workspace_root, name)
        if not artifact.is_file():
            raise PolicyViolation(f"Generated Playwright file was not found: {name}")
    gate_file = _confined_path(
        generated_dir / "quality-gate.json", request.workspace_root, "quality gate"
    )
    try:
        gate = json.loads(gate_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyViolation("Generation quality gate is invalid") from exc
    if not isinstance(gate, dict) or gate.get("status") != "READY_FOR_HUMAN_APPROVAL":
        raise PolicyViolation("Generation quality gate blocks Playwright execution")
    _validate_plan(playwright_dir / "playwright-plan.json", request)
    return playwright_dir


def _validate_plan(plan_file: Path, request: PlaywrightRunnerRequest) -> None:
    try:
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyViolation("Playwright plan is invalid") from exc
    if not isinstance(plan, dict) or plan.get("authority") != "human-review-required":
        raise PolicyViolation("Playwright plan is invalid")
    planned_url = plan.get("base_url")
    if not isinstance(planned_url, str) or planned_url.rstrip("/") != request.web_base_url.rstrip(
        "/"
    ):
        raise PolicyViolation("Requested web base URL differs from the reviewed plan")
    if plan.get("allowed_hosts") != normalized_hosts(request.allowed_hosts):
        raise PolicyViolation("Requested allowlist differs from the reviewed plan")


def _confined_path(path: Path, workspace_root: Path, label: str) -> Path:
    root = workspace_root.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise PolicyViolation(f"{label} path escapes the workspace")
    return resolved


def _safe_environment(request: PlaywrightRunnerRequest) -> dict[str, str]:
    environment = {
        "CI": "1",
        "PLAYWRIGHT_BROWSERS_PATH": "0",
        "SPECVORA_WEB_BASE_URL": request.web_base_url,
        "SPECVORA_ALLOWED_HOSTS": json.dumps(normalized_hosts(request.allowed_hosts)),
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
