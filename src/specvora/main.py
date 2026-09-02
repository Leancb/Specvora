from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from specvora.pipeline import run_analysis

app = FastAPI(title="Specvora", version="0.1.0")


class AnalyzeRequest(BaseModel):
    project_file: Path
    workspace_root: Path = Path("workspaces")


@app.get("/")
def home() -> dict[str, str]:
    return {"product": "Specvora", "status": "ready", "authority": "human"}


@app.post("/analyze")
def analyze_project(request: AnalyzeRequest) -> dict[str, object]:
    try:
        result, files = run_analysis(request.project_file, request.workspace_root)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "project_id": result.project.project_id,
        "operations": len(result.operations),
        "scenarios": len(result.scenarios),
        "artifacts": [str(path) for path in files],
    }
