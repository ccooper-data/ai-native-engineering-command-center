import pytest

from app.identity import IdentityAssertion, IdentityPolicyError, actor_from_verified_assertion, require_capability


def test_verified_github_human_identity_is_accepted() -> None:
    actor = actor_from_verified_assertion(
        IdentityAssertion(
            subject="github:user:123",
            actor_type="human",
            authentication_source="github-oidc",
            role="incident-resolver",
            verified=True,
        )
    )
    assert actor.identity_id == "github:user:123"
    assert actor.actor_type == "human"


def test_self_declared_unverified_human_identity_is_rejected() -> None:
    with pytest.raises(IdentityPolicyError, match="not verified"):
        actor_from_verified_assertion(
            IdentityAssertion(
                subject="attacker",
                actor_type="human",
                authentication_source="github-oidc",
                role="approver",
                verified=False,
            )
        )


def test_human_identity_from_untrusted_source_is_rejected() -> None:
    with pytest.raises(IdentityPolicyError, match="trusted authentication source"):
        actor_from_verified_assertion(
            IdentityAssertion(
                subject="self-declared",
                actor_type="human",
                authentication_source="request-body",
                role="incident-resolver",
                verified=True,
            )
        )


def test_authenticated_human_without_required_role_is_not_authorized() -> None:
    actor = actor_from_verified_assertion(
        IdentityAssertion(
            subject="github:user:developer",
            actor_type="human",
            authentication_source="github-oidc",
            role="developer",
            verified=True,
        )
    )
    with pytest.raises(IdentityPolicyError, match="not authorized"):
        require_capability(actor, "resolve-repository-incident")


def test_incident_resolver_role_has_only_incident_resolution_capability() -> None:
    actor = actor_from_verified_assertion(
        IdentityAssertion(
            subject="github:user:resolver",
            actor_type="human",
            authentication_source="github-oidc",
            role="incident-resolver",
            verified=True,
        )
    )
    require_capability(actor, "resolve-repository-incident")
    with pytest.raises(IdentityPolicyError, match="not authorized"):
        require_capability(actor, "approve-workflow")
