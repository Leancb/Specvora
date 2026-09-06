"""Central portal-state service. Deploy only behind authenticated TLS."""

from __future__ import annotations

import hmac
import os
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from pydantic import BaseModel, Field

from specvora.portal_session_store import PortalSessionStore

app = FastAPI(title="Specvora Portal State Service", version="0.1.0", docs_url=None)
_stores: dict[str, PortalSessionStore] = {}
_stores_lock = Lock()


class MfaClaim(BaseModel):
    username: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,63}$")
    counter: int = Field(ge=0)


class SessionRegistration(BaseModel):
    session_id: str = Field(min_length=16, max_length=200)
    username: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,63}$")
    expires_at: datetime


def _authorize(authorization: Annotated[str | None, Header()] = None) -> None:
    token = os.getenv("SPECVORA_STATE_SERVICE_TOKEN", "")
    if len(token) < 32 or not authorization or not hmac.compare_digest(
        authorization, f"Bearer {token}"
    ):
        raise HTTPException(status_code=401, detail="State service authentication failed")


def _store_for_path(path: str) -> PortalSessionStore:
    with _stores_lock:
        store = _stores.get(path)
        if store is None:
            store = PortalSessionStore(Path(path))
            _stores[path] = store
        return store


def _store() -> PortalSessionStore:
    path = os.getenv("SPECVORA_STATE_SERVICE_DB")
    if not path:
        raise HTTPException(status_code=503, detail="State service storage is unavailable")
    return _store_for_path(str(Path(path).resolve()))


Authorized = Annotated[None, Depends(_authorize)]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/v1/mfa-claims", status_code=201)
def claim_mfa(claim: MfaClaim, _authorized: Authorized) -> Response:
    if not _store().claim_mfa_counter(claim.username, claim.counter):
        raise HTTPException(status_code=409, detail="MFA counter was already claimed")
    return Response(status_code=201)


@app.post("/v1/sessions", status_code=201)
def register_session(session: SessionRegistration, _authorized: Authorized) -> Response:
    _store().register_session(session.session_id, session.username, session.expires_at)
    return Response(status_code=201)


@app.get("/v1/sessions/{session_id}")
def session_status(session_id: str, at: datetime, _authorized: Authorized) -> dict[str, bool]:
    return {"active": _store().session_is_active(session_id, at)}


@app.delete("/v1/sessions/{session_id}", status_code=204)
def revoke_session(session_id: str, _authorized: Authorized) -> Response:
    _store().revoke_session(session_id)
    return Response(status_code=204)
