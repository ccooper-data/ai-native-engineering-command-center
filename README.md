# AI-Native Engineering Command Center

A governed, auditable multi-agent software-engineering platform for turning ambiguous product requests into structured planning, architecture, implementation artifacts, quality/security evidence, controlled repository changes, human decisions, and draft pull-request evidence.

This project is intentionally different from an “agents talking to agents” demo. LLM reasoning is separated from repository authority, consequential actions are fail-closed, and progression depends on evidence tied to immutable commit identity.

## What is implemented

### Multi-agent engineering
- Planning, Architecture, and Engineering responsibilities with schema-enforced artifacts.
- LangGraph orchestration and provider-independent OpenAI / Anthropic / deterministic mock abstractions.
- QA, Security, independent Review, remediation, requirements-to-implementation traceability, and model usage/cost accounting.
- FastAPI/Python backend and Next.js/TypeScript Command Center.

### Governed repository mutation
- Zero-mutation repository dry runs and bounded change-set policy.
- Isolated `agent/*` branch mutation; protected paths and branch aliases fail closed.
- Python AST and Ruff-aware source preflight before governed mutation.
- Digest-bound preflight evidence: changed source invalidates stale validation.
- Post-write content verification and immutable mutation commit-SHA capture.
- Rollback after mutation failure and independent rollback verification.
- Failed rollback becomes a critical repository incident rather than ordinary remediation.

### Human authority and identity
- Structured actor identities rather than display-name authorization.
- Separation of authentication, identity policy, role/capability authorization, and sensitive action execution.
- Trusted issuer, audience, issuance/expiry, authentication-source, and role checks.
- Sensitive approval and incident recovery are human-only capabilities.
- Assertions are bound to exact capability + workflow + commit SHA.
- SQL-backed atomic assertion consumption prevents replay across service instances.
- Mutation actor cannot independently certify recovery of its own critical incident.

### Evidence and progression
- Source-preflight evidence and audit events.
- Verified mutation SHA, executable CI evidence, independent review, and human approval form a chain of custody.
- Stale or mismatched mutation/CI/approval identities block progression.
- Human approval permits generation of a governed **draft PR** only.
- Merge and deployment authority remain explicitly separate and are not granted by approval.
- Critical incident recovery invalidates pre-incident mutation, CI, review, and approval trust so fresh evidence must be established.

## Governed workflow

```text
Product Request
      |
Planning Agent
      |
Architecture Agent
      |
Engineering Agent
      |
Source Preflight ----> BLOCK on deterministic failure
      |
Repository Dry Run
      |
Bounded Isolated Mutation
      |
Post-write Verification
      | failure
      +----> Rollback ----> verify rollback
                              | failure
                              v
                     CRITICAL REPOSITORY INCIDENT
                              |
                    independent human recovery
                              |
                    prior trust evidence cleared
      |
Executable CI
      |
QA / Security / Review
      |
Acceptance-Criteria / Evidence Gates
      |
Authenticated HUMAN APPROVAL
      |
Governed Draft PR
      |
Merge / Deployment remain separate authorities
```

## Trust model

The Command Center does not treat model output as authority.

```text
LLM reasoning
   != repository authority
   != human identity
   != approval authority
   != merge authority
   != deployment authority
```

Sensitive human actions follow a separate trust chain:

```text
Bearer credential
  -> cryptographic verifier boundary
  -> verified claims / provenance
  -> trusted ActorIdentity
  -> role + human capability
  -> exact workflow/SHA authorization context
  -> atomic one-time assertion consumption
  -> governed action
```

The repository currently provides the verifier **interface/boundary** and a fail-closed API default. A production external OIDC/SSO cryptographic verifier is intentionally not faked in this repository.

## Failure model

Important failures are explicit state transitions, not exceptions that disappear into logs.

- Failed source preflight: zero repository writes.
- Stored content differs from intended content: mutation fails and rollback is attempted.
- Verified rollback succeeds: controlled remediation can proceed.
- Rollback cannot be verified: critical uncertain repository state; progression stops.
- Critical recovery requires an independently authorized human and exact restored SHA.
- CI failure, review failure, identity mismatch, stale approval, or governance-control regression blocks readiness.
- A recovered incident never resurrects stale approval or CI evidence.

## Adversarial regression evidence

The test suite deliberately attacks governance boundaries, including:

- service identity attempting a human-only approval capability;
- wrong role/capability;
- wrong workflow authorization context;
- stale commit SHA;
- replayed authentication assertion;
- source modified after preflight;
- corrupted repository write;
- failed rollback and uncertain repository state;
- self-resolution / authority separation;
- stale CI or approval evidence;
- attempted merge/deployment authority escalation;
- corruption -> failed rollback -> durable incident -> independently authenticated recovery -> trust invalidation.

These tests complement normal unit/integration tests and are intended to detect control regression as the architecture evolves.

## Technology

| Layer | Implementation |
| --- | --- |
| Backend | FastAPI, Python, Pydantic |
| Frontend | Next.js, TypeScript |
| Orchestration | LangGraph |
| LLM abstraction | OpenAI, Anthropic, deterministic mock providers |
| Persistence | SQLAlchemy; PostgreSQL-oriented architecture with local SQLite test support |
| Repository governance | bounded executor, source preflight, digest binding, post-write verification, rollback |
| CI/CD | GitHub Actions |
| Security | Gitleaks, Semgrep |
| Infrastructure direction | AWS, Terraform, Docker |
| Observability direction | OpenTelemetry |
| Testing | pytest, frontend type/build checks, adversarial governance regression |

## CI gates

The repository's CI independently validates three major surfaces:

1. **Backend** — Ruff plus pytest.
2. **Frontend** — TypeScript checking plus production build.
3. **Security** — Gitleaks plus Semgrep.

Application preflight is intentionally not a replacement for CI. It moves deterministic feedback earlier; CI remains independent evidence.

## Model-provider operation

Deterministic development does not require paid model access:

```bash
COMMAND_CENTER_LLM_PROVIDER=mock
```

Controlled real-model workflows can use configured OpenAI or Anthropic providers through the same abstraction. Credentials belong in runtime environment/secrets and must never be committed.

## Management Command Center

The management surface exposes workflow state, traceability, audit events, CI/review/approval status, chain-of-custody identity, governance readiness, and critical repository incidents.

Readiness is fail-closed. A workflow can reach `READY_FOR_DRAFT_PR` only when required mutation, CI, review, identity, and human-approval evidence are aligned.

## Repository design principles

1. **Evidence before authority.**
2. **LLM reasoning is not repository permission.**
3. **Human identity is authenticated, not self-declared.**
4. **Authorization is capability-specific and least privilege.**
5. **Immutable commit identity binds mutation, CI, and approval.**
6. **Recovery does not restore stale trust.**
7. **Security controls fail closed.**
8. **CI remains independent of application claims.**
9. **Adversarial tests validate control composition, not only happy paths.**
10. **Merge and deployment remain separate human-controlled authorities.**

## Current status

**Governed engineering core: implemented and under final convergence/release review.**

The remaining work is primarily portfolio/release convergence: final architecture review, documentation/evidence polish, release-baseline validation, and clearly separating implemented behavior from future production integrations.

## Scope boundaries / future production integrations

The repository deliberately does not claim production capabilities it does not yet implement. Future integrations include:

- a concrete external GitHub OIDC / enterprise SSO cryptographic verifier;
- production deployment authority and post-deployment verification;
- production-grade distributed infrastructure/observability deployment;
- operational key rotation, identity lifecycle, and environment-specific authorization policy.

Those integrations can plug into the existing trust boundaries without granting additional authority to LLM agents.
