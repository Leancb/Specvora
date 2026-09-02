from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from specvora.confidence import TestRunResult

MAX_REPORT_BYTES = 5 * 1024 * 1024
SUPPORTED_STATUSES = {"expected", "unexpected", "flaky", "skipped"}


class PlaywrightIngestRequest(BaseModel):
    project_id: str
    run_id: str
    report_path: Path
    workspace_root: Path
    requirements_total: int = Field(gt=0)
    requirements_covered: int = Field(ge=0)
    critical_markers: list[str] = Field(default_factory=list)


class PlaywrightEvidence(BaseModel):
    source: str = "playwright-json-reporter"
    report_path: str
    report_sha256: str
    collected: int
    passed: int
    failed: int
    flaky: int
    skipped: int
    top_level_errors: int
    critical_failures: int
    failed_test_ids: list[str]
    normalized_at: datetime
    result: TestRunResult


def ingest_playwright_report(request: PlaywrightIngestRequest) -> PlaywrightEvidence:
    report_path = _confined_report(request.report_path, request.workspace_root)
    raw = report_path.read_bytes()
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError("Playwright report exceeds the 5 MB limit")
    try:
        report = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Playwright report is not valid UTF-8 JSON") from exc
    if not isinstance(report, dict):
        raise ValueError("Playwright report root must be an object")
    tests = _collect_tests(report.get("suites"))
    top_level_errors = _top_level_errors(report.get("errors", []))
    statuses = [_status(test) for test in tests]
    passed = statuses.count("expected")
    flaky = statuses.count("flaky")
    test_failures = statuses.count("unexpected") + flaky
    failed = test_failures + top_level_errors
    skipped = statuses.count("skipped")
    if passed + failed == 0:
        raise ValueError("Playwright report contains no executed pass/fail tests")
    _validate_stats(report.get("stats"), passed, test_failures - flaky, flaky, skipped)
    failed_test_ids = [
        _test_id(test)
        for test, status in zip(tests, statuses, strict=True)
        if status in {"unexpected", "flaky"}
    ]
    failed_test_ids.extend(
        f"playwright:top-level-error:{index}" for index in range(1, top_level_errors + 1)
    )
    failed_test_ids.sort()
    markers = [marker.casefold() for marker in request.critical_markers if marker]
    critical = top_level_errors + sum(
        any(marker in test_id.casefold() for marker in markers)
        for test_id in failed_test_ids
        if not test_id.startswith("playwright:top-level-error:")
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
    return PlaywrightEvidence(
        report_path=str(report_path),
        report_sha256=hashlib.sha256(raw).hexdigest(),
        collected=len(tests),
        passed=passed,
        failed=failed,
        flaky=flaky,
        skipped=skipped,
        top_level_errors=top_level_errors,
        critical_failures=critical,
        failed_test_ids=failed_test_ids,
        normalized_at=datetime.now(UTC),
        result=result,
    )


def write_playwright_evidence(
    evidence: PlaywrightEvidence, output_path: Path, workspace_root: Path
) -> Path:
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
        raise ValueError("Playwright report escapes the workspace")
    if not resolved.is_file():
        raise ValueError("Playwright report was not found")
    return resolved


def _collect_tests(suites: Any) -> list[dict[str, Any]]:
    if not isinstance(suites, list):
        raise ValueError("Playwright report must contain a suites array")
    collected = []
    for suite in suites:
        if not isinstance(suite, dict):
            raise ValueError("Every Playwright suite must be an object")
        specs = suite.get("specs", [])
        children = suite.get("suites", [])
        if not isinstance(specs, list) or not isinstance(children, list):
            raise ValueError("Playwright suite specs and suites must be arrays")
        for spec in specs:
            if not isinstance(spec, dict) or not isinstance(spec.get("tests"), list):
                raise ValueError("Every Playwright spec must contain a tests array")
            for test in spec["tests"]:
                if not isinstance(test, dict):
                    raise ValueError("Every Playwright test must be an object")
                collected.append({**test, "spec_title": spec.get("title", "")})
        collected.extend(_collect_tests(children))
    return collected


def _status(test: dict[str, Any]) -> str:
    status = test.get("status")
    if status not in SUPPORTED_STATUSES:
        raise ValueError("Every Playwright test must have a supported status")
    return str(status)


def _top_level_errors(errors: Any) -> int:
    if not isinstance(errors, list) or any(not isinstance(error, dict) for error in errors):
        raise ValueError("Playwright report errors must be an array of objects")
    return len(errors)


def _test_id(test: dict[str, Any]) -> str:
    title = test.get("spec_title")
    project = test.get("projectName") or test.get("projectId")
    parts = [str(value) for value in (project, title) if value]
    return " :: ".join(parts) or "unnamed-playwright-test"


def _validate_stats(stats: Any, passed: int, unexpected: int, flaky: int, skipped: int) -> None:
    if not isinstance(stats, dict):
        raise ValueError("Playwright report stats must be an object")
    expected = {
        "expected": passed,
        "unexpected": unexpected,
        "flaky": flaky,
        "skipped": skipped,
    }
    for key, value in expected.items():
        if key in stats and stats[key] != value:
            raise ValueError(f"Playwright stats {key} does not match tests")
