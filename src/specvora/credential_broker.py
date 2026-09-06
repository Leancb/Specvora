"""Resolve operator-owned credential references without serializing secret values."""

from __future__ import annotations

import os
import re

from pydantic import BaseModel, ConfigDict, Field


class CredentialReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alias: str = Field(pattern=r"^[a-z][a-z0-9-]{1,62}$")


class CredentialBrokerError(RuntimeError):
    pass


def resolve_bearer_credential(reference: CredentialReference) -> str:
    """Resolve a bearer value from the runner environment using an alias-derived name."""
    variable = "SPECVORA_CREDENTIAL_" + reference.alias.upper().replace("-", "_")
    value = os.environ.get(variable)
    if value is None:
        raise CredentialBrokerError(f"Credential reference is unavailable: {reference.alias}")
    if len(value) < 16 or len(value) > 4096 or re.search(r"[\r\n\x00]", value):
        raise CredentialBrokerError(f"Credential reference is invalid: {reference.alias}")
    return value


def redact_secret(value: str, secret: str | None) -> str:
    if not secret:
        return value
    return value.replace(secret, "[REDACTED]").replace(f"Bearer {secret}", "Bearer [REDACTED]")
