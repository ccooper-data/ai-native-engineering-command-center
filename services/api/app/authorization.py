from .contracts import ActorIdentity
from .identity import (
    IdentityAssertion,
    actor_from_verified_assertion,
    require_authorization_context,
    require_human_capability,
)


class ReplayGuard:
    def consume(self, assertion: IdentityAssertion) -> None: ...


def authorize_sensitive_action(
    assertion: IdentityAssertion,
    replay_guard: ReplayGuard,
    *,
    capability: str,
    workflow_id: str,
    commit_sha: str,
) -> ActorIdentity:
    """Fail-closed composite authorization for sensitive human actions."""
    actor = actor_from_verified_assertion(assertion)
    require_human_capability(actor, capability)
    require_authorization_context(
        assertion,
        capability=capability,
        workflow_id=workflow_id,
        commit_sha=commit_sha,
    )
    replay_guard.consume(assertion)
    return actor
