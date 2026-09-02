from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from specvora.confidence import TestRunResult

MAX_REPORT_BYTES = 5 * 1024 * 1024


class PytestIngestRequest(BaseModel):
    project_id: str
    run_id: str
    report_path: Path
    workspace_root: Path
    requirements_total: int = Field(gt=0)
    requirements_covered: int = Field(ge=0)
    critical_markers: list[str] = Field(default_factory=list)


class PytestEvidence(BaseModel):
    source: str = "pytest-json-report"
    report_path: str
    report_sha256: str
    collected: int
    passed: int
    failed: int
    skipped: int
    critical_failures: int
    failed_nodeids: list[str]
    normalized_at: datetime
    result: TestRunResult


def ingest_pytest_report(request: PytestIngestRequest) -> PytestEvidence:
    report_path = _confined_report(request.report_path, request.workspace_root)
    raw = report_path.read_bytes()
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError("Pytest report exceeds the 5 MB limit")
    try:
        report = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Pytest report is not valid UTF-8 JSON") from exc
    if not isinstance(report, dict):
        raise ValueError("Pytest report root must be an object")
    tests = report.get("tests")
    if not isinstance(tests, list):
        raise ValueError("Pytest report must contain a tests array")
    outcomes = [_outcome(item) for item in tests]
    passed = outcomes.count("passed")
    failed = outcomes.count("failed")
    skipped = outcomes.count("skipped")
    if passed + failed == 0:
        raise ValueError("Pytest report contains no executed pass/fail tests")
    summary = report.get("summary", {})
    _validate_summary(summary, passed, failed, skipped, len(tests))
    failed_nodeids = sorted(
        str(item.get("nodeid"))
        for item in tests
        if isinstance(item, dict) and item.get("outcome") == "failed" and item.get("nodeid")
    )
    normalized_markers = [marker.casefold() for marker in request.critical_markers if marker]
    critical = sum(
        any(marker in nodeid.casefold() for marker in normalized_markers)
        for nodeid in failed_nodeids
    )
    result = TestRunResult(
        project_id=request.project_id,
        run_id=request.run_id,
        total=passed + failed,
        passed=passed,
        failed=failed,
        critical_failures=critical,
        requirements_total=request.requirements_total,
        requirements_covered=request.requirements_covered,
    )
    return PytestEvidence(
        report_path=str(report_path),
        report_sha256=hashlib.sha256(raw).hexdigest(),
        collected=len(tests),
        passed=passed,
        failed=failed,
        skipped=skipped,
        critical_failures=critical,
        failed_nodeids=failed_nodeids,
        normalized_at=datetime.now(UTC),
        result=result,
    )


def write_evidence(evidence: PytestEvidence, output_path: Path, workspace_root: Path) -> Path:
    root = workspace_root.resolve()
    target = output_path.resolve()
    if not target.is_relative_to(root):
        raise ValueError("Evidence output escapes the workspace")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(evidence.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return target


def _confined_report(report_path: Path, workspace_root: Path) -> Path:
    root = workspace_root.resolve()
    resolved = report_path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Pytest report escapes the workspace")
    if not resolved.is_file():
        raise ValueError("Pytest report was not found")
    return resolved


def _outcome(item: Any) -> str:
    if not isinstance(item, dict) or item.get("outcome") not in {"passed", "failed", "skipped"}:
        raise ValueError("Every Pytest test must have a supported outcome")
    return str(item["outcome"])


def _validate_summary(summary: Any, passed: int, failed: int, skipped: int, collected: int) -> None:
    if not isinstance(summary, dict):
        raise ValueError("Pytest report summary must be an object")
    expected = {"passed": passed, "failed": failed, "skipped": skipped, "total": collected}
    for key, value in expected.items():
        if key in summary and summary[key] != value:
            raise ValueError(f"Pytest summary {key} does not match tests")
