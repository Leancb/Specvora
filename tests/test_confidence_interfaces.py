import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from specvora.cli import main
from specvora.main import app


def payload() -> dict[str, object]:
    return {
        "project_id": "petstore-demo",
        "run_id": "run-001",
        "total": 10,
        "passed": 10,
        "failed": 0,
        "requirements_total": 2,
        "requirements_covered": 2,
    }


def test_cli_assesses_and_verifies_audit(tmp_path: Path, monkeypatch, capsys) -> None:
    results_file = tmp_path / "results.json"
    audit_log = tmp_path / "audit.jsonl"
    results_file.write_text(json.dumps(payload()), encoding="utf-8")
    monkeypatch.setattr(
        sys, "argv", ["specvora", "assess", str(results_file), "--audit-log", str(audit_log)]
    )
    main()
    assert json.loads(capsys.readouterr().out)["decision"] == "RELEASE"
    monkeypatch.setattr(sys, "argv", ["specvora", "verify-audit", str(audit_log)])
    main()
    assert json.loads(capsys.readouterr().out)["valid"] is True


def test_api_assesses_results_and_writes_audit(tmp_path: Path) -> None:
    audit_log = tmp_path / "audit.jsonl"
    response = TestClient(app).post(
        "/assess", json={"result": payload(), "audit_log": str(audit_log)}
    )
    assert response.status_code == 200
    assert response.json()["score"] == 100
    assert audit_log.is_file()
