from pydantic import BaseModel, Field

from .contracts import ActorIdentity


class IdentityAssertion(BaseModel):
    subject: str = Field(min_length=1)
    actor_type: str = Field(pattern="^(human|service|agent)$")
    authentication_source: str = Field(min_length=1)
    role: str = Field(min_length=1)
    verified: bool


class IdentityPolicyError(ValueError):
    pass


TRUSTED_HUMAN_AUTH_SOURCES = {"github-oidc", "enterprise-sso"}


def actor_from_verified_assertion(assertion: IdentityAssertion) -> ActorIdentity:
    """Construct authority-bearing identity only from a verified trusted assertion."""
    if not assertion.verified:
        raise IdentityPolicyError("Identity assertion is not verified")
    if assertion.actor_type == "human" and assertion.authentication_source not in TRUSTED_HUMAN_AUTH_SOURCES:
        raise IdentityPolicyError("Human identity requires a trusted authentication source")
    return ActorIdentity(
        identity_id=assertion.subject,
        actor_type=assertion.actor_type,
        authentication_source=assertion.authentication_source,
        role=assertion.role,
    )


ROLE_CAPABILITIES: dict[str, set[str]] = {
    "workflow-approver": {"approve-workflow"},
    "incident-resolver": {"resolve-repository-incident"},
    "repository-mutation": {"mutate-isolated-repository"},
    "reviewer": {"independent-review"},
}


def require_capability(actor: ActorIdentity, capability: str) -> None:
    allowed = ROLE_CAPABILITIES.get(actor.role, set())
    if capability not in allowed:
        raise IdentityPolicyError(
            f"Actor role {actor.role!r} is not authorized for capability {capability!r}"
        )


SENSITIVE_CAPABILITIES = {
    "approve-workflow",
    "resolve-repository-incident",
}


def require_human_capability(actor: ActorIdentity, capability: str) -> None:
    require_capability(actor, capability)
    if capability in SENSITIVE_CAPABILITIES and actor.actor_type != "human":
        raise IdentityPolicyError(
            f"Capability {capability!r} requires an authenticated human identity"
        )
    if capability in SENSITIVE_CAPABILITIES and actor.authentication_source not in TRUSTED_HUMAN_AUTH_SOURCES:
        raise IdentityPolicyError(
            f"Capability {capability!r} requires trusted human authentication"
        )
