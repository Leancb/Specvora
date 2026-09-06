from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from pydantic import BaseModel, Field

from specvora.ai_proposals import AIProposalEnvelope, validate_proposal_envelope
from specvora.authorization import authorize_action, canonical_action
from specvora.data_cases import generate_request_cases
from specvora.models import ProjectInput
from specvora.openapi import extract_operations, load_openapi
from specvora.promoted_generation import CaseBinding, GenerationBindings, generate_promoted
from specvora.proposal_review import HumanReviewInput, review_and_promote
from specvora.repository import ProjectRepository
from specvora.schema_resolver import resolve_document
from specvora.signed_approval import SignedApproval


class SignedReviewDecision(HumanReviewInput):
    signed_approval: SignedApproval | None = None


class ProjectRegistration(BaseModel):
    project_file: Path
    workspace_root: Path


class ReviewRegistration(BaseModel):
    review_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")
    project_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,62}$")
    proposal_file: Path


class PortalGenerationRequest(BaseModel):
    plan_id: str = Field(pattern=r"^plan-[a-z0-9][a-z0-9-]{0,55}$")
    bindings: list[CaseBinding]


def repository() -> ProjectRepository:
    return ProjectRepository(Path(os.getenv("SPECVORA_DB_PATH", "workspaces/specvora.db")))


def register_project(request: ProjectRegistration) -> dict:
    project_file = _confined_file(request.project_file, request.workspace_root, "project")
    project = ProjectInput.model_validate_json(project_file.read_bytes())
    specification = (project_file.parent / project.openapi_path).resolve()
    workspace = request.workspace_root.resolve()
    if not specification.is_relative_to(workspace) or not specification.is_file():
        raise ValueError("Portal OpenAPI file must exist inside the workspace")
    return repository().add_project(project.project_id, project_file, workspace)


def register_review(request: ReviewRegistration) -> dict:
    project = repository().get_project(request.project_id)
    workspace = Path(project["workspace_root"])
    proposal_file = _confined_file(request.proposal_file, workspace, "proposal")
    envelope = AIProposalEnvelope.model_validate_json(proposal_file.read_bytes())
    if envelope.status != "READY_FOR_HUMAN_REVIEW" or envelope.findings:
        raise ValueError("Only policy-ready AI proposals can enter the review queue")
    if validate_proposal_envelope(envelope, Path(project["project_file"])):
        raise ValueError("AI proposal does not pass deterministic project policy")
    digest = hashlib.sha256(proposal_file.read_bytes()).hexdigest()
    return repository().add_review(request.review_id, request.project_id, proposal_file, digest)


def review_action(review_id: str, decision: HumanReviewInput) -> bytes:
    store = repository()
    item = store.get_review(review_id)
    project = store.get_project(item["project_id"])
    workspace = Path(project["workspace_root"])
    source = _confined_file(Path(project["project_file"]), workspace, "project")
    parsed = ProjectInput.model_validate_json(source.read_bytes())
    specification = (source.parent / parsed.openapi_path).resolve()
    if not specification.is_relative_to(workspace.resolve()) or not specification.is_file():
        raise ValueError("Portal OpenAPI file must exist inside the workspace")
    proposal = _confined_file(Path(item["proposal_file"]), workspace, "proposal")
    proposal_hash = hashlib.sha256(proposal.read_bytes()).hexdigest()
    if proposal_hash != item["proposal_sha256"] or parsed.project_id != item["project_id"]:
        raise ValueError("Queued project or proposal changed")
    return canonical_action(
        {
            "version": "review-action-v1",
            "review_id": review_id,
            "project_id": item["project_id"],
            "proposal_sha256": proposal_hash,
            "project_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "openapi_sha256": hashlib.sha256(specification.read_bytes()).hexdigest(),
            "decision": decision.model_dump(mode="json", exclude={"signed_approval"}),
        }
    )


def decide_review(review_id: str, decision: SignedReviewDecision) -> dict:
    store = repository()
    item = store.get_review(review_id)
    if item["status"] != "PENDING":
        raise ValueError("Review is no longer pending")
    project = store.get_project(item["project_id"])
    workspace = Path(project["workspace_root"])
    review_dir = workspace / item["project_id"] / "reviews"
    promotion_dir = workspace / item["project_id"] / "promoted"
    decision_path = review_dir / f"{review_id}-decision.json"
    record_path = review_dir / f"{review_id}-record.json"
    catalog_path = promotion_dir / f"{review_id}-catalog.json"
    for output in (decision_path, record_path, catalog_path):
        if not output.resolve().is_relative_to(workspace.resolve()):
            raise ValueError("Portal output escapes the workspace")
    if decision_path.exists():
        raise ValueError("Review decision artifact already exists")
    action = review_action(review_id, decision)
    approval_id = authorize_action(
        decision.signed_approval,
        action,
        item["project_id"],
        "proposal-promotion",
        decision.reviewer,
    )
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    with decision_path.open("x", encoding="utf-8") as stream:
        stream.write(decision.model_dump_json(indent=2) + "\n")
    try:
        record, catalog = review_and_promote(
            Path(project["project_file"]),
            Path(item["proposal_file"]),
            decision_path,
            record_path,
            catalog_path,
            workspace,
        )
    except Exception:
        decision_path.unlink(missing_ok=True)
        raise
    persisted = store.complete_review(review_id, record_path, catalog_path)
    return {
        "approval_id": approval_id,
        "review": persisted,
        "decision": record.model_dump(mode="json"),
        "promotion": catalog.model_dump(mode="json"),
    }


