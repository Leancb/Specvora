import json
from pathlib import Path

from specvora.pytest_ingest import PytestIngestRequest, ingest_pytest_report
from specvora.runner import RunnerRequest, run_generated_tests


def test_runner_produces_ingestable_real_pytest_report(tmp_path: Path) -> None:
    generated = tmp_path / "project/generated"
    generated.mkdir(parents=True)
    (generated / "test_generated_api.py").write_text(
        "def test_generated_passes():\n    assert 2 + 2 == 4\n", encoding="utf-8"
    )
    (generated / "quality-gate.json").write_text(
        json.dumps({"status": "READY_FOR_HUMAN_APPROVAL"}), encoding="utf-8"
    )
    report = tmp_path / "project/runs/report.json"
    outcome = run_generated_tests(
        RunnerRequest(
            workspace_root=tmp_path,
            generated_dir=generated,
            report_path=report,
            base_url="http://localhost:8080",
            allowed_hosts=["localhost"],
            approval="APPROVED",
            timeout_seconds=30,
        )
    )
    assert outcome.exit_code == 0
    assert json.loads(report.read_text())["summary"]["passed"] == 1
    evidence = ingest_pytest_report(
        PytestIngestRequest(
            project_id="demo",
            run_id="real-001",
            report_path=report,
            workspace_root=tmp_path,
            requirements_total=1,
            requirements_covered=1,
        )
    )
    assert evidence.result.passed == 1
