"""Command-line leased OIDC monitoring cycle."""

import argparse
import json
import os
from pathlib import Path

from specvora.oidc_cycle import run_oidc_monitor_cycle


def main() -> None:
    parser = argparse.ArgumentParser(prog="specvora-oidc-cycle")
    parser.add_argument("--discovery-endpoint", required=True)
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--provider-allowed-host", action="append", required=True)
    parser.add_argument("--trust-file", type=Path, required=True)
    parser.add_argument("--audit-log", type=Path, required=True)
    parser.add_argument("--alert-endpoint", required=True)
    parser.add_argument("--alert-allowed-host", action="append", required=True)
    parser.add_argument("--state-database", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    args = parser.parse_args()
    result = run_oidc_monitor_cycle(
        args.discovery_endpoint, args.issuer, set(args.provider_allowed_host),
        args.trust_file, args.audit_log, args.workspace_root, args.alert_endpoint,
        set(args.alert_allowed_host), os.getenv("SPECVORA_OIDC_ALERT_TOKEN", ""),
        args.state_database,
    )
    print(json.dumps(result.model_dump(mode="json"), sort_keys=True))
    if result.status == "DELIVERY_FAILED":
        raise SystemExit(20)


if __name__ == "__main__":
    main()
