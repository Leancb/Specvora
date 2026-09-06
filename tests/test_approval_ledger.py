from uuid import uuid4

import httpx
import pytest

from specvora.approval_ledger import claim_github_reference


def test_github_reference_claim_is_atomic_and_bound_to_commit():
    approval_id = uuid4()
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        status = 201 if len(requests) == 1 else 422
        return httpx.Response(status, json={"message": "Reference already exists"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        reference = claim_github_reference(
            approval_id,
            "Leancb/Specvora",
            "a" * 40,
            "secret-token",
            client=client,
        )
        assert reference == f"refs/tags/specvora-approvals/{approval_id}"
        with pytest.raises(ValueError, match="already be consumed"):
            claim_github_reference(
                approval_id,
                "Leancb/Specvora",
                "a" * 40,
                "secret-token",
                client=client,
            )
    assert requests[0].url == "https://api.github.com/repos/Leancb/Specvora/git/refs"
    assert requests[0].headers["authorization"] == "Bearer secret-token"
    assert requests[0].read() == (
        f'{{"ref":"refs/tags/specvora-approvals/{approval_id}","sha":"{"a" * 40}"}}'
    ).encode()


@pytest.mark.parametrize(
    ("repository", "commit_sha", "token", "message"),
    [
        ("invalid", "a" * 40, "token", "repository"),
        ("owner/repo", "not-a-sha", "token", "commit SHA"),
        ("owner/repo", "a" * 40, "", "token"),
    ],
)
def test_github_reference_claim_rejects_invalid_configuration(
    repository, commit_sha, token, message
):
    with pytest.raises(ValueError, match=message):
        claim_github_reference(uuid4(), repository, commit_sha, token)


@pytest.mark.parametrize("status", [401, 403, 500])
def test_github_reference_claim_fails_closed_without_remote_details(status):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text="remote-secret-detail")

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(ValueError) as failure,
    ):
        claim_github_reference(uuid4(), "owner/repo", "b" * 40, "token", client=client)
    assert "remote-secret-detail" not in str(failure.value)
