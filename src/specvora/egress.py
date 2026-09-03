from __future__ import annotations

import hashlib
import ipaddress
import socket
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field


class EgressEndpoint(BaseModel):
    hostname: str
    port: int = Field(ge=1, le=65535)
    addresses: list[str] = Field(min_length=1)


class EgressPolicy(BaseModel):
    version: Literal["specvora-egress-v1"] = "specvora-egress-v1"
    authority: Literal["human-approved"] = "human-approved"
    created_at: datetime
    endpoint: EgressEndpoint
    default_action: Literal["DROP"] = "DROP"
    rules_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


Resolver = Callable[[str, int], list[tuple]]


def create_egress_policy(
    target_url: str,
    allowed_hosts: list[str],
    approval: str,
    policy_dir: Path,
    workspace_root: Path,
    *,
    resolver: Resolver = socket.getaddrinfo,
) -> tuple[Path, Path, EgressPolicy]:
    if approval != "APPROVED_EGRESS_POLICY":
        raise ValueError("Explicit egress policy approval is required")
    parsed = urlparse(target_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Egress target must be an HTTP or HTTPS URL with a hostname")
    hostname = parsed.hostname.casefold()
    normalized = {host.strip().casefold() for host in allowed_hosts}
    if hostname not in normalized:
        raise ValueError(f"Egress target host is not allowed: {hostname}")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = _resolve_addresses(hostname, port, resolver)
    target = _new_policy_dir(policy_dir, workspace_root)
    rules = _render_nftables(addresses, port)
    rules_path = target / "specvora-egress.nft"
    policy_path = target / "egress-policy.json"
    policy = EgressPolicy(
        created_at=datetime.now(UTC),
        endpoint=EgressEndpoint(hostname=hostname, port=port, addresses=addresses),
        rules_sha256=hashlib.sha256(rules.encode()).hexdigest(),
    )
    rules_path.write_bytes(rules.encode())
    policy_path.write_text(policy.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return policy_path, rules_path, policy


def verify_egress_policy(policy_path: Path, rules_path: Path, workspace_root: Path) -> bool:
    policy_file = _confined_file(policy_path, workspace_root, "policy")
    rules_file = _confined_file(rules_path, workspace_root, "rules")
    try:
        policy = EgressPolicy.model_validate_json(policy_file.read_bytes())
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Egress policy is invalid") from exc
    rules = rules_file.read_bytes()
    if hashlib.sha256(rules).hexdigest() != policy.rules_sha256:
        raise ValueError("Egress rules hash does not match the approved policy")
    expected = _render_nftables(policy.endpoint.addresses, policy.endpoint.port).encode()
    if rules != expected:
        raise ValueError("Egress rules do not match the deterministic policy")
    return True


def _resolve_addresses(hostname: str, port: int, resolver: Resolver) -> list[str]:
    try:
        answers = resolver(hostname, port)
    except OSError as exc:
        raise ValueError(f"Egress target could not be resolved: {hostname}") from exc
    addresses = sorted(
        {str(ipaddress.ip_address(answer[4][0])) for answer in answers},
        key=lambda value: (ipaddress.ip_address(value).version, ipaddress.ip_address(value)),
    )
    if not addresses:
        raise ValueError(f"Egress target could not be resolved: {hostname}")
    return addresses


def _render_nftables(addresses: list[str], port: int) -> str:
    ipv4 = [address for address in addresses if ipaddress.ip_address(address).version == 4]
    ipv6 = [address for address in addresses if ipaddress.ip_address(address).version == 6]
    lines = [
        "table inet specvora {",
        "  chain output {",
        "    type filter hook output priority 0; policy drop;",
        "    ct state established,related accept",
    ]
    if ipv4:
        lines.append(f"    ip daddr {{ {', '.join(ipv4)} }} tcp dport {port} accept")
    if ipv6:
        lines.append(f"    ip6 daddr {{ {', '.join(ipv6)} }} tcp dport {port} accept")
    lines.extend(["  }", "}", ""])
    return "\n".join(lines)


def _new_policy_dir(path: Path, workspace_root: Path) -> Path:
    root = workspace_root.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Egress policy directory escapes the workspace")
    if resolved.exists() and any(resolved.iterdir()):
        raise ValueError("Egress policy directory already contains immutable artifacts")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _confined_file(path: Path, workspace_root: Path, label: str) -> Path:
    root = workspace_root.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"Egress {label} escapes the workspace")
    if not resolved.is_file():
        raise ValueError(f"Egress {label} file was not found")
    return resolved
