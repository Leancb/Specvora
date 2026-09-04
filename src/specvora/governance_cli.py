"""Operator-only interface. Private keys are never accepted by the web portal."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from specvora.authorization import execution_action
from specvora.combined_release import CombinedReleaseRequest, assess_combined
from specvora.playwright_runner import PlaywrightRunnerRequest
from specvora.runner import RunnerRequest
from specvora.signed_approval import (
    ApprovalClaims,
    SignedApproval,
    consume_approval,
    sign_approval,
    verify_approval,
)


def confined(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("Governance artifact escapes the workspace")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(prog="specvora-governance")
    parser.add_argument("--workspace-root", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare-execution")
    prepare.add_argument("input", type=Path, help="Runner request JSON")
    prepare.add_argument("--kind", choices=["api", "browser"], required=True)
    prepare.add_argument("--output", type=Path, required=True)
    combined = commands.add_parser("assess-combined")
    combined.add_argument("input", type=Path)
    combined.add_argument("--output", type=Path, required=True)
    signing = commands.add_parser("sign")
    signing.add_argument("input", type=Path, help="Approval claims JSON")
    signing.add_argument("--artifact", type=Path, required=True)
    signing.add_argument("--private-key", type=Path, required=True, help="Raw 32-byte Ed25519 key")
    signing.add_argument("--approval", required=True)
    signing.add_argument("--output", type=Path, required=True)
    for command in ("verify", "consume"):
        verification = commands.add_parser(command)
        verification.add_argument("input", type=Path, help="Signed approval JSON")
        verification.add_argument("--artifact", type=Path, required=True)
        verification.add_argument("--public-key", type=Path, required=True)
        verification.add_argument("--project-id", required=True)
        verification.add_argument("--purpose", required=True)
        if command == "consume":
            verification.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    raw = confined(args.input, args.workspace_root).read_bytes()
    if args.command == "prepare-execution":
        request_type = RunnerRequest if args.kind == "api" else PlaywrightRunnerRequest
        request = request_type.model_validate_json(raw)
        if request.workspace_root.resolve() != args.workspace_root.resolve():
            raise ValueError("Request workspace differs from the operator workspace")
        target = confined(args.output, args.workspace_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(execution_action(request, args.kind))
        print(json.dumps({"output": str(target)}))
        return
    if args.command == "assess-combined":
        result = assess_combined(CombinedReleaseRequest.model_validate_json(raw))
    elif args.command == "sign":
        key = Ed25519PrivateKey.from_private_bytes(args.private_key.read_bytes())
        result = sign_approval(
            ApprovalClaims.model_validate_json(raw),
            confined(args.artifact, args.workspace_root).read_bytes(),
            key,
            args.approval,
        )
    else:
        arguments = (
            SignedApproval.model_validate_json(raw),
            confined(args.artifact, args.workspace_root).read_bytes(),
            Ed25519PublicKey.from_public_bytes(args.public_key.read_bytes()),
            args.project_id,
            args.purpose,
            datetime.now(UTC),
        )
        if args.command == "consume":
            consume_approval(*arguments, ledger=confined(args.ledger, args.workspace_root))
        else:
            verify_approval(*arguments)
        print(json.dumps({"valid": True, "consumed": args.command == "consume"}))
        return
    target = confined(args.output, args.workspace_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(result.model_dump_json(indent=2) + "\n")
    print(json.dumps({"output": str(target)}))


if __name__ == "__main__":
    main()
