from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from specvora.audit import append_assessment
from specvora.confidence import ConfidenceAssessment, TestRunResult, assess_release
from specvora.pipeline import run_analysis
from specvora.portal import (
    ProjectRegistration,
    ReviewRegistration,
    decide_review,
    portal_html,
    register_project,
    register_review,
    repository,
    review_detail,
)
from specvora.proposal_review import HumanReviewInput
from specvora.pytest_ingest import PytestEvidence, PytestIngestRequest, ingest_pytest_report

app = FastAPI(title="Specvora", version="0.1.0")


class AnalyzeRequest(BaseModel):
    project_file: Path
    workspace_root: Path = Path("workspaces")


class AssessRequest(BaseModel):
    result: TestRunResult
    audit_log: Path


@app.get("/")
def home() -> dict[str, str]:
    return {"product": "Specvora", "status": "ready", "authority": "human"}


@app.get("/portal", response_class=HTMLResponse)
def review_portal() -> str:
    return portal_html()


@app.get("/api/projects")
def list_projects() -> list[dict]:
    return repository().list_projects()


@app.post("/api/projects", status_code=201)
def create_project(request: ProjectRegistration) -> dict:
    try:
        return register_project(request)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/reviews")
def list_reviews(status: str | None = None) -> list[dict]:
    try:
        return repository().list_reviews(status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/reviews", status_code=201)
def create_review(request: ReviewRegistration) -> dict:
    try:
        return register_review(request)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/reviews/{review_id}")
def get_review(review_id: str) -> dict:
    try:
        return review_detail(review_id)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/reviews/{review_id}/decision")
def submit_review(review_id: str, decision: HumanReviewInput) -> dict:
    try:
        return decide_review(review_id, decision)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@app.post("/assess", response_model=ConfidenceAssessment)
def assess_results(request: AssessRequest) -> ConfidenceAssessment:
    try:
        assessment = assess_release(request.result)
        append_assessment(request.audit_log, assessment)
        return assessment
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ingest/pytest", response_model=PytestEvidence)
def ingest_pytest(request: PytestIngestRequest) -> PytestEvidence:
    try:
        return ingest_pytest_report(request)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