def review_detail(review_id: str) -> dict:
    item = repository().get_review(review_id)
    envelope = AIProposalEnvelope.model_validate_json(Path(item["proposal_file"]).read_bytes())
    return {"review": item, "proposal": envelope.model_dump(mode="json")}


def generation_detail(review_id: str) -> dict:
    item = repository().get_review(review_id)
    if item["status"] != "REVIEWED" or not item["promotion_catalog"]:
        raise ValueError("Only reviewed promotions can generate tests")
    project = repository().get_project(item["project_id"])
    workspace = Path(project["workspace_root"]).resolve()
    project_file = _confined_file(Path(project["project_file"]), workspace, "project")
    parsed = ProjectInput.model_validate_json(project_file.read_bytes())
    specification = (project_file.parent / parsed.openapi_path).resolve()
    if not specification.is_relative_to(workspace) or not specification.is_file():
        raise ValueError("Portal OpenAPI file must exist inside the workspace")
    document = resolve_document(load_openapi(specification))
    cases = {
        operation.operation_id: [
            case.model_dump(mode="json") for case in generate_request_cases(operation)
        ]
        for operation in extract_operations(document)
    }
    catalog = Path(item["promotion_catalog"])
    catalog_data = json.loads(_confined_file(catalog, workspace, "catalog").read_text())
    plan_root = workspace / "workspaces" / item["project_id"] / "promoted-generated"
    plans = sorted(path.name for path in plan_root.glob("plan-*") if path.is_dir())
    return {
        "review_id": review_id,
        "scenarios": catalog_data["scenarios"],
        "cases": cases,
        "plans": plans,
    }


def generate_review_plan(review_id: str, request: PortalGenerationRequest) -> dict:
    store = repository()
    item = store.get_review(review_id)
    if item["status"] != "REVIEWED" or not item["review_record"] or not item["promotion_catalog"]:
        raise ValueError("Only reviewed promotions can generate tests")
    project = store.get_project(item["project_id"])
    workspace = Path(project["workspace_root"]).resolve()
    project_workspace = workspace / "workspaces" / item["project_id"]
    output = project_workspace / "promoted-generated" / request.plan_id
    binding_dir = project_workspace / "bindings"
    binding_file = binding_dir / f"{request.plan_id}.json"
    if output.exists() or binding_file.exists():
        raise ValueError("Plan ID already exists; choose a new plan ID")
    for path in (output, binding_file):
        if not path.resolve().is_relative_to(workspace):
            raise ValueError("Portal generation output escapes the workspace")
    binding_dir.mkdir(parents=True, exist_ok=True)
    try:
        with binding_file.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(
                GenerationBindings(bindings=request.bindings).model_dump_json(indent=2) + "\n"
            )
        return generate_promoted(
            Path(project["project_file"]),
            Path(item["proposal_file"]),
            workspace / item["project_id"] / "reviews" / f"{review_id}-decision.json",
            Path(item["review_record"]),
            Path(item["promotion_catalog"]),
            binding_file,
            output,
            workspace,
        )
    except Exception:
        if not output.exists():
            binding_file.unlink(missing_ok=True)
        raise


