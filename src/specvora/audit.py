from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from specvora.confidence import ConfidenceAssessment

GENESIS_HASH = "0" * 64


def append_assessment(path: Path, assessment: ConfidenceAssessment) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    previous_hash = _last_hash(path)
    payload = assessment.model_dump(mode="json")
    record_hash = _hash_record(previous_hash, payload)
    record = {"previous_hash": previous_hash, "record_hash": record_hash, "assessment": payload}
    with path.open("a", encoding="utf-8", newline="\n") as audit_file:
        audit_file.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def verify_audit_log(path: Path) -> bool:
    previous_hash = GENESIS_HASH
    if not path.is_file():
        return True
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            if record["previous_hash"] != previous_hash:
                return False
            expected = _hash_record(previous_hash, record["assessment"])
            if record["record_hash"] != expected:
                return False
            previous_hash = record["record_hash"]
        except (KeyError, TypeError, json.JSONDecodeError):
            return False
    return True


def _last_hash(path: Path) -> str:
    if not path.is_file() or not path.stat().st_size:
        return GENESIS_HASH
    if not verify_audit_log(path):
        raise ValueError("Audit log integrity check failed")
    return json.loads(path.read_text(encoding="utf-8").splitlines()[-1])["record_hash"]


def _hash_record(previous_hash: str, payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{previous_hash}:{canonical}".encode()).hexdigest()
