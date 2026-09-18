"""Bounded repository-mutation proof.

This deliberately small module exists to prove that a policy-approved
EngineeringArtifact can be applied only to its pre-authorized agent branch.
"""


def governed_mutation_proof() -> str:
    """Return a deterministic marker used by executable QA."""
    return "governed-mutation-proof"
