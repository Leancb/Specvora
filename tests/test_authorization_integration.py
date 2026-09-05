import hashlib
import json
import subprocess
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from test_playwright_runner import runner_request as browser_request
from test_portal import workspace
from test_runner import runner_request as api_request

from specvora.authorization import authorize_action, execution_action
from specvora.main import app
from specvora.playwright_runner import run_generated_playwright
from specvora.runner import run_generated_tests
from specvora.signed_approval import ApprovalClaims, sign_approval


@pytest.fixture
def trust(tmp_path, monkeypatch):
    monkeypatch.delenv("SPECVORA_AUTH_MODE", raising=False)
    key = Ed25519PrivateKey.generate()
    public = tmp_path / "public.key"
    public.write_bytes(key.public_key().public_bytes_raw())
    monkeypatch.setenv("SPECVORA_TRUSTED_PUBLIC_KEY", str(public))
    monkeypatch.setenv("SPECVORA_APPROVAL_LEDGER", str(tmp_path / "consumed.db"))
    monkeypatch.setenv("SPECVORA_APPROVER_NAME", "Human approver")
    return key


def signed(key, action, project, purpose):
    now = datetime.now(UTC)
    claims = ApprovalClaims(
        project_id=project,
        purpose=purpose,
        reviewer="Human approver",
        artifact_sha256=hashlib.sha256(action).hexdigest(),
        issued_at=now,
        expires_at=now + timedelta(minutes=30),
    )
    return sign_approval(claims, action, key, "APPROVED_SIGNING")


@pytest.mark.parametrize("kind", ["api", "browser"])
def test_executors_require_signature_and_consume_once(tmp_path, monkeypatch, trust, kind):
    request = (api_request if kind == "api" else browser_request)(tmp_path, project_id="demo")
    run = run_generated_tests if kind == "api" else run_generated_playwright
    calls = []

    def execute(command, **kwargs):
        calls.append(command)
        request.report_path.write_text('{"tests":[]}', encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout='{"suites":[]}', stderr="")

    monkeypatch.setattr(subprocess, "run", execute)
    with pytest.raises(ValueError, match="Signed approval"):
        run(request)
    assert calls == []
    envelope = signed(trust, execution_action(request, kind), "demo", f"{kind}-execution")
    request.signed_approval = envelope
    outcome = run(request)
    assert outcome.exit_code == 0
    assert outcome.approval_id == str(envelope.claims.approval_id)
    with pytest.raises(ValueError, match="already been consumed"):
        run(request)
    assert len(calls) == 1


@pytest.mark.parametrize("change", ["target", "file", "allowlist", "timeout"])
def test_execution_changes_invalidate_signature(tmp_path, monkeypatch, trust, change):
    request = api_request(tmp_path, project_id="demo")
    request.signed_approval = signed(
        trust, execution_action(request, "api"), "demo", "api-execution"
    )
    if change == "target":
        request.base_url = "http://localhost:9999"
    elif change == "allowlist":
        request.allowed_hosts.append("other.test")
    elif change == "timeout":
        request.timeout_seconds = 20
    else:
        (request.generated_dir / "test_generated_api.py").write_text("changed")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("Must not execute"))
    with pytest.raises(ValueError, match="hash mismatch"):
        run_generated_tests(request)


def test_portable_execution_action_is_stable_across_workspace_roots(tmp_path, monkeypatch):
    first = api_request(tmp_path / "windows", project_id="demo")
    second = api_request(tmp_path / "linux", project_id="demo")
    monkeypatch.setenv("SPECVORA_ACTION_PATH_MODE", "workspace-relative")
    first_action = execution_action(first, "api")
    second_action = execution_action(second, "api")
    assert first_action == second_action
    payload = json.loads(first_action)
    assert payload["version"] == "execution-v2-portable"
    assert payload["request"]["workspace_root"] == "$WORKSPACE"
    assert payload["request"]["generated_dir"] == "project/generated"
    (second.generated_dir / "test_generated_api.py").write_text("changed")
    assert execution_action(second, "api") != first_action


