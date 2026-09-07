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
    args = parser.parse_args()
    report = monitor_oidc_trust(
        args.discovery_endpoint, args.issuer, set(args.allowed_host), args.trust_file,
        args.audit_log, args.workspace_root,
    )
    print(json.dumps(report.model_dump(mode="json"), sort_keys=True))
    if report.status != "HEALTHY":
        raise SystemExit(10 if report.status == "REVIEW_REQUIRED" else 20)


if __name__ == "__main__":
    main()
