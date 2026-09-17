# Milestone 1 — Planning Vertical Slice

## Product objective

Prove that the platform can accept an ambiguous product request, create a durable workflow run, invoke a bounded Planning Agent, and return structured planning artifacts that are visible through an API and UI.

## Example request

> Add customer churn forecasting to our SaaS product and expose the results through the mobile app.

## Functional requirements

1. A user can create a product request from the Command Center UI.
2. The API creates a unique workflow run and persists the original request.
3. The Planning Agent converts the request into structured artifacts.
4. Planning output includes business objective, scope, assumptions, functional requirements, non-functional requirements, acceptance criteria, dependencies, risks, and implementation tasks.
5. Every acceptance criterion has a stable identifier for downstream traceability.
6. Every planning invocation records provider/model metadata, status, timestamps, and cost/usage metadata when available.
7. A mock provider can execute the workflow without paid API calls.
8. The UI can display workflow status and planning artifacts.
9. Invalid or incomplete structured agent output fails validation rather than silently entering workflow state.

## Non-functional requirements

- Provider-independent LLM interface.
- Structured Pydantic contracts.
- Durable state in PostgreSQL.
- REST API documented through OpenAPI.
- Automated backend tests.
- No API keys committed to source control.
- Agent actions must emit auditable events.

## Acceptance criteria

- `AC-001`: Given a valid product request, the API returns a unique workflow-run identifier.
- `AC-002`: The original request is retrievable after creation.
- `AC-003`: Planning produces schema-valid requirements and acceptance criteria.
- `AC-004`: Planning artifacts are associated with the originating workflow run.
- `AC-005`: Mock mode completes without OpenAI or Anthropic credentials.
- `AC-006`: Invalid planning output is rejected and the run records a failure state.
- `AC-007`: The UI displays the original request, workflow status, requirements, acceptance criteria, dependencies, and risks.
- `AC-008`: Automated tests validate the core request-to-plan path.
- `AC-009`: Secrets are supplied only through environment/configuration mechanisms and are excluded from version control.
- `AC-010`: Planning execution creates an audit event containing agent name, action, status, and timestamp.

## Out of scope for Milestone 1

Architecture Agent, repository modification, pull-request creation, QA execution, security scanning, remediation loops, human merge approval, AWS deployment, and SWE-bench execution. These enter subsequent milestones after the planning vertical slice is reliable.
