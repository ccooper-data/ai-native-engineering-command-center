from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from app.authentication import TokenVerificationError, assertion_from_verified_token
from app.identity import actor_from_verified_assertion


@dataclass
class Claims:
    issuer: str
    subject: str
    audience: str
    assertion_id: str
    issued_at: datetime
    expires_at: datetime


class RecordingVerifier:
    def __init__(self) -> None:
        self.tokens: list[str] = []

    def verify(self, token: str) -> Claims:
        self.tokens.append(token)
        now = datetime.now(UTC)
        return Claims(
            issuer="https://token.actions.githubusercontent.com",
            subject="github:user:verified",
            audience="ai-native-engineering-command-center",
            assertion_id="assertion-123",
            issued_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=5),
        )


def test_token_must_pass_verifier_before_identity_policy() -> None:
    verifier = RecordingVerifier()
    assertion = assertion_from_verified_token(
        "signed-token",
        verifier,
        actor_type="human",
        authentication_source="github-oidc",
        role="workflow-approver",
        capability="approve-workflow",
        workflow_id="workflow-123",
        commit_sha="a" * 40,
    )
    actor = actor_from_verified_assertion(assertion)
    assert verifier.tokens == ["signed-token"]
    assert actor.identity_id == "github:user:verified"


def test_empty_token_is_rejected_before_verifier() -> None:
    verifier = RecordingVerifier()
    with pytest.raises(TokenVerificationError, match="required"):
        assertion_from_verified_token(
            "",
            verifier,
            actor_type="human",
            authentication_source="github-oidc",
            role="workflow-approver",
            capability="approve-workflow",
            workflow_id="workflow-123",
            commit_sha="a" * 40,
        )
    assert verifier.tokens == []
