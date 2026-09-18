from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from .database import ConsumedAssertionRecord, SessionLocal
from .identity import IdentityAssertion, IdentityPolicyError


class SqlAssertionReplayGuard:
    """Atomically consumes assertion IDs using a database uniqueness boundary."""

    def consume(self, assertion: IdentityAssertion) -> None:
        assertion_id = assertion.verification.assertion_id
        expires_at = assertion.verification.expires_at
        if expires_at <= datetime.now(UTC):
            raise IdentityPolicyError("Identity assertion has expired")
        with SessionLocal() as session:
            session.add(
                ConsumedAssertionRecord(
                    assertion_id=assertion_id,
                    expires_at=expires_at,
                )
            )
            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise IdentityPolicyError(
                    "Identity assertion has already been consumed"
                ) from exc
