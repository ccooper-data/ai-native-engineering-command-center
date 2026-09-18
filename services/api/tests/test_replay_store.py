from datetime import UTC, datetime, timedelta

import pytest

from app.database import ConsumedAssertionRecord, SessionLocal, create_schema
from app.identity import IdentityAssertion, IdentityPolicyError, VerificationProvenance
from app.replay_store import SqlAssertionReplayGuard


def assertion(assertion_id: str) -> IdentityAssertion:
    now = datetime.now(UTC)
    return IdentityAssertion(
        subject="github:user:replay-test",
        actor_type="human",
        authentication_source="github-oidc",
        role="workflow-approver",
        verification=VerificationProvenance(
            issuer="https://token.actions.githubusercontent.com",
            audience="ai-native-engineering-command-center",
            verification_method="oidc-signature",
            assertion_id=assertion_id,
            issued_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=5),
        ),
    )


def test_sql_replay_guard_allows_exactly_one_consumption() -> None:
    create_schema()
    item = assertion("sql-replay-once")
    with SessionLocal() as session:
        session.query(ConsumedAssertionRecord).filter_by(assertion_id="sql-replay-once").delete()
        session.commit()
    first = SqlAssertionReplayGuard()
    second = SqlAssertionReplayGuard()
    first.consume(item)
    with pytest.raises(IdentityPolicyError, match="already been consumed"):
        second.consume(item)
