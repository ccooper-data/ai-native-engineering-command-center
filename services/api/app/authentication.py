from typing import Protocol

from .identity import IdentityAssertion, VerificationProvenance


class TokenVerificationError(ValueError):
    pass


class VerifiedTokenClaims(Protocol):
    @property
    def issuer(self) -> str: ...
    @property
    def subject(self) -> str: ...
    @property
    def audience(self) -> str: ...
    @property
    def assertion_id(self) -> str: ...
    @property
    def issued_at(self): ...
    @property
    def expires_at(self): ...


class TokenVerifier(Protocol):
    def verify(self, token: str) -> VerifiedTokenClaims: ...


def assertion_from_verified_token(
    token: str,
    verifier: TokenVerifier,
    *,
    actor_type: str,
    authentication_source: str,
    role: str,
) -> IdentityAssertion:
    """Convert cryptographically verified claims into policy input.

    The verifier owns signature/key validation. This adapter does not decode or
    trust unsigned token contents.
    """
    if not token:
        raise TokenVerificationError("Authentication token is required")
    claims = verifier.verify(token)
    return IdentityAssertion(
        subject=claims.subject,
        actor_type=actor_type,
        authentication_source=authentication_source,
        role=role,
        verification=VerificationProvenance(
            issuer=claims.issuer,
            audience=claims.audience,
            verification_method="cryptographic-token-verifier",
            assertion_id=claims.assertion_id,
            issued_at=claims.issued_at,
            expires_at=claims.expires_at,
        ),
    )
