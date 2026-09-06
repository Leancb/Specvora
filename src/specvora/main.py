import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from specvora.audit import append_assessment
from specvora.confidence import ConfidenceAssessment, TestRunResult, assess_release
from specvora.pipeline import run_analysis
from specvora.portal import (
    PortalGenerationRequest,
    ProjectRegistration,
    ReviewRegistration,
    SignedReviewDecision,
    decide_review,
    generate_review_plan,
    generation_detail,
    portal_html,
    register_project,
    register_review,
    repository,
    review_action,
    review_detail,
)
from specvora.portal_auth import (
    Capability,
    SessionIdentity,
    authenticate,
    issue_session,
    portal_auth_mode,
    require_capability,
    verify_session,
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


class PortalLoginRequest(BaseModel):
    username: str
    password: str


SESSION_COOKIE = "specvora_session"


def _portal_identity(request: Request) -> SessionIdentity:
    if portal_auth_mode() == "local-development":
        return SessionIdentity(
            username="local-development",
            display_name="Local development operator",
            roles=["reviewer", "operator"],
            csrf_token="local-development",
            expires_at=datetime.now(UTC),
        )
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Portal authentication is required")
    try:
        return verify_session(token)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _authorized(request: Request, capability: Capability, *, csrf: bool) -> SessionIdentity:
    identity = _portal_identity(request)
    try:
        require_capability(identity, capability)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if csrf and portal_auth_mode() == "required":
        supplied = request.headers.get("X-Specvora-CSRF", "")
        if not supplied or supplied != identity.csrf_token:
            raise HTTPException(status_code=403, detail="Portal CSRF token is missing or invalid")
    return identity


def portal_reader(request: Request) -> SessionIdentity:
    return _authorized(request, "read", csrf=False)


def portal_reviewer(request: Request) -> SessionIdentity:
    return _authorized(request, "review", csrf=True)


def portal_authenticated_writer(request: Request) -> SessionIdentity:
    return _authorized(request, "read", csrf=True)


def portal_operator(request: Request) -> SessionIdentity:
    return _authorized(request, "manage", csrf=True)


PortalReader = Annotated[SessionIdentity, Depends(portal_reader)]
PortalReviewer = Annotated[SessionIdentity, Depends(portal_reviewer)]
PortalOperator = Annotated[SessionIdentity, Depends(portal_operator)]
PortalAuthenticatedWriter = Annotated[
    SessionIdentity, Depends(portal_authenticated_writer)
]


@app.get("/")
def home() -> dict[str, str]:
    return {"product": "Specvora", "status": "ready", "authority": "human"}


@app.get("/portal", response_class=HTMLResponse)
def review_portal() -> str:
    return portal_html()


@app.post("/api/session")
def login_portal(request: PortalLoginRequest, response: Response) -> dict:
    if portal_auth_mode() != "required":
        raise HTTPException(status_code=400, detail="Portal authentication is not enabled")
    try:
        token, identity = issue_session(authenticate(request.username, request.password))
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=401, detail="Invalid portal credentials") from exc
    secure = os.getenv("SPECVORA_PORTAL_COOKIE_SECURE", "true").lower() == "true"
    max_age = max(0, int((identity.expires_at - datetime.now(UTC)).total_seconds()))
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=max_age,
        httponly=True,
        secure=secure,
        samesite="strict",
        path="/",
    )
    return identity.model_dump(mode="json")


@app.get("/api/session")
def get_portal_session(identity: PortalReader) -> dict:
    return identity.model_dump(mode="json")


@app.delete("/api/session", status_code=204)
def logout_portal(response: Response, _identity: PortalAuthenticatedWriter) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


@app.get("/api/projects")
def list_projects(_identity: PortalReader) -> list[dict]:
    return repository().list_projects()


@app.post("/api/projects", status_code=201)
def create_project(
    request: ProjectRegistration, _identity: PortalOperator
) -> dict:
    try:
        return register_project(request)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/reviews")
def list_reviews(
    _identity: PortalReader, status: str | None = None
) -> list[dict]:
    try:
        return repository().list_reviews(status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/reviews", status_code=201)
def create_review(
    request: ReviewRegistration, _identity: PortalOperator
) -> dict:
    try:
        return register_review(request)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/reviews/{review_id}")
def get_review(review_id: str, _identity: PortalReader) -> dict:
    try:
        return review_detail(review_id)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/reviews/{review_id}/generation")
def get_review_generation(
    review_id: str, _identity: PortalReader
) -> dict:
    try:
        return generation_detail(review_id)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/reviews/{review_id}/generation", status_code=201)
def create_review_generation(
    review_id: str,
    request: PortalGenerationRequest,
    _identity: PortalOperator,
) -> dict:
    try:
        return generate_review_plan(review_id, request)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/reviews/{review_id}/decision")
def submit_review(
    review_id: str,
    decision: SignedReviewDecision,
    identity: PortalReviewer,
) -> dict:
    try:
        if portal_auth_mode() == "required" and decision.reviewer != identity.display_name:
            raise ValueError("Decision reviewer differs from the authenticated identity")
        return decide_review(review_id, decision)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/reviews/{review_id}/approval-payload")
def prepare_review_approval(
    review_id: str,
    decision: HumanReviewInput,
    identity: PortalReviewer,
) -> dict:
    try:
        if portal_auth_mode() == "required" and decision.reviewer != identity.display_name:
            raise ValueError("Decision reviewer differs from the authenticated identity")
        payload = review_action(review_id, decision)
        return {"artifact": payload.decode(), "sha256": hashlib.sha256(payload).hexdigest()}
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/analyze")
def analyze_project(request: AnalyzeRequest, _identity: PortalOperator) -> dict[str, object]:
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
def assess_results(request: AssessRequest, _identity: PortalOperator) -> ConfidenceAssessment:
    try:
        assessment = assess_release(request.result)
        append_assessment(request.audit_log, assessment)
        return assessment
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ingest/pytest", response_model=PytestEvidence)
def ingest_pytest(request: PytestIngestRequest, _identity: PortalReader) -> PytestEvidence:
    try:
        return ingest_pytest_report(request)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
