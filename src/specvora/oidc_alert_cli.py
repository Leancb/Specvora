"""CLI for delivering an existing OIDC monitor report."""

import argparse
import json
import os
from pathlib import Path

from specvora.oidc_alert import deliver_oidc_alert
from specvora.oidc_monitor import OidcTrustMonitorReport


def main() -> None:
    parser = argparse.ArgumentParser(prog="specvora-oidc-alert")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--allowed-host", action="append", required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    args = parser.parse_args()
    report_path = (
        args.report if args.report.is_absolute() else args.workspace_root / args.report
    ).resolve()
    if (
        report_path.suffix.lower() != ".json"
        or not report_path.is_relative_to(args.workspace_root.resolve())
        or report_path.stat().st_size > 65_536
    ):
        raise ValueError("OIDC monitor report escapes the workspace or is invalid")
    token = os.getenv("SPECVORA_OIDC_ALERT_TOKEN", "")
    report = OidcTrustMonitorReport.model_validate_json(report_path.read_bytes())
    result = deliver_oidc_alert(report, args.endpoint, set(args.allowed_host), token)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
