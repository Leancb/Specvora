import json
import sys
from pathlib import Path

import pytest

from specvora.cli import main
from specvora.egress import create_egress_policy, verify_egress_policy


def resolver(host: str, port: int) -> list[tuple]:
    assert (host, port) == ("api.example.test", 8443)
    return [
        (2, 1, 6, "", ("203.0.113.20", port)),
        (10, 1, 6, "", ("2001:db8::20", port, 0, 0)),
        (2, 1, 6, "", ("203.0.113.20", port)),
    ]


def create(tmp_path: Path, **overrides: object):
    values = {
        "target_url": "https://api.example.test:8443/v1",
        "allowed_hosts": ["api.example.test"],
        "approval": "APPROVED_EGRESS_POLICY",
        "policy_dir": tmp_path / "project/egress/run-001",
        "workspace_root": tmp_path,
        "resolver": resolver,
    }
    values.update(overrides)
    return create_egress_policy(**values)


def test_policy_pins_addresses_denies_by_default_and_verifies(tmp_path: Path) -> None:
    policy_path, rules_path, policy = create(tmp_path)
    rules = rules_path.read_text(encoding="utf-8")
    assert policy.endpoint.addresses == ["203.0.113.20", "2001:db8::20"]
    assert policy.endpoint.port == 8443
    assert "policy drop" in rules
    assert "203.0.113.20" in rules and "2001:db8::20" in rules
    assert "udp" not in rules
    assert verify_egress_policy(policy_path, rules_path, tmp_path) is True


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"approval": "APPROVED"}, "approval"),
        ({"target_url": "ftp://api.example.test/file"}, "HTTP or HTTPS"),
        ({"allowed_hosts": ["other.example.test"]}, "not allowed"),
        ({"policy_dir": Path("../outside")}, "escapes"),
    ],
)
def test_policy_fails_closed_for_invalid_authority_or_boundary(
    tmp_path: Path, overrides: dict, message: str
) -> None:
    if "policy_dir" in overrides:
        overrides["policy_dir"] = tmp_path / overrides["policy_dir"]
    with pytest.raises(ValueError, match=message):
        create(tmp_path, **overrides)


def test_policy_is_immutable_and_detects_rule_tampering(tmp_path: Path) -> None:
    policy_path, rules_path, _ = create(tmp_path)
    with pytest.raises(ValueError, match="immutable"):
        create(tmp_path)
    rules_path.write_text(rules_path.read_text() + "add rule inet specvora output accept\n")
    with pytest.raises(ValueError, match="hash"):
        verify_egress_policy(policy_path, rules_path, tmp_path)


def test_policy_rejects_resolution_failure(tmp_path: Path) -> None:
    def failed(host: str, port: int) -> list[tuple]:
        raise OSError("DNS unavailable")

    with pytest.raises(ValueError, match="could not be resolved"):
        create(tmp_path, resolver=failed)


def test_cli_verifies_existing_policy(tmp_path: Path, monkeypatch, capsys) -> None:
    policy_path, rules_path, _ = create(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "specvora",
            "verify-egress-policy",
            str(policy_path),
            str(rules_path),
            "--workspace-root",
            str(tmp_path),
        ],
    )
    main()
    assert json.loads(capsys.readouterr().out)["valid"] is True


def test_container_profile_applies_policy_before_dropping_privileges() -> None:
    root = Path(__file__).parents[1]
    entrypoint = (root / "deploy/egress/entrypoint.sh").read_text(encoding="utf-8")
    dockerfile = (root / "deploy/egress/Dockerfile").read_text(encoding="utf-8")
    assert entrypoint.index('nft --file "$policy"') < entrypoint.index("exec setpriv")
    assert "--no-new-privs" in entrypoint
    assert "--bounding-set=-all" in entrypoint
    assert "nftables util-linux" in dockerfile
