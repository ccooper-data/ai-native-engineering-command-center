from datetime import UTC, datetime, timedelta

import pytest

from app.authorization import authorize_sensitive_action
from app.identity import (
    AssertionReplayGuard,
    AuthorizationContext,
    IdentityAssertion,
    IdentityPolicyError,
    VerificationProvenance,
)


def assertion(*, capability: str = "approve-workflow", workflow_id: str = "workflow-123", commit_sha: str = "a" * 40) -> IdentityAssertion:
    now = datetime.now(UTC)
    return IdentityAssertion(
        subject="github:user:approver",
        actor_type="human",
        authentication_source="github-oidc",
        role="workflow-approver",
        verification=VerificationProvenance(
            issuer="https://token.actions.githubusercontent.com",
            audience="ai-native-engineering-command-center",
            verification_method="oidc-signature",
            assertion_id="composite-authorization-1",
            authorization_context=AuthorizationContext(
                capability=capability,
                workflow_id=workflow_id,
                commit_sha=commit_sha,
            ),
            issued_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=5),
        ),
    )


def test_composite_authorization_returns_actor_and_consumes_assertion() -> None:
    guard = AssertionReplayGuard()
    item = assertion()
    actor = authorize_sensitive_action(item, guard, capability="approve-workflow", workflow_id="workflow-123", commit_sha="a" * 40)
    assert actor.identity_id == "github:user:approver"
    with pytest.raises(IdentityPolicyError, match="already been consumed"):
        authorize_sensitive_action(item, guard, capability="approve-workflow", workflow_id="workflow-123", commit_sha="a" * 40)


def test_context_mismatch_does_not_consume_assertion() -> None:
    guard = AssertionReplayGuard()
    item = assertion()
    with pytest.raises(IdentityPolicyError, match="does not match"):
        authorize_sensitive_action(item, guard, capability="approve-workflow", workflow_id="other-workflow", commit_sha="a" * 40)
    actor = authorize_sensitive_action(item, guard, capability="approve-workflow", workflow_id="workflow-123", commit_sha="a" * 40)
    assert actor.identity_id == "github:user:approver"
