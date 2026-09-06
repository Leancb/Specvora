"""Explicit local-only target for deterministic resilience training fixtures."""

from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title="Specvora controlled fixture target")


@app.get("/pets/{pet_id}")
def get_pet(
    pet_id: str,
    x_specvora_fixture: str | None = Header(default=None),
    x_specvora_auth_fixture: str | None = Header(default=None),
    x_specvora_dependency_fixture: str | None = Header(default=None),
) -> dict:
    if x_specvora_auth_fixture in {"missing", "expired"}:
        raise HTTPException(status_code=401, detail="Controlled authentication fixture")
    if x_specvora_auth_fixture == "insufficient-scope":
        raise HTTPException(status_code=403, detail="Controlled authorization fixture")
    if x_specvora_auth_fixture not in {None, "valid"}:
        raise HTTPException(status_code=400, detail="Unknown authentication fixture")
    if x_specvora_dependency_fixture in {"unavailable", "timeout"}:
        raise HTTPException(status_code=503, detail="Controlled dependency fixture")
    if x_specvora_dependency_fixture is not None:
        raise HTTPException(status_code=400, detail="Unknown dependency fixture")
    if x_specvora_fixture == "rate-limit":
        raise HTTPException(status_code=429, detail="Controlled rate-limit fixture")
    if x_specvora_fixture == "dependency-failure":
        raise HTTPException(status_code=503, detail="Controlled dependency failure fixture")
    if x_specvora_fixture is not None:
        raise HTTPException(status_code=400, detail="Unknown fixture")
    return {"id": pet_id, "name": "Controlled pet"}
