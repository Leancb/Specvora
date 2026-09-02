from pathlib import Path

import pytest
from pydantic import ValidationError

from specvora.models import ProjectInput
from specvora.playwright import generate_playwright_artifacts, validate_web_journeys


def project(steps: list[dict[str, str]], **overrides: object) -> ProjectInput:
    values = {
        "project_id": "web-demo",
        "requirements": ["A user can sign in"],
        "openapi_path": "openapi.yaml",
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
        "web_base_url": "http://localhost:3000",
        "web_journeys": [{"journey_id": "sign-in", "title": "User signs in", "steps": steps}],
    }
    values.update(overrides)
    return ProjectInput.model_validate(values)


def test_generates_escaped_reviewable_playwright_project(tmp_path: Path) -> None:
    target = project(
        [
            {"action": "goto", "path": "/login"},
            {"action": "fill", "selector": "[name=email]", "value": 'qa"@example.com'},
            {"action": "click", "selector": "button[type=submit]"},
            {"action": "assert_visible", "selector": "text=Welcome"},
        ]
    )
    files = generate_playwright_artifacts(target, tmp_path)
    assert {path.name for path in files} == {
        "playwright-plan.json",
        "playwright.config.ts",
        "test_generated_web.spec.ts",
        "package.json",
    }
    generated = (tmp_path / "playwright/test_generated_web.spec.ts").read_text()
    assert "Human review and approval are required" in generated
    assert 'qa\\"@example.com' in generated
    assert "eval(" not in generated
    assert validate_web_journeys(target)[0].valid


def test_journey_without_initial_navigation_blocks_generation_gate() -> None:
    target = project([{"action": "click", "selector": "text=Start"}])
    validation = validate_web_journeys(target)[0]
    assert not validation.valid
    assert validation.findings[0].code == "INVALID_JOURNEY"


def test_rejects_unallowlisted_or_protocol_relative_web_targets() -> None:
    with pytest.raises(ValidationError, match="explicitly allowlisted"):
        project([{"action": "goto", "path": "/"}], web_base_url="https://example.com")
    with pytest.raises(ValidationError, match="protocol-relative"):
        project([{"action": "goto", "path": "//evil.example"}])


def test_requires_web_url_and_journeys_together() -> None:
    with pytest.raises(ValidationError, match="provided together"):
        project([], web_journeys=[])
