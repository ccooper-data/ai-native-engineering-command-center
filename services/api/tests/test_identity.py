from datetime import UTC, datetime, timedelta

import pytest

from app.identity import (
    AuthorizationContext,
    IdentityAssertion,
    IdentityPolicyError,
    InMemoryAssertionReplayGuard,
    VerificationProvenance,
    actor_from_verified_assertion,
    require_authorization_context,
    require_capability,
)


def verification(**overrides) -> VerificationProvenance:
    now = datetime.now(UTC)
    values = {
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "ai-native-engineering-command-center",
        "verification_method": "oidc-signature",
        "assertion_id": "assertion-123",
        "authorization_context": AuthorizationContext(capability="approve-workflow", workflow_id="workflow-123", commit_sha="a" * 40),
        "issued_at": now - timedelta(minutes=1),
        "expires_at": now + timedelta(minutes=5),
    }
    values.update(overrides)
    return VerificationProvenance(**values)


def assertion(role: str = "incident-resolver", **overrides) -> IdentityAssertion:
    values = {
        "subject": "github:user:123",
        "actor_type": "human",
        "authentication_source": "github-oidc",
        "role": role,
        "verification": verification(),
    }
    values.update(overrides)
    return IdentityAssertion(**values)


def test_verified_github_human_identity_is_accepted() -> None:
    actor = actor_from_verified_assertion(assertion())
    assert actor.identity_id == "github:user:123"
    assert actor.actor_type == "human"


def test_expired_identity_assertion_is_rejected() -> None:
    now = datetime.now(UTC)
    with pytest.raises(IdentityPolicyError, match="expired"):
        actor_from_verified_assertion(assertion(verification=verification(expires_at=now - timedelta(seconds=1))))


def test_wrong_audience_is_rejected() -> None:
    with pytest.raises(IdentityPolicyError, match="audience"):
        actor_from_verified_assertion(assertion(verification=verification(audience="other-service")))


def test_untrusted_issuer_is_rejected() -> None:
    with pytest.raises(IdentityPolicyError, match="issuer"):
        actor_from_verified_assertion(assertion(verification=verification(issuer="https://attacker.example")))


def test_human_identity_from_untrusted_source_is_rejected() -> None:
    with pytest.raises(IdentityPolicyError, match="trusted authentication source"):
        actor_from_verified_assertion(assertion(authentication_source="request-body"))


def test_authenticated_human_without_required_role_is_not_authorized() -> None:
    actor = actor_from_verified_assertion(assertion(role="developer"))
    with pytest.raises(IdentityPolicyError, match="not authorized"):
        require_capability(actor, "resolve-repository-incident")


def test_incident_resolver_role_has_only_incident_resolution_capability() -> None:
    actor = actor_from_verified_assertion(assertion())
    require_capability(actor, "resolve-repository-incident")
    with pytest.raises(IdentityPolicyError, match="not authorized"):
        require_capability(actor, "approve-workflow")


def test_sensitive_identity_assertion_cannot_be_replayed() -> None:
    guard = InMemoryAssertionReplayGuard()
    identity_assertion = assertion()
    guard.consume(identity_assertion)
    with pytest.raises(IdentityPolicyError, match="already been consumed"):
        guard.consume(identity_assertion)


def test_authorization_context_must_match_exact_action_resource_and_sha() -> None:
    identity_assertion = assertion()
    require_authorization_context(
        identity_assertion,
        capability="approve-workflow",
        workflow_id="workflow-123",
        commit_sha="a" * 40,
    )
    with pytest.raises(IdentityPolicyError, match="does not match"):
        require_authorization_context(
            identity_assertion,
            capability="resolve-repository-incident",
            workflow_id="workflow-123",
            commit_sha="a" * 40,
        )
    with pytest.raises(IdentityPolicyError, match="does not match"):
        require_authorization_context(
            identity_assertion,
            capability="approve-workflow",
            workflow_id="workflow-999",
            commit_sha="a" * 40,
        )
    with pytest.raises(IdentityPolicyError, match="does not match"):
        require_authorization_context(
            identity_assertion,
            capability="approve-workflow",
            workflow_id="workflow-123",
            commit_sha="b" * 40,
        )
