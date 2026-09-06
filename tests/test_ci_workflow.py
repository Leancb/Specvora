from pathlib import Path


def test_governed_workflow_has_no_private_key_and_uses_signed_runner():
    workflow = Path(".github/workflows/governed-fixtures.yml").read_text(encoding="utf-8")
    assert "PRIVATE_KEY" not in workflow
    assert "SPECVORA_CI_SIGNED_APPROVAL_B64" in workflow
    assert "SPECVORA_ACTION_PATH_MODE: workspace-relative" in workflow
    assert "specvora run-pytest" in workflow
    assert "environment: specvora-governed" in workflow
    assert "permissions:\n  contents: write" in workflow
    assert "actions/upload-artifact@v7" in workflow
    assert "SPECVORA_APPROVAL_LEDGER_BACKEND: github-ref" in workflow
    assert "SPECVORA_GITHUB_LEDGER_REPOSITORY: ${{ github.repository }}" in workflow
    assert "SPECVORA_GITHUB_LEDGER_SHA: ${{ github.sha }}" in workflow
    assert "SPECVORA_GITHUB_LEDGER_TOKEN: ${{ github.token }}" in workflow


def test_ci_plan_is_ready_and_cannot_target_external_hosts():
    test = Path("ci/module22-plan/test_generated_api.py").read_text(encoding="utf-8")
    gate = Path("ci/module22-plan/quality-gate.json").read_text(encoding="utf-8")
    assert "READY_FOR_HUMAN_APPROVAL" in gate
    assert 'os.environ["SPECVORA_BASE_URL"]' in test
    assert "X-Specvora-Fixture" in test
    assert "trust_env=False" in test
    assert "ci/module22-plan/* text eol=lf" in Path(".gitattributes").read_text()


def test_ci_approval_scripts_use_unique_complete_unexpired_sessions():
    prepare = Path("scripts/prepare-ci-approval.ps1").read_text(encoding="utf-8")
    publish = Path("scripts/publish-ci-approval.ps1").read_text(encoding="utf-8")
    assert 'Join-Path $runtimeRoot "current-session.txt"' in prepare
    assert 'Join-Path $runtimeRoot "sessions"' in prepare
    assert 'Join-Path $runtimeRoot "current-session.txt"' in publish
    assert "Pacote da sessao esta incompleto" in publish
    assert "$expiresAt -le [DateTimeOffset]::UtcNow" in publish
    assert "$publicBytes.Length -ne 32" in publish
