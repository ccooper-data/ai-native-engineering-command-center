import pytest

from app.identity import IdentityAssertion, IdentityPolicyError, actor_from_verified_assertion


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
