# Architecture & Governance Evidence

Validated engineering baseline: `f3914f23f17710b63d357acef858334582ac2836`

## Executive architecture

The AI-Native Engineering Command Center separates reasoning, execution, evidence, and authority.

```text
Product intent
   |
Planning -> Architecture -> Engineering
   |
Deterministic source preflight
   |
Zero-mutation dry run
   |
Bounded isolated repository mutation
   |
Post-write verification + immutable commit SHA
   |
Executable CI + QA + Security + Independent Review
   |
Authenticated human approval bound to exact workflow/SHA
   |
Governed draft PR

Merge authority != approval authority
Deployment authority != approval authority
```

## Control map

| Risk | Preventive / detective control | Fail-closed result |
| --- | --- | --- |
| LLM gains repository authority | reasoning and mutation capabilities are separated | model output alone cannot mutate |
| Unsafe path/branch | bounded change-set and agent-branch policy | mutation rejected |
| Invalid generated Python | AST + Ruff-aware preflight | zero governed writes |
| Source changes after preflight | SHA-256 EngineeringArtifact digest binding | stale evidence rejected/recomputed |
| Repository stores different content | post-write readback verification | rollback attempted |
| Rollback fails | branch SHA rollback verification | critical repository incident |
| Stale CI/approval | mutation, CI, approval SHA chain of custody | progression blocked |
| Forged human authority | structured identity + trusted authentication provenance | sensitive action rejected |
| Wrong role | explicit role/capability map | action rejected |
| Service impersonates human | human-only sensitive capabilities | action rejected |
| Valid credential used for wrong action | capability + workflow + SHA context binding | action rejected |
| Credential replay | SQL uniqueness-backed assertion consumption | second use rejected |
| Mutation actor certifies own recovery | separation of duties | recovery rejected |
| Human approval escalates to merge/deploy | post-approval capability boundary | merge/deploy denied |
| Control regression | adversarial benchmark/regression evidence | readiness blocked |

## Evidence chain

A workflow is not considered ready because an agent says it is ready. Readiness is derived from independently recorded evidence:

1. source-preflight result bound to the exact EngineeringArtifact digest;
2. verified repository mutation and immutable commit SHA;
3. executable CI evidence for that SHA;
4. independent review and acceptance-criteria traceability;
5. authenticated human approval for the same workflow and SHA;
6. capability evaluation allowing only a governed draft PR.

Any identity mismatch or unresolved critical repository incident blocks progression.

## Human authorization boundary

Sensitive actions follow:

```text
Bearer credential
 -> cryptographic verifier interface
 -> verification provenance
 -> trusted ActorIdentity
 -> explicit role/capability
 -> human-only sensitive capability
 -> exact capability/workflow/SHA context
 -> atomic one-time assertion consumption
 -> governed action
```

The API intentionally fails closed when a trusted external verifier is not configured. The repository does not fake production OIDC verification.

## Repository integrity and recovery

The hardened isolated executor:

1. validates bounded repository policy;
2. requires matching source-preflight evidence or recomputes it;
3. captures the pre-mutation branch SHA;
4. applies changes only to the authorized `agent/*` branch;
5. reads each changed path back and compares stored state with intended state;
6. captures the resulting immutable commit SHA;
7. on failure, resets to the starting SHA and verifies rollback;
8. if rollback cannot be verified, creates a critical uncertain-state incident.

Critical recovery requires independently authenticated human authority scoped to the exact workflow and restored SHA. Recovery clears pre-incident mutation, CI, review, and approval trust.

## Adversarial validation

The regression suite deliberately exercises:

- forged/service human authority;
- wrong role/capability;
- wrong workflow context;
- stale SHA;
- assertion replay;
- modified source after preflight;
- corrupted post-write repository content;
- failed rollback;
- critical incident persistence;
- mutation-actor/self-recovery separation;
- independent human recovery;
- stale trust invalidation;
- merge/deployment escalation attempts.

A full integrated scenario traverses corruption -> verification failure -> rollback failure -> critical incident -> independent human recovery -> evidence invalidation.

## Portfolio significance

This project demonstrates more than prompt engineering or multi-agent choreography. It demonstrates design of an AI-enabled engineering control plane where autonomy is bounded by deterministic policy, immutable evidence, least privilege, human decision rights, and adversarial validation.

Relevant engineering themes include:

- AI/agent architecture
- platform engineering
- secure software supply chain
- identity and authorization design
- responsible AI / AI governance
- software assurance
- CI/CD governance
- auditability and evidence engineering
- failure recovery and operational controls
- executive/management readiness reporting

## Production boundaries

Implemented architecture should not be confused with unimplemented production integrations. Remaining production integrations include:

- concrete external GitHub OIDC / enterprise SSO cryptographic verification;
- production merge/deployment authority;
- post-deployment verification;
- deployed distributed infrastructure and observability;
- operational identity lifecycle and key rotation.

These are intentionally outside the current portfolio baseline and can attach to existing narrow interfaces without granting additional authority to LLM agents.
