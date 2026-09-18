from typing import Protocol

from fastapi import Header, HTTPException, status

from .identity import IdentityAssertion


class RequestIdentityVerifier(Protocol):
    def verify_bearer(
        self,
        token: str,
        *,
        capability: str,
        workflow_id: str,
        commit_sha: str,
    ) -> IdentityAssertion: ...


class UnconfiguredRequestIdentityVerifier:
    def verify_bearer(
        self,
        token: str,
        *,
        capability: str,
        workflow_id: str,
        commit_sha: str,
    ) -> IdentityAssertion:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trusted request identity verifier is not configured",
        )


request_identity_verifier: RequestIdentityVerifier = UnconfiguredRequestIdentityVerifier()


def verified_approval_assertion(
    workflow_id: str,
    commit_sha: str,
    authorization: str | None = Header(default=None),
) -> IdentityAssertion:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer authentication is required")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer authentication is required")
    return request_identity_verifier.verify_bearer(
        token,
        capability="approve-workflow",
        workflow_id=workflow_id,
        commit_sha=commit_sha,
    )
