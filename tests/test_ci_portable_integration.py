import hashlib
import shutil
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta

import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from specvora.authorization import execution_action
from specvora.runner import RunnerRequest, run_generated_tests
from specvora.signed_approval import ApprovalClaims, sign_approval


def test_portable_signed_runner_executes_real_loopback_fixtures(tmp_path, monkeypatch):
    generated = tmp_path / "ci/module22-plan"
    shutil.copytree("ci/module22-plan", generated)
    report = tmp_path / "ci/evidence/report.json"
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    request = RunnerRequest(
        project_id="petstore-demo",
        workspace_root=tmp_path,
        generated_dir=generated,
        report_path=report,
        base_url=f"http://127.0.0.1:{port}",
        allowed_hosts=["127.0.0.1"],
        approval="APPROVED",
        timeout_seconds=30,
    )
    key = Ed25519PrivateKey.generate()
    public = tmp_path / "public.key"
    public.write_bytes(key.public_key().public_bytes_raw())
    monkeypatch.setenv("SPECVORA_ACTION_PATH_MODE", "workspace-relative")
    monkeypatch.setenv("SPECVORA_AUTH_MODE", "signed")
    monkeypatch.setenv("SPECVORA_TRUSTED_PUBLIC_KEY", str(public))
    monkeypatch.setenv("SPECVORA_APPROVER_NAME", "CI reviewer")
    monkeypatch.setenv("SPECVORA_APPROVAL_LEDGER", str(tmp_path / "ledger.sqlite"))
    action = execution_action(request, "api")
    now = datetime.now(UTC)
    request.signed_approval = sign_approval(
        ApprovalClaims(
            project_id="petstore-demo",
            purpose="api-execution",
            reviewer="CI reviewer",
            artifact_sha256=hashlib.sha256(action).hexdigest(),
            issued_at=now,
            expires_at=now + timedelta(minutes=5),
        ),
        action,
        key,
        "APPROVED_SIGNING",
    )
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "specvora.fixture_app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):
            try:
                if (
                    httpx.get(
                        f"http://127.0.0.1:{port}/pets/preflight", trust_env=False
                    ).status_code
                    == 200
                ):
                    break
            except httpx.TransportError:
                time.sleep(0.1)
        else:
            raise AssertionError("Fixture target did not start")
        outcome = run_generated_tests(request)
        assert outcome.exit_code == 0
        assert report.is_file()
        assert "2 passed" in outcome.stdout
    finally:
        server.terminate()
        server.wait(timeout=5)
