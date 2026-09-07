"""Operator CLI for pinned OIDC trust bootstrap and rotation."""

import argparse
import json
from pathlib import Path

from specvora.oidc_trust import refresh_oidc_trust


def main() -> None:
    parser = argparse.ArgumentParser(prog="specvora-oidc-trust")
    parser.add_argument("command", choices=["bootstrap", "rotate"])
    parser.add_argument("--discovery-endpoint", required=True)
    parser.add_argument("--issuer", required=True)
    parser.add_argument("--allowed-host", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    args = parser.parse_args()
    result = refresh_oidc_trust(
        args.discovery_endpoint, args.issuer, set(args.allowed_host), args.output,
        args.workspace_root, bootstrap=args.command == "bootstrap",
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
