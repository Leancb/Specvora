import argparse
import json
from pathlib import Path

from specvora.audit import append_assessment, verify_audit_log
from specvora.confidence import TestRunResult, assess_release
from specvora.pipeline import run_analysis


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
    else:
        output = {"audit_log": str(args.audit_log), "valid": verify_audit_log(args.audit_log)}
    print(json.dumps(output, indent=2))
