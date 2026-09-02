import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from specvora.cli import main
from specvora.main import app


def report(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "tests": [{"nodeid": "test_api.py::test_ok", "outcome": "passed"}],
                "summary": {"passed": 1, "total": 1},
            }
        ),
        encoding="utf-8",
    )


def test_cli_ingests_assesses_and_writes_evidence(tmp_path: Path, monkeypatch, capsys) -> None:
    report_path = tmp_path / "report.json"
    evidence_path = tmp_path / "runs/evidence.json"
    audit_path = tmp_path / "runs/audit.jsonl"
    report(report_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "specvora",
            "ingest-pytest",
            str(report_path),
            "--workspace-root",
            str(tmp_path),
            "--project-id",
            "petstore",
            "--run-id",
            "run-201",
            "--requirements-total",
            "2",
            "--requirements-covered",
            "2",
            "--evidence-out",
            str(evidence_path),
            "--audit-log",
            str(audit_path),
        ],
    )
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["assessment"]["decision"] == "RELEASE"
    assert evidence_path.is_file()
    assert audit_path.is_file()


def test_api_ingests_confined_report(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report(report_path)
    response = TestClient(app).post(
        "/ingest/pytest",
        json={
            "project_id": "petstore",
            "run_id": "run-202",
            "report_path": str(report_path),
            "workspace_root": str(tmp_path),
            "requirements_total": 1,
            "requirements_covered": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["result"]["passed"] == 1
