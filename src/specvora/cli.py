import argparse
import json
import os
from pathlib import Path

from specvora.ai_proposals import DEFAULT_MODEL, propose_scenarios
from specvora.audit import append_assessment, verify_audit_log
from specvora.confidence import TestRunResult, assess_release
from specvora.egress import create_egress_policy, verify_egress_policy
from specvora.pipeline import run_analysis
from specvora.playwright_ingest import (
    PlaywrightIngestRequest,
    ingest_playwright_report,
    write_playwright_evidence,
)
from specvora.playwright_runner import PlaywrightRunnerRequest, run_generated_playwright
from specvora.proposal_review import review_and_promote
from specvora.pytest_ingest import PytestIngestRequest, ingest_pytest_report, write_evidence
from specvora.runner import RunnerRequest, run_generated_tests
from specvora.signed_approval import SignedApproval


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
    run_parser.add_argument("--signed-approval", type=Path)
    run_parser.add_argument("--timeout", type=int, default=60)
    run_parser.add_argument("--project-id", required=True)
    run_parser.add_argument("--run-id", required=True)
    run_parser.add_argument("--requirements-total", type=int, required=True)
    run_parser.add_argument("--requirements-covered", type=int, required=True)
    run_parser.add_argument("--critical-marker", action="append", default=[])
    web_run_parser = commands.add_parser(
        "run-playwright", help="Run approved generated browser tests with fixed controls"
    )
    web_run_parser.add_argument("--workspace-root", type=Path, required=True)
    web_run_parser.add_argument("--generated-dir", type=Path, required=True)
    web_run_parser.add_argument("--report-out", type=Path, required=True)
    web_run_parser.add_argument("--web-base-url", required=True)
    web_run_parser.add_argument("--allowed-host", action="append", required=True)
    web_run_parser.add_argument("--approval", required=True)
    web_run_parser.add_argument("--signed-approval", type=Path)
    web_run_parser.add_argument("--project-id", default="")
    web_run_parser.add_argument("--timeout", type=int, default=120)
    web_ingest_parser = commands.add_parser(
        "ingest-playwright", help="Normalize a confined Playwright JSON report"
    )
    web_ingest_parser.add_argument("report_path", type=Path)
    web_ingest_parser.add_argument("--workspace-root", type=Path, required=True)
    web_ingest_parser.add_argument("--project-id", required=True)
    web_ingest_parser.add_argument("--run-id", required=True)
    web_ingest_parser.add_argument("--requirements-total", type=int, required=True)
    web_ingest_parser.add_argument("--requirements-covered", type=int, required=True)
    web_ingest_parser.add_argument("--critical-marker", action="append", default=[])
    web_ingest_parser.add_argument("--evidence-out", type=Path, required=True)
    web_ingest_parser.add_argument("--audit-log", type=Path, required=True)
    ai_parser = commands.add_parser(
        "propose-ai", help="Request schema-validated AI scenario proposals"
    )
    ai_parser.add_argument("project_file", type=Path)
    ai_parser.add_argument("--workspace-root", type=Path, default=Path("workspaces"))
    ai_parser.add_argument("--output", type=Path, required=True)
    ai_parser.add_argument("--model", default=os.environ.get("SPECVORA_AI_MODEL", DEFAULT_MODEL))
    review_parser = commands.add_parser(
        "review-ai", help="Record human decisions and promote accepted AI proposals"
    )
    review_parser.add_argument("project_file", type=Path)
    review_parser.add_argument("proposal_file", type=Path)
    review_parser.add_argument("decision_file", type=Path)
    review_parser.add_argument("--workspace-root", type=Path, required=True)
    review_parser.add_argument("--review-record", type=Path, required=True)
    review_parser.add_argument("--promotion-catalog", type=Path, required=True)
    egress_parser = commands.add_parser(
        "create-egress-policy", help="Create an approved default-deny container egress policy"
    )
    egress_parser.add_argument("--target-url", required=True)
    egress_parser.add_argument("--allowed-host", action="append", required=True)
    egress_parser.add_argument("--approval", required=True)
    egress_parser.add_argument("--workspace-root", type=Path, required=True)
    egress_parser.add_argument("--policy-dir", type=Path, required=True)
    egress_verify_parser = commands.add_parser(
        "verify-egress-policy", help="Verify an immutable container egress policy"
    )
    egress_verify_parser.add_argument("policy_file", type=Path)
    egress_verify_parser.add_argument("rules_file", type=Path)
    egress_verify_parser.add_argument("--workspace-root", type=Path, required=True)
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
    elif args.command == "run-pytest":
        run = run_generated_tests(
            RunnerRequest(
                project_id=args.project_id,
                signed_approval=(SignedApproval.model_validate_json(args.signed_approval.read_bytes())
                                 if args.signed_approval else None),
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
    elif args.command == "run-playwright":
        run = run_generated_playwright(
            PlaywrightRunnerRequest(
                project_id=args.project_id,
                signed_approval=(SignedApproval.model_validate_json(args.signed_approval.read_bytes())
                                 if args.signed_approval else None),
                workspace_root=args.workspace_root,
                generated_dir=args.generated_dir,
                report_path=args.report_out,
                web_base_url=args.web_base_url,
                allowed_hosts=args.allowed_host,
                approval=args.approval,
                timeout_seconds=args.timeout,
            )
        )
        output = {"run": run.model_dump(mode="json")}
    elif args.command == "ingest-playwright":
        evidence = ingest_playwright_report(
            PlaywrightIngestRequest(
                project_id=args.project_id,
                run_id=args.run_id,
                report_path=args.report_path,
                workspace_root=args.workspace_root,
                requirements_total=args.requirements_total,
                requirements_covered=args.requirements_covered,
                critical_markers=args.critical_marker,
            )
        )
        evidence_path = write_playwright_evidence(evidence, args.evidence_out, args.workspace_root)
        assessment = assess_release(evidence.result)
        append_assessment(args.audit_log, assessment)
        output = {
            "evidence": str(evidence_path),
            "report_sha256": evidence.report_sha256,
            "assessment": assessment.model_dump(mode="json"),
        }
    elif args.command == "propose-ai":
        proposal = propose_scenarios(
            args.project_file,
            args.output,
            args.workspace_root,
            model=args.model,
        )
        output = proposal.model_dump(mode="json")
    elif args.command == "review-ai":
        review, catalog = review_and_promote(
            args.project_file,
            args.proposal_file,
            args.decision_file,
            args.review_record,
            args.promotion_catalog,
            args.workspace_root,
        )
        output = {
            "review": review.model_dump(mode="json"),
            "promotion": catalog.model_dump(mode="json"),
        }
    elif args.command == "create-egress-policy":
        policy_path, rules_path, policy = create_egress_policy(
            args.target_url,
            args.allowed_host,
            args.approval,
            args.policy_dir,
            args.workspace_root,
        )
        output = {
            "policy": str(policy_path),
            "rules": str(rules_path),
            "endpoint": policy.endpoint.model_dump(),
            "rules_sha256": policy.rules_sha256,
        }
    else:
        output = {
            "policy": str(args.policy_file),
            "valid": verify_egress_policy(
                args.policy_file, args.rules_file, args.workspace_root
            ),
        }
    print(json.dumps(output, indent=2))
