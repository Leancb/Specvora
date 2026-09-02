import json
from pathlib import Path

from specvora.analyzer import analyze
from specvora.generator import generate_artifacts
from specvora.models import AnalysisResult, ProjectInput
from specvora.openapi import extract_operations, load_openapi


def run_analysis(
    project_file: Path, workspace_root: Path | None = None
) -> tuple[AnalysisResult, list[Path]]:
    project_file = project_file.resolve()
    project = ProjectInput.model_validate(json.loads(project_file.read_text(encoding="utf-8")))
    result = analyze(
        project,
        extract_operations(load_openapi((project_file.parent / project.openapi_path).resolve())),
    )
    output = (workspace_root or Path("workspaces")).resolve() / project.project_id / "generated"
    return result, generate_artifacts(result, output)
