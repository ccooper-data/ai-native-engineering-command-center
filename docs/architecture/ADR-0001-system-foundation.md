# ADR-0001: System Foundation

- Status: Accepted
- Date: 2026-09-17

## Context

The AI-Native Engineering Command Center must orchestrate real software-development work while preserving traceability, bounded authority, deterministic quality gates, and human control over consequential actions.

## Decision

Use a modular monorepo with the following logical components:

- `apps/web`: Next.js + TypeScript command-center UI.
- `services/api`: FastAPI REST API and OpenAPI contract.
- `services/orchestrator`: LangGraph workflow definitions and agent nodes.
- `packages/contracts`: shared structured workflow contracts and schemas.
- `infra`: Terraform and deployment configuration.
- `benchmarks`: product-request and security-fault evaluation fixtures.
- `docs`: architecture decisions, threat model, runbooks, and evaluation documentation.

PostgreSQL will be the durable system of record. pgvector will initially provide vector retrieval. Redis will support ephemeral workflow coordination/cache where useful, but durable business state must not depend solely on Redis.

LLM access will be implemented behind a provider abstraction supporting OpenAI, Anthropic, and a deterministic mock provider. Agent nodes will consume structured contracts rather than vendor-specific response objects.

## Control model

Agents propose or execute within explicit permissions. QA and security are independent checks. Failed checks route to remediation. Merge and deployment require an explicit human approval record. Deployment logic cannot infer approval from an LLM response.

## Consequences

This introduces more structure than a simple agent demo, but makes the system testable, auditable, provider-independent, and suitable for demonstrating production engineering and AI governance practices.
