import argparse
import json
from pathlib import Path

from specvora.pipeline import run_analysis


def main() -> None:
    parser = argparse.ArgumentParser(prog="specvora")
    commands = parser.add_subparsers(dest="command", required=True)
    analyze_parser = commands.add_parser("analyze", help="Generate deterministic quality artifacts")
    analyze_parser.add_argument("project_file", type=Path)
    analyze_parser.add_argument("--workspace-root", type=Path, default=Path("workspaces"))
    args = parser.parse_args()
    if args.command == "analyze":
        result, files = run_analysis(args.project_file, args.workspace_root)
        print(
            json.dumps(
                {
                    "project_id": result.project.project_id,
                    "artifacts": [str(path) for path in files],
                },
                indent=2,
            )
        )