def test_portable_execution_rejects_invalid_mode_and_report_escape(tmp_path, monkeypatch):
    request = api_request(tmp_path, project_id="demo")
    monkeypatch.setenv("SPECVORA_ACTION_PATH_MODE", "invalid")
    with pytest.raises(ValueError, match="path mode"):
        execution_action(request, "api")
    monkeypatch.setenv("SPECVORA_ACTION_PATH_MODE", "workspace-relative")
    request.report_path = tmp_path.parent / "escaped.json"
    with pytest.raises(ValueError, match="report escapes"):
        execution_action(request, "api")


def test_portal_requires_action_signature_before_writing(tmp_path, monkeypatch, trust):
    project, proposal = workspace(tmp_path)
    monkeypatch.setenv("SPECVORA_DB_PATH", str(tmp_path / "portal.db"))
    client = TestClient(app)
    assert (
        client.post(
            "/api/projects", json={"project_file": str(project), "workspace_root": str(tmp_path)}
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/reviews",
            json={
                "review_id": "signed-001",
                "project_id": "portal-demo",
                "proposal_file": str(proposal),
            },
        ).status_code
        == 201
    )
    decision = {
        "reviewer": "Human approver",
        "approval": "APPROVED_PROPOSAL_PROMOTION",
        "decisions": [
            {"proposal_id": "AI-001", "decision": "ACCEPT", "rationale": "Reviewed case"}
        ],
    }
    url = "/api/reviews/signed-001"
    rejected = client.post(url + "/decision", json=decision)
    assert rejected.status_code == 400
    assert not (tmp_path / "portal-demo/reviews").exists()
    prepared = client.post(url + "/approval-payload", json=decision)
    assert prepared.status_code == 200
    action = prepared.json()["artifact"].encode()
    envelope = signed(trust, action, "portal-demo", "proposal-promotion")
    decision["signed_approval"] = envelope.model_dump(mode="json")
    decision["decisions"][0]["rationale"] = "Different decision"
    tampered = client.post(url + "/decision", json=decision)
    assert tampered.status_code == 400
    assert "hash mismatch" in tampered.json()["detail"]
    assert not (tmp_path / "portal-demo/reviews").exists()
    decision["decisions"][0]["rationale"] = "Reviewed case"
    result = client.post(url + "/decision", json=decision)
    assert result.status_code == 200, result.text
    assert result.json()["approval_id"] == str(envelope.claims.approval_id)
    assert client.post(url + "/decision", json=decision).status_code == 400


def test_configuration_and_identity_fail_closed(monkeypatch, trust):
    envelope = signed(trust, b"action", "demo", "api-execution")
    with pytest.raises(ValueError, match="identity"):
        authorize_action(envelope, b"action", "demo", "api-execution", "Someone else")
    monkeypatch.delenv("SPECVORA_APPROVAL_LEDGER")
    with pytest.raises(ValueError, match="incomplete"):
        authorize_action(envelope, b"action", "demo", "api-execution")
    monkeypatch.setenv("SPECVORA_AUTH_MODE", "typo")
    with pytest.raises(ValueError, match="Invalid"):
        authorize_action(None, b"action", "demo", "api-execution")


def test_prepare_execution_cli_matches_runtime(tmp_path, monkeypatch, capsys):
    import sys

    from specvora.governance_cli import main

    request = api_request(tmp_path, project_id="demo")
    source, target = tmp_path / "request.json", tmp_path / "action.json"
    source.write_text(request.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "governance",
            "--workspace-root",
            str(tmp_path),
            "prepare-execution",
            str(source),
            "--kind",
            "api",
            "--output",
            str(target),
        ],
    )
    main()
    assert json.loads(capsys.readouterr().out)["output"] == str(target.resolve())
    assert target.read_bytes() == execution_action(request, "api")
