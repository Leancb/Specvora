"""Legacy workflow tests explicitly select the non-production development mode."""

import pytest


@pytest.fixture(autouse=True)
def legacy_authorization_mode(request, monkeypatch):
    # Host shell configuration must not silently change a test's authentication contract.
    # Authentication-specific tests opt into required mode explicitly.
    monkeypatch.setenv("SPECVORA_PORTAL_AUTH_MODE", "local-development")
    if request.node.path.name in {
        "test_runner.py",
        "test_runner_integration.py",
        "test_playwright_runner.py",
        "test_playwright_cli.py",
        "test_portal.py",
        "test_cli.py",
    }:
        monkeypatch.setenv("SPECVORA_AUTH_MODE", "local-development")
