from datetime import UTC, datetime

from pydantic import BaseModel, Field

from .contracts import ActorIdentity


class AuthorizationContext(BaseModel):
    capability: str = Field(min_length=1)
    workflow_id: str = Field(min_length=1)
    commit_sha: str = Field(min_length=40, max_length=40)


class VerificationProvenance(BaseModel):
    issuer: str = Field(min_length=1)
    audience: str = Field(min_length=1)
    verification_method: str = Field(min_length=1)
    assertion_id: str = Field(min_length=1)
    authorization_context: AuthorizationContext | None = None
    issued_at: datetime
    expires_at: datetime


class IdentityAssertion(BaseModel):
    subject: str = Field(min_length=1)
    actor_type: str = Field(pattern="^(human|service|agent)$")
    authentication_source: str = Field(min_length=1)
    role: str = Field(min_length=1)
    verification: VerificationProvenance


class IdentityPolicyError(ValueError):
    pass


TRUSTED_HUMAN_AUTH_SOURCES = {"github-oidc", "enterprise-sso"}


def actor_from_verified_assertion(assertion: IdentityAssertion) -> ActorIdentity:
    """Construct authority-bearing identity only from a verified trusted assertion."""
    now = datetime.now(UTC)
    if assertion.verification.expires_at <= now:
        raise IdentityPolicyError("Identity assertion has expired")
    if assertion.verification.issued_at > now:
        raise IdentityPolicyError("Identity assertion was issued in the future")
    if assertion.verification.issuer not in {"https://token.actions.githubusercontent.com", "enterprise-sso"}:
        raise IdentityPolicyError("Identity assertion issuer is not trusted")
    if assertion.verification.audience != "ai-native-engineering-command-center":
        raise IdentityPolicyError("Identity assertion audience is invalid")
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


class InMemoryAssertionReplayGuard:
    """Process-local replay guard for deterministic tests only; not production authorization."""

    def __init__(self) -> None:
        self._consumed: set[str] = set()

    def consume(self, assertion: IdentityAssertion) -> None:
        assertion_id = assertion.verification.assertion_id
        if assertion_id in self._consumed:
            raise IdentityPolicyError("Identity assertion has already been consumed")
        self._consumed.add(assertion_id)


def require_authorization_context(
    assertion: IdentityAssertion,
    *,
    capability: str,
    workflow_id: str,
    commit_sha: str,
) -> None:
    context = assertion.verification.authorization_context
    if context is None:
        raise IdentityPolicyError("Identity assertion lacks authorization context")
    if (
        context.capability != capability
        or context.workflow_id != workflow_id
        or context.commit_sha != commit_sha
    ):
        raise IdentityPolicyError("Identity assertion authorization context does not match requested action")
