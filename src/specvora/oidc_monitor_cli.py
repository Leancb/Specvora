"""Read-only command-line OIDC trust monitor."""

import argparse
import json
from pathlib import Path

from specvora.oidc_monitor import monitor_oidc_trust


def main() -> None:
    parser = argparse.ArgumentParser(prog="specvora-oidc-monitor")
    parser.add_argument("--discovery-endpoint", required=True)
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--allowed-host", action="append", required=True)
    parser.add_argument("--trust-file", type=Path, required=True)
    parser.add_argument("--audit-log", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = monitor_oidc_trust(
        args.discovery_endpoint, args.issuer, set(args.allowed_host), args.trust_file,
        args.audit_log, args.workspace_root,
    )
    serialized = json.dumps(report.model_dump(mode="json"), sort_keys=True)
    if args.output:
        output = (args.output if args.output.is_absolute()
                  else args.workspace_root / args.output).resolve()
        if output.suffix.lower() != ".json" or not output.is_relative_to(
            args.workspace_root.resolve()
        ):
            raise ValueError("OIDC monitor output escapes the workspace")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(serialized + "\n")
    print(serialized)
    if report.status != "HEALTHY":
        raise SystemExit(10 if report.status == "REVIEW_REQUIRED" else 20)


if __name__ == "__main__":
    main()
