import json
from pathlib import Path

import pytest

from specvora.pytest_ingest import PytestIngestRequest, ingest_pytest_report, write_evidence


def write_report(
    path: Path, tests: list[dict[str, str]], summary: dict[str, int] | None = None
) -> None:
    payload = {"tests": tests, "summary": summary or {}}
    path.write_text(json.dumps(payload), encoding="utf-8")


def request(root: Path, report: Path, **overrides: object) -> PytestIngestRequest:
    values = {
        "project_id": "petstore",
        "run_id": "run-101",
        "report_path": report,
        "workspace_root": root,
        "requirements_total": 3,
        "requirements_covered": 3,
        "critical_markers": ["security", "payment"],
    }
    values.update(overrides)
    return PytestIngestRequest.model_validate(values)


def test_ingests_report_and_normalizes_auditable_evidence(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    tests = [
        {"nodeid": "test_api.py::test_ok", "outcome": "passed"},
        {"nodeid": "test_security.py::test_auth", "outcome": "failed"},
        {"nodeid": "test_ui.py::test_optional", "outcome": "skipped"},
    ]
    write_report(report, tests, {"passed": 1, "failed": 1, "skipped": 1, "total": 3})
    evidence = ingest_pytest_report(request(tmp_path, report))
    assert evidence.result.total == 2
    assert evidence.result.critical_failures == 1
    assert evidence.skipped == 1
    assert len(evidence.report_sha256) == 64
    output = write_evidence(evidence, tmp_path / "runs/evidence.json", tmp_path)
    assert json.loads(output.read_text())["source"] == "pytest-json-report"


def test_rejects_report_and_output_outside_workspace(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-report.json"
    write_report(outside, [{"nodeid": "test_ok", "outcome": "passed"}])
    with pytest.raises(ValueError, match="escapes"):
        ingest_pytest_report(request(tmp_path, outside))
    inside = tmp_path / "report.json"
    write_report(inside, [{"nodeid": "test_ok", "outcome": "passed"}])
    evidence = ingest_pytest_report(request(tmp_path, inside))
    with pytest.raises(ValueError, match="output escapes"):
        write_evidence(evidence, outside, tmp_path)


def test_rejects_inconsistent_or_unsupported_report(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    write_report(report, [{"nodeid": "test_ok", "outcome": "passed"}], {"passed": 2})
    with pytest.raises(ValueError, match="does not match"):
        ingest_pytest_report(request(tmp_path, report))
    write_report(report, [{"nodeid": "test_ok", "outcome": "error"}])
    with pytest.raises(ValueError, match="supported outcome"):
        ingest_pytest_report(request(tmp_path, report))
