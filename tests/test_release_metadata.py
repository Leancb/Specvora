import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_release_version_is_consistent():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs/RELEASE_CHECKLIST.md").read_text(encoding="utf-8")
    assert project["version"] == "0.1.0"
    assert "## 0.1.0" in changelog
    assert "v0.1.0" in checklist


def test_quality_workflow_is_read_only_and_covers_release_checks():
    workflow = (ROOT / ".github/workflows/quality.yml").read_text(encoding="utf-8")
    assert "contents: read" in workflow
    assert "pull_request:" in workflow
    assert "python -m ruff check src tests" in workflow
    assert "python -m pytest -q" in workflow
    assert "python -m pip wheel . --no-deps" in workflow
    assert "secrets." not in workflow
