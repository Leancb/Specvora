import json
from pathlib import Path

from specvora.pipeline import run_analysis


def write_project(tmp_path: Path, steps: list[dict[str, str]]) -> Path:
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "Web", "version": "1"},
        "paths": {"/health": {"get": {"responses": {"200": {"description": "ok"}}}}},
    }
    (tmp_path / "openapi.json").write_text(json.dumps(spec), encoding="utf-8")
    payload = {
        "project_id": "web-demo",
        "requirements": ["Sign in"],
        "openapi_path": "openapi.json",
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
        "web_base_url": "http://localhost:3000",
        "web_journeys": [{"journey_id": "sign-in", "title": "Sign in", "steps": steps}],
    }
    path = tmp_path / "project.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_pipeline_generates_playwright_and_includes_it_in_ready_gate(tmp_path: Path) -> None:
    _, files = run_analysis(
        write_project(
            tmp_path,
            [{"action": "goto", "path": "/login"}, {"action": "assert_visible", "selector": "h1"}],
        ),
        tmp_path / "workspaces",
    )
    assert {path.name for path in files if path.parent.name == "playwright"} == {
        "playwright-plan.json",
        "playwright.config.ts",
        "test_generated_web.spec.ts",
        "package.json",
    }
    generated = tmp_path / "workspaces/web-demo/generated"
    gate = json.loads((generated / "quality-gate.json").read_text())
    assert gate["status"] == "READY_FOR_HUMAN_APPROVAL"
    assert gate["operations_checked"] == 2


def test_pipeline_blocks_journey_without_initial_goto(tmp_path: Path) -> None:
    run_analysis(
        write_project(tmp_path, [{"action": "click", "selector": "text=Start"}]),
        tmp_path / "workspaces",
    )
    gate = json.loads((tmp_path / "workspaces/web-demo/generated/quality-gate.json").read_text())
    assert gate["status"] == "BLOCKED"
    assert gate["blocking_codes"] == ["INVALID_JOURNEY"]
