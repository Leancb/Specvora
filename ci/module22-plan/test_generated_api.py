"""Reviewed module 22 CI fixture cases; execution requires a detached signature."""

import os

import httpx
import pytest

CASES = [
    ("rate-limit", 429),
    ("dependency-failure", 503),
]


@pytest.mark.parametrize(("fixture", "expected"), CASES)
def test_controlled_resilience_fixture(fixture: str, expected: int) -> None:
    response = httpx.get(
        os.environ["SPECVORA_BASE_URL"].rstrip("/") + "/pets/ci-pet",
        headers={"X-Specvora-Fixture": fixture},
        timeout=10,
        follow_redirects=False,
        trust_env=False,
    )
    assert response.status_code == expected
