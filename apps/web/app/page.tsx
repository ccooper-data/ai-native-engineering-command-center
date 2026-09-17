"use client";

import { FormEvent, useState } from "react";

type Criterion = { id: string; statement: string };
type Plan = { business_objective: string; functional_requirements: string[]; acceptance_criteria: Criterion[]; dependencies: string[]; risks: string[]; implementation_tasks: string[] };
type Decision = { id: string; title: string; decision: string };
type Architecture = { summary: string; affected_components: string[]; security_controls: string[]; decisions: Decision[]; implementation_sequence: string[] };
type FileChange = { path: string; operation: string; purpose: string };
type Engineering = { branch_name: string; summary: string; files: FileChange[]; acceptance_criteria_addressed: string[]; tests_required: string[] };
type Run = { id: string; status: string; provider: string; model: string; planning: Plan | null; architecture: Architecture | null; engineering: Engineering | null };

const example = "Add customer churn forecasting to our SaaS product and expose the results through the mobile app.";
const stages = ["Product Request", "Planning", "Architecture", "Engineering", "QA + Security", "Review", "Human Approval", "Deploy"];

export default function Home() {
  const [request, setRequest] = useState(example);
  const [run, setRun] = useState<Run | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError("");
    try {
      const response = await fetch("http://localhost:8000/api/v1/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request }) });
      if (!response.ok) throw new Error(`Workflow failed (${response.status})`);
      setRun(await response.json());
    } catch (err) { setError(err instanceof Error ? err.message : "Unexpected error"); }
    finally { setLoading(false); }
  }

  return <main>
    <header><div><p className="eyebrow">AI-NATIVE ENGINEERING</p><h1>Command Center</h1><p className="subtitle">Bounded autonomous engineering with auditable human control.</p></div><span className="status">3 AGENTS · MOCK MODE</span></header>
    <section className="pipeline" aria-label="Engineering workflow">{stages.map((stage, index) => <div className={index < 4 ? "stage active" : "stage"} key={stage}><span>{String(index + 1).padStart(2, "0")}</span>{stage}</div>)}</section>
    <section className="workspace">
      <form className="panel request" onSubmit={submit}><p className="label">FOUNDER / PRODUCT REQUEST</p><textarea value={request} onChange={(e) => setRequest(e.target.value)} /><button disabled={loading || request.trim().length < 10}>{loading ? "Orchestrating…" : "Start Engineering Workflow"}</button>{error && <p className="error">{error}</p>}<div className="guardrail"><strong>Governance:</strong> Engineering may propose file changes, but this workflow has no repository-write or deployment authority.</div></form>
      <div className="panel output"><div className="outputHeader"><div><p className="label">MULTI-AGENT ARTIFACTS</p><h2>{run ? run.status.toUpperCase() : "WAITING FOR REQUEST"}</h2></div>{run && <code>{run.provider}/{run.model}</code>}</div>
        {!run?.planning ? <div className="empty">Submit a request to run Planning → Architecture → Engineering.</div> : <div className="plan">
          <article><h3>Planning · Business objective</h3><p>{run.planning.business_objective}</p></article>
          <List title="Planning · Acceptance criteria" items={run.planning.acceptance_criteria.map((x) => `${x.id} — ${x.statement}`)} />
          {run.architecture && <><article><h3>Architecture · Summary</h3><p>{run.architecture.summary}</p></article><List title="Architecture · Components" items={run.architecture.affected_components} /><List title="Architecture · Decisions" items={run.architecture.decisions.map((x) => `${x.id}: ${x.title} — ${x.decision}`)} /><List title="Architecture · Security controls" items={run.architecture.security_controls} /></>}
          {run.engineering && <><article><h3>Engineering · Proposed change set</h3><p>{run.engineering.summary}</p><p><b>Proposed branch:</b> {run.engineering.branch_name}</p></article><List title="Engineering · Files" items={run.engineering.files.map((x) => `${x.operation.toUpperCase()} ${x.path} — ${x.purpose}`)} /><List title="Engineering · Tests required" items={run.engineering.tests_required} /></>}
        </div>}
      </div>
    </section>
  </main>;
}

function List({ title, items }: { title: string; items: string[] }) { return <article><h3>{title}</h3><ul>{items.map((item) => <li key={item}>{item}</li>)}</ul></article>; }