def portal_html() -> str:
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Specvora Review Portal</title><style>
body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 20px;color:#17202a}
h1{margin-bottom:4px}.notice{background:#fff4ce;padding:12px;border-left:4px solid #b7791f}
table{width:100%;border-collapse:collapse;margin-top:24px}
th,td{padding:10px;border-bottom:1px solid #ddd;text-align:left}
.PENDING{color:#9c5700}.REVIEWED{color:#217346}code{font-size:13px}
input{display:block;margin:8px 0;padding:8px;min-width:280px}</style></head><body>
<h1>Specvora human review</h1><p>AI proposes. Policies validate. People authorize.</p>
<p class="notice">Local training portal. Enable required authentication before network exposure.</p>
<p>Signed approvals are required by default. Private keys must remain offline.</p>
<section id="login" hidden><h2>Sign in</h2><input id="username" autocomplete="username"
 placeholder="Username"><input id="password" type="password" autocomplete="current-password"
 placeholder="Password"><input id="totp" inputmode="numeric" autocomplete="one-time-code"
 placeholder="MFA code (if enabled)"><button onclick="loginPortal()">Sign in</button></section>
<div id="portal-content" hidden><p id="identity"></p>
<button onclick="logoutPortal()">Sign out</button>
<h2>Projects</h2><table id="projects"><tbody></tbody></table>
<h2>Review queue</h2><table id="reviews"><tbody></tbody></table>
</div>
<script>
let csrf='';
async function api(url,options={}){
 const method=(options.method||'GET').toUpperCase();options.headers=options.headers||{};
 if(!['GET','HEAD'].includes(method))options.headers['X-Specvora-CSRF']=csrf;
 return fetch(url,options);
}
async function load(){
 const session=await fetch('/api/session');
 if(!session.ok){document.getElementById('login').hidden=false;return;}
 const who=await session.json();csrf=who.csrf_token;
 document.getElementById('identity').innerText=
  `Signed in: ${who.display_name} (${who.roles.join(', ')})`;
 document.getElementById('portal-content').hidden=false;
 const [p,r]=await Promise.all([fetch('/api/projects'),fetch('/api/reviews')]);
 for(const x of await p.json()) projects.tBodies[0].insertRow().innerText=x.project_id;
 for(const x of await r.json()){
  const row=reviews.tBodies[0].insertRow();
  row.insertCell().innerText=`${x.review_id} | ${x.project_id} | ${x.status}`;
  if(x.status==='PENDING'){
   const button=document.createElement('button');button.innerText='Review proposals';
   button.onclick=()=>decide(x.review_id);row.insertCell().appendChild(button);
  }else{const button=document.createElement('button');button.innerText='Generate test plan';
   button.onclick=()=>generatePlan(x.review_id);row.insertCell().appendChild(button);}
  row.className=x.status;
 }
}
async function loginPortal(){
 const response=await fetch('/api/session',{method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({username:document.getElementById('username').value,
   password:document.getElementById('password').value,
   totp_code:document.getElementById('totp').value||null})});
 if(!response.ok)return alert((await response.json()).detail);location.reload();
}
async function logoutPortal(){
 const response=await api('/api/session',{method:'DELETE'});
 if(!response.ok)return alert((await response.json()).detail);location.reload();
}
async function decide(id){
 const detail=await (await fetch(`/api/reviews/${id}`)).json();
 const reviewer=prompt('Reviewer full name');if(!reviewer)return;
 const decisions=[];
 for(const proposal of detail.proposal.proposals){
  const choice=prompt(`${proposal.title}: type ACCEPT or REJECT`);
  if(!['ACCEPT','REJECT'].includes(choice))return alert('Decision cancelled.');
  const rationale=prompt('Explain this decision');if(!rationale)return;
  decisions.push({proposal_id:proposal.proposal_id,decision:choice,rationale});
 }
 if(!confirm('Record this human decision? This action is immutable.'))return;
 const decision={reviewer,approval:'APPROVED_PROPOSAL_PROMOTION',decisions};
 const preview=await api(`/api/reviews/${id}/approval-payload`,{method:'POST',
  headers:{'Content-Type':'application/json'},body:JSON.stringify(decision)});
 if(!preview.ok)return alert((await preview.json()).detail);
 const payload=await preview.json();
 const link=document.createElement('a');
 link.href=URL.createObjectURL(new Blob([payload.artifact],{type:'application/json'}));
 link.download='review-action.json';link.click();URL.revokeObjectURL(link.href);
 const signed=prompt('Sign the downloaded action offline, then paste the signed envelope JSON.'+
  ' Cancel to stop. Empty is accepted only in operator-configured local-development mode.');
 if(signed===null)return;
 try{if(signed.trim())decision.signed_approval=JSON.parse(signed);}catch{
  return alert('Invalid signed envelope JSON');}
 const response=await api(`/api/reviews/${id}/decision`,{method:'POST',headers:{
  'Content-Type':'application/json'},body:JSON.stringify(decision)});
 if(!response.ok)return alert((await response.json()).detail);
 location.reload();
}
async function generatePlan(id){
 const detailResponse=await fetch(`/api/reviews/${id}/generation`);
 if(!detailResponse.ok)return alert((await detailResponse.json()).detail);
 const detail=await detailResponse.json();
 const suggested=`plan-portal-${String(detail.plans.length+1).padStart(3,'0')}`;
 const plan_id=prompt('New plan ID (existing plans are never overwritten)',suggested);
 if(!plan_id)return;
 const bindings=[];
 for(const scenario of detail.scenarios){
  const choices=detail.cases[scenario.operation_id]||[];
  const caseList=choices.map(x=>x.case_id).join('\\n');
  const case_id=prompt(`${scenario.title}\nChoose one case ID:\n${caseList}`);
  if(!case_id)return alert('Generation cancelled.');
  bindings.push({scenario_id:scenario.scenario_id,case_id});
 }
 if(!confirm('Generate artifacts only? No tests will execute.'))return;
 const response=await api(`/api/reviews/${id}/generation`,{method:'POST',headers:{
  'Content-Type':'application/json'},body:JSON.stringify({plan_id,bindings})});
 const result=await response.json();if(!response.ok)return alert(result.detail);
 alert(`Plan ${result.status}: ${result.output_dir}\nTests generated: ${result.tests_generated}`);
 location.reload();
}
load();
</script>
</body></html>"""


def _confined_file(path: Path, workspace_root: Path, label: str) -> Path:
    root = workspace_root.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"Portal {label} escapes the workspace")
    if not resolved.is_file() or resolved.suffix.lower() != ".json":
        raise ValueError(f"Portal {label} must be an existing JSON file")
    return resolved
