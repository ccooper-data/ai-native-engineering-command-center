# AI-Native Engineering Command Center

A production-oriented multi-agent software engineering platform that transforms an ambiguous product request into structured requirements, architecture decisions, implementation, testing, security review, human approval, and deployment.

## Vision

The Command Center is designed to demonstrate bounded autonomous engineering rather than simulated agent conversations. Agents operate against shared workflow state, use explicitly authorized tools, produce auditable artifacts, and cannot bypass deterministic quality or human-approval gates.

## Target workflow

```text
Product Request
      |
Planning Agent
      |
Architecture Agent
      |
Engineering Agent
      |
+-----+------+
|            |
QA Agent  Security Agent
|            |
+-----+------+
      |
Remediation Gate <---- failed checks
      |
Reviewer Agent
      |
Acceptance Criteria Gate
      |
HUMAN APPROVAL
      |
Merge / Deployment
      |
Post-deployment Verification
```

## Planned stack

- Frontend: Next.js + TypeScript
- Backend: FastAPI + Python
- Agent orchestration: LangGraph
- Database: PostgreSQL + pgvector
- Workflow/cache state: Redis
- LLMs: provider-independent gateway (OpenAI / Anthropic / mock provider)
- Containers: Docker
- Infrastructure: AWS + Terraform
- CI/CD: GitHub Actions
- Observability: OpenTelemetry
- Testing: pytest + frontend tests
- Security: Semgrep, Gitleaks, dependency/container scanning
- API: REST + OpenAPI contracts

## Engineering principles

1. Agents receive least-privilege tool access.
2. Consequential actions require deterministic gates and/or human approval.
3. Every agent run, tool call, artifact, test result, security finding, approval, and deployment is auditable.
4. Failed QA or security checks route work back for remediation rather than being ignored.
5. Workflow cost, retries, and model usage are budgeted and observable.
6. LLM providers are replaceable; orchestration is not coupled to one model vendor.
7. Evaluation uses objective outcomes where possible, including executable tests.

## Evaluation strategy

The project will use three complementary evaluation layers:

- **SWE-bench Verified subset** for real-world software-engineering tasks with executable ground truth.
- **Command Center Product Benchmark** for ambiguous product requests that test planning, requirements, architecture, and traceability.
- **Security Fault Injection Benchmark** for controlled vulnerabilities and unsafe changes that should be detected and blocked.

## Runtime model selection

The default runtime remains deterministic and does not require paid model access:

```bash
COMMAND_CENTER_LLM_PROVIDER=mock
```

A controlled live Planning Agent can be enabled with either provider. API credentials must be supplied through the local/runtime environment and must never be committed to the repository.

OpenAI:

```bash
export COMMAND_CENTER_LLM_PROVIDER=openai
export COMMAND_CENTER_OPENAI_API_KEY='<set-locally>'
export COMMAND_CENTER_OPENAI_MODEL='<supported-model-id>'
```

Anthropic:

```bash
export COMMAND_CENTER_LLM_PROVIDER=anthropic
export COMMAND_CENTER_ANTHROPIC_API_KEY='<set-locally>'
export COMMAND_CENTER_ANTHROPIC_MODEL='<supported-model-id>'
```

For the first live validation, only the Planning Agent should use a paid provider. Architecture, Engineering, QA, and Security remain controlled providers so the test has a bounded cost and a small failure surface.

### First live request

Use the benchmark product request:

> Add customer churn forecasting to our SaaS product and expose the results through the mobile app.

The expected output is a schema-validated PlanningArtifact with explicit assumptions, requirements, dependencies, risks, implementation tasks, and testable acceptance criteria. A live Planning Agent has no repository-write, merge, deployment, or approval authority.

## Milestone 1

Build the first real vertical slice:

> Product request -> Planning Agent -> structured requirements and acceptance criteria -> persisted workflow state -> API -> Command Center UI.

The first milestone supports deterministic development plus opt-in real OpenAI or Anthropic planning through the same provider-independent contract.

## Status

**Phase 1: Governed real-agent integration — in progress**
