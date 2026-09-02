from pathlib import Path

import pytest

from specvora.policy import (
    ExecutionRequest,
    PolicyViolation,
    build_test_command,
    validate_execution,
)


def request_for(generated: Path, **overrides: object) -> ExecutionRequest:
    values = {
        "base_url": "http://localhost:8080",
        "allowed_hosts": ["localhost"],
        "approval": "APPROVED",
        "generated_dir": generated,
    }
    values.update(overrides)
    return ExecutionRequest.model_validate(values)


def test_policy_allows_only_approved_allowlisted_confined_test(tmp_path: Path) -> None:
    generated = tmp_path / "project/generated"
    generated.mkdir(parents=True)
    test_file = generated / "test_generated_api.py"
    test_file.write_text("def test_ok(): assert True", encoding="utf-8")
    approved = validate_execution(request_for(generated), tmp_path)
    assert approved == test_file
    assert build_test_command(approved)[:4] == ["python", "-m", "pytest", str(test_file)]


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"approval": "yes"}, "human approval"),
        ({"base_url": "https://production.example.com"}, "not allowed"),
    ],
)
def test_policy_rejects_missing_approval_or_unknown_host(
    tmp_path: Path, overrides: dict[str, object], message: str
) -> None:
    generated = tmp_path / "project/generated"
    generated.mkdir(parents=True)
    (generated / "test_generated_api.py").write_text("", encoding="utf-8")
    with pytest.raises(PolicyViolation, match=message):
        validate_execution(request_for(generated, **overrides), tmp_path)


def test_policy_rejects_workspace_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)
    (outside / "test_generated_api.py").write_text("", encoding="utf-8")
    with pytest.raises(PolicyViolation, match="escapes"):
        validate_execution(request_for(outside), tmp_path)
