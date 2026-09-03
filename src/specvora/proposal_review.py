from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from specvora.ai_proposals import (
    AIProposalEnvelope,
    AIProposedScenario,
    validate_proposal_envelope,
)


class ProposalDecision(BaseModel):
    proposal_id: str = Field(pattern=r"^AI-[0-9]{3}$")
    decision: Literal["ACCEPT", "REJECT"]
    rationale: str = Field(min_length=3, max_length=500)


class HumanReviewInput(BaseModel):
    reviewer: str = Field(min_length=3, max_length=200)
    approval: str
    decisions: list[ProposalDecision] = Field(min_length=1, max_length=20)


class PromotedScenario(BaseModel):
    scenario_id: str
    source_proposal_id: str
    requirement: str
    operation_id: str
    kind: Literal["positive", "negative"]
    title: str
    rationale: str
    expected_statuses: list[int]
    reviewed_by: str


class PromotionCatalog(BaseModel):
    source_proposal_sha256: str
    review_decision_sha256: str
    authority: Literal["human-approved"] = "human-approved"
    promoted_at: datetime
    scenarios: list[PromotedScenario]


class ProposalReviewRecord(BaseModel):
    source_proposal_sha256: str
    review_decision_sha256: str
    reviewer: str
    reviewed_at: datetime
    authority: Literal["human-approved"] = "human-approved"
    status: Literal["PROMOTED", "REVIEWED_NO_PROMOTION"]
    accepted: int
    rejected: int
    decisions: list[ProposalDecision]
    promotion_catalog: str


def review_and_promote(
    project_file: Path,
    proposal_path: Path,
    decision_path: Path,
    review_record_path: Path,
    promotion_catalog_path: Path,
    workspace_root: Path,
) -> tuple[ProposalReviewRecord, PromotionCatalog]:
    proposal_file = _existing_json(proposal_path, workspace_root, "AI proposal")
    decision_file = _existing_json(decision_path, workspace_root, "review decision")
    review_target = _new_json(review_record_path, workspace_root, "review record")
    catalog_target = _new_json(promotion_catalog_path, workspace_root, "promotion catalog")
    if len({proposal_file, decision_file, review_target, catalog_target}) != 4:
        raise ValueError("Review inputs and outputs must use distinct files")

    proposal_raw = proposal_file.read_bytes()
    decision_raw = decision_file.read_bytes()
    try:
        envelope = AIProposalEnvelope.model_validate_json(proposal_raw)
        review = HumanReviewInput.model_validate_json(decision_raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Proposal or review decision does not match the required schema") from exc

    if envelope.status != "READY_FOR_HUMAN_REVIEW" or envelope.findings:
        raise ValueError("Blocked AI proposals cannot be promoted")
    if validate_proposal_envelope(envelope, project_file):
        raise ValueError("AI proposal no longer passes deterministic project policy")
    if review.approval != "APPROVED_PROPOSAL_PROMOTION":
        raise ValueError("Explicit proposal promotion approval is required")
    _validate_decisions(envelope, review)

    proposal_hash = hashlib.sha256(proposal_raw).hexdigest()
    decision_hash = hashlib.sha256(decision_raw).hexdigest()
    reviewed_at = datetime.now(UTC)
    by_id = {proposal.proposal_id: proposal for proposal in envelope.proposals}
    promoted = [
        _promoted(by_id[decision.proposal_id], review.reviewer)
        for decision in review.decisions
        if decision.decision == "ACCEPT"
    ]
    catalog = PromotionCatalog(
        source_proposal_sha256=proposal_hash,
        review_decision_sha256=decision_hash,
        promoted_at=reviewed_at,
        scenarios=promoted,
    )
    record = ProposalReviewRecord(
        source_proposal_sha256=proposal_hash,
        review_decision_sha256=decision_hash,
        reviewer=review.reviewer,
        reviewed_at=reviewed_at,
        status="PROMOTED" if promoted else "REVIEWED_NO_PROMOTION",
        accepted=len(promoted),
        rejected=len(review.decisions) - len(promoted),
        decisions=review.decisions,
        promotion_catalog=str(catalog_target),
    )
    review_target.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
    catalog_target.write_text(catalog.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return record, catalog


def _validate_decisions(envelope: AIProposalEnvelope, review: HumanReviewInput) -> None:
    proposal_ids = [proposal.proposal_id for proposal in envelope.proposals]
    decision_ids = [decision.proposal_id for decision in review.decisions]
    if len(proposal_ids) != len(set(proposal_ids)):
        raise ValueError("AI proposal envelope contains duplicate proposal IDs")
    if len(decision_ids) != len(set(decision_ids)):
        raise ValueError("Every proposal must have exactly one review decision")
    if set(decision_ids) != set(proposal_ids):
        raise ValueError("Review decisions must cover exactly every proposal")


def _promoted(proposal: AIProposedScenario, reviewer: str) -> PromotedScenario:
    return PromotedScenario(
        scenario_id=f"PROM-{proposal.proposal_id}",
        source_proposal_id=proposal.proposal_id,
        requirement=proposal.requirement,
        operation_id=proposal.operation_id,
        kind=proposal.kind,
        title=proposal.title,
        rationale=proposal.rationale,
        expected_statuses=proposal.expected_statuses,
        reviewed_by=reviewer,
    )


def _existing_json(path: Path, workspace_root: Path, label: str) -> Path:
    resolved = _confined_json(path, workspace_root, label)
    if not resolved.is_file():
        raise ValueError(f"{label} file was not found")
    return resolved


def _new_json(path: Path, workspace_root: Path, label: str) -> Path:
    resolved = _confined_json(path, workspace_root, label)
    if resolved.exists():
        raise ValueError(f"{label} already exists and is immutable")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def _confined_json(path: Path, workspace_root: Path, label: str) -> Path:
    root = workspace_root.resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{label} escapes the workspace")
    if resolved.suffix.lower() != ".json":
        raise ValueError(f"{label} must be a JSON file")
    return resolved
