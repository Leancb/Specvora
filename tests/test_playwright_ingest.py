import json
import sys
from pathlib import Path

import pytest

from specvora.audit import verify_audit_log
from specvora.cli import main
from specvora.confidence import assess_release
from specvora.playwright_ingest import (
    PlaywrightIngestRequest,
    ingest_playwright_report,
    write_playwright_evidence,
)


def write_report(path: Path, statuses: list[str], stats: dict[str, int] | None = None) -> None:
    tests = [
        {"projectId": "chromium", "projectName": "chromium", "status": status}
        for status in statuses
    ]
    specs = [
        {"title": f"journey-{index}", "tests": [test]} for index, test in enumerate(tests, start=1)
    ]
    payload = {"suites": [{"title": "generated", "specs": specs}], "stats": stats or {}}
    path.write_text(json.dumps(payload), encoding="utf-8")


def request(root: Path, report: Path, **overrides: object) -> PlaywrightIngestRequest:
    values = {
        "project_id": "web-demo",
        "run_id": "web-101",
        "report_path": report,
        "workspace_root": root,
        "requirements_total": 4,
        "requirements_covered": 4,
        "critical_markers": ["journey-2"],
    }
    values.update(overrides)
    return PlaywrightIngestRequest.model_validate(values)


def test_normalizes_expected_unexpected_flaky_and_skipped(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    write_report(
        report,
        ["expected", "unexpected", "flaky", "skipped"],
        {"expected": 1, "unexpected": 1, "flaky": 1, "skipped": 1},
    )
    evidence = ingest_playwright_report(request(tmp_path, report))
    assert evidence.collected == 4
    assert evidence.passed == 1
    assert evidence.failed == 2
    assert evidence.flaky == 1
    assert evidence.skipped == 1
    assert evidence.critical_failures == 1
    assert evidence.result.total == 3
    assert len(evidence.report_sha256) == 64
    output = write_playwright_evidence(evidence, tmp_path / "runs/evidence.json", tmp_path)
    assert json.loads(output.read_text())["source"] == "playwright-json-reporter"


def test_collects_nested_suites_and_rejects_inconsistent_stats(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    payload = {
        "suites": [
            {
                "title": "file",
                "specs": [],
                "suites": [
                    {
                        "title": "describe",
                        "specs": [
                            {
                                "title": "nested journey",
                                "tests": [{"projectId": "chromium", "status": "expected"}],
                            }
                        ],
                    }
                ],
            }
        ],
        "stats": {"expected": 2},
    }
    report.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match"):
        ingest_playwright_report(request(tmp_path, report))
    payload["stats"]["expected"] = 1
    report.write_text(json.dumps(payload), encoding="utf-8")
    assert ingest_playwright_report(request(tmp_path, report)).passed == 1


def test_top_level_error_is_a_critical_failure(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    write_report(
        report,
        ["expected"],
        {"expected": 1, "unexpected": 0, "flaky": 0, "skipped": 0},
    )
    payload = json.loads(report.read_text())
    payload["errors"] = [{"message": "Browser setup failed"}]
    report.write_text(json.dumps(payload), encoding="utf-8")
    evidence = ingest_playwright_report(request(tmp_path, report))
    assert evidence.top_level_errors == 1
    assert evidence.failed == 1
    assert evidence.critical_failures == 1
    assert evidence.result.total == 2
    assert assess_release(evidence.result).decision == "BLOCK"


def test_rejects_unsupported_empty_or_external_reports(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    write_report(report, ["timedOut"])
    with pytest.raises(ValueError, match="supported status"):
        ingest_playwright_report(request(tmp_path, report))
    write_report(report, ["skipped"])
    with pytest.raises(ValueError, match="no executed"):
        ingest_playwright_report(request(tmp_path, report))
    outside = tmp_path.parent / "outside-playwright.json"
    write_report(outside, ["expected"])
    with pytest.raises(ValueError, match="escapes"):
        ingest_playwright_report(request(tmp_path, outside))


def test_cli_writes_evidence_assessment_and_chained_audit(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    report = tmp_path / "runs/playwright.json"
    report.parent.mkdir()
    write_report(
        report,
        ["expected", "expected"],
        {"expected": 2, "unexpected": 0, "flaky": 0, "skipped": 0},
    )
    evidence = tmp_path / "evidence/playwright.json"
    audit = tmp_path / "audit/assessment.jsonl"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "specvora",
            "ingest-playwright",
            str(report),
            "--workspace-root",
            str(tmp_path),
            "--project-id",
            "web-demo",
            "--run-id",
            "web-102",
            "--requirements-total",
            "2",
            "--requirements-covered",
            "2",
            "--evidence-out",
            str(evidence),
            "--audit-log",
            str(audit),
        ],
    )
    main()
    output = json.loads(capsys.readouterr().out)
    assert output["assessment"]["decision"] == "RELEASE"
    assert output["evidence"] == str(evidence)
    assert verify_audit_log(audit)
