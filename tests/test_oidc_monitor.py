import json
from datetime import UTC, datetime

from test_oidc_trust import jwk, transport_for
from test_oidc_trust_approval import apply, approve, proposal

from specvora.oidc_monitor import monitor_oidc_trust


def governed_trust(tmp_path, key):
    proposed, trust = proposal(tmp_path, key=key)
    approval, public, now = approve(tmp_path, proposed)
    apply(tmp_path, proposed, trust, approval, public, now)
    return trust, tmp_path / "audit/oidc-trust.jsonl"


def monitor(tmp_path, trust, audit, keys, *, transport=None):
    return monitor_oidc_trust(
        "https://identity.example/tenant/.well-known/openid-configuration",
        "https://identity.example/tenant", {"identity.example", "keys.example"},
        trust, audit, tmp_path, now=datetime(2026, 9, 7, 2, tzinfo=UTC),
        transport=transport or transport_for(keys),
    )


def test_monitor_reports_healthy_without_writing(tmp_path):
    first = jwk("key-a")
    trust, audit = governed_trust(tmp_path, first)
    before = {path: path.read_bytes() for path in (trust, audit)}
    report = monitor(tmp_path, trust, audit, [first])
    assert report.status == "HEALTHY"
    assert report.findings == []
    assert report.current_jwks_sha256 == report.discovered_jwks_sha256
    assert {path: path.read_bytes() for path in (trust, audit)} == before


def test_monitor_requests_review_for_overlapping_change(tmp_path):
    first = jwk("key-a")
    trust, audit = governed_trust(tmp_path, first)
    report = monitor(tmp_path, trust, audit, [first, jwk("key-b")])
    assert report.status == "REVIEW_REQUIRED"
    assert report.findings == ["PROVIDER_KEYS_CHANGED"]
    assert report.current_key_ids == ["key-a"]
    assert report.discovered_key_ids == ["key-a", "key-b"]


def test_monitor_blocks_trust_discontinuity(tmp_path):
    trust, audit = governed_trust(tmp_path, jwk("key-a"))
    report = monitor(tmp_path, trust, audit, [jwk("key-b")])
    assert report.status == "BLOCKED"
    assert report.findings == ["TRUST_DISCONTINUITY"]


def test_monitor_blocks_tampered_or_missing_audit_without_discovery(tmp_path):
    first = jwk("key-a")
    trust, audit = governed_trust(tmp_path, first)
    audit.write_text(audit.read_text().replace("Operations User", "Intruder"), encoding="utf-8")
    report = monitor(tmp_path, trust, audit, [first])
    assert report.status == "BLOCKED"
    assert report.findings == ["AUDIT_INVALID"]
    audit.unlink()
    assert monitor(tmp_path, trust, audit, [first]).findings == ["AUDIT_INVALID"]


def test_monitor_blocks_out_of_band_valid_trust_change(tmp_path):
    first = jwk("key-a")
    trust, audit = governed_trust(tmp_path, first)
    trust.write_text(json.dumps({"keys": [first, jwk("key-b")]}), encoding="utf-8")
    report = monitor(tmp_path, trust, audit, [first])
    assert report.status == "BLOCKED"
    assert report.findings == ["TRUST_AUDIT_MISMATCH"]


def test_monitor_classifies_discovery_failure_without_remote_details(tmp_path):
    first = jwk("key-a")
    trust, audit = governed_trust(tmp_path, first)
    report = monitor(
        tmp_path, trust, audit, [],
        transport=transport_for([], issuer="https://evil.example/secret"),
    )
    assert report.status == "BLOCKED"
    assert report.findings == ["DISCOVERY_UNAVAILABLE"]
    assert "evil" not in report.model_dump_json()
