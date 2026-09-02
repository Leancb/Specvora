import argparse
import json
from pathlib import Path

from specvora.audit import append_assessment, verify_audit_log
from specvora.confidence import TestRunResult, assess_release
from specvora.pipeline import run_analysis
from specvora.pytest_ingest import PytestIngestRequest, ingest_pytest_report, write_evidence
from specvora.runner import RunnerRequest, run_generated_tests


def main() -> None:
    parser = argparse.ArgumentParser(prog="specvora")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze_parser = commands.add_parser("analyze", help="Generate deterministic quality artifacts")
    analyze_parser.add_argument("project_file", type=Path)
    analyze_parser.add_argument("--workspace-root", type=Path, default=Path("workspaces"))
    assess_parser = commands.add_parser("assess", help="Calculate deterministic release confidence")
    assess_parser.add_argument("results_file", type=Path)
    assess_parser.add_argument("--audit-log", type=Path, required=True)
    verify_parser = commands.add_parser("verify-audit", help="Verify the audit hash chain")
    verify_parser.add_argument("audit_log", type=Path)
    ingest_parser = commands.add_parser(
        "ingest-pytest", help="Normalize a confined Pytest JSON report"
    )
    ingest_parser.add_argument("report_path", type=Path)
    ingest_parser.add_argument("--workspace-root", type=Path, required=True)
    ingest_parser.add_argument("--project-id", required=True)
    ingest_parser.add_argument("--run-id", required=True)
    ingest_parser.add_argument("--requirements-total", type=int, required=True)
    ingest_parser.add_argument("--requirements-covered", type=int, required=True)
    ingest_parser.add_argument("--critical-marker", action="append", default=[])
    ingest_parser.add_argument("--evidence-out", type=Path, required=True)
    ingest_parser.add_argument("--audit-log", type=Path, required=True)
    run_parser = commands.add_parser(
        "run-pytest", help="Run approved generated tests with fixed controls"
    )
    run_parser.add_argument("--workspace-root", type=Path, required=True)
    run_parser.add_argument("--generated-dir", type=Path, required=True)
    run_parser.add_argument("--report-out", type=Path, required=True)
    run_parser.add_argument("--evidence-out", type=Path, required=True)
    run_parser.add_argument("--audit-log", type=Path, required=True)
    run_parser.add_argument("--base-url", required=True)
    run_parser.add_argument("--allowed-host", action="append", required=True)
    run_parser.add_argument("--approval", required=True)
    run_parser.add_argument("--timeout", type=int, default=60)
    run_parser.add_argument("--project-id", required=True)
    run_parser.add_argument("--run-id", required=True)
    run_parser.add_argument("--requirements-total", type=int, required=True)
    run_parser.add_argument("--requirements-covered", type=int, required=True)
    run_parser.add_argument("--critical-marker", action="append", default=[])
    args = parser.parse_args()
    if args.command == "analyze":
        result, files = run_analysis(args.project_file, args.workspace_root)
        output = {
            "project_id": result.project.project_id,
            "artifacts": [str(path) for path in files],
        }
    elif args.command == "assess":
        result = TestRunResult.model_validate_json(args.results_file.read_text(encoding="utf-8"))
        assessment = assess_release(result)
        append_assessment(args.audit_log, assessment)
        output = assessment.model_dump(mode="json")
    elif args.command == "verify-audit":
        output = {"audit_log": str(args.audit_log), "valid": verify_audit_log(args.audit_log)}
    elif args.command == "ingest-pytest":
        request = PytestIngestRequest(
            project_id=args.project_id,
            run_id=args.run_id,
            report_path=args.report_path,
            workspace_root=args.workspace_root,
            requirements_total=args.requirements_total,
            requirements_covered=args.requirements_covered,
            critical_markers=args.critical_marker,
        )
        evidence = ingest_pytest_report(request)
        evidence_path = write_evidence(evidence, args.evidence_out, args.workspace_root)
        assessment = assess_release(evidence.result)
        append_assessment(args.audit_log, assessment)
        output = {
            "evidence": str(evidence_path),
            "report_sha256": evidence.report_sha256,
            "assessment": assessment.model_dump(mode="json"),
        }
    else:
        run = run_generated_tests(
            RunnerRequest(
                workspace_root=args.workspace_root,
                generated_dir=args.generated_dir,
                report_path=args.report_out,
                base_url=args.base_url,
                allowed_hosts=args.allowed_host,
                approval=args.approval,
                timeout_seconds=args.timeout,
            )
        )
        evidence = ingest_pytest_report(
            PytestIngestRequest(
                project_id=args.project_id,
                run_id=args.run_id,
                report_path=run.report_path,
                workspace_root=args.workspace_root,
                requirements_total=args.requirements_total,
                requirements_covered=args.requirements_covered,
                critical_markers=args.critical_marker,
            )
        )
        evidence_path = write_evidence(evidence, args.evidence_out, args.workspace_root)
        assessment = assess_release(evidence.result)
        append_assessment(args.audit_log, assessment)
        output = {
            "run": run.model_dump(mode="json"),
            "evidence": str(evidence_path),
            "assessment": assessment.model_dump(mode="json"),
        }
    print(json.dumps(output, indent=2))
