"use client";

import { FormEvent, useEffect, useState } from "react";

type Criterion = { id: string; statement: string };
type Plan = { business_objective: string; acceptance_criteria: Criterion[] };
type Decision = { id: string; title: string; decision: string };
type Architecture = { summary: string; affected_components: string[]; security_controls: string[]; decisions: Decision[] };
type FileChange = { path: string; operation: string; purpose: string };
type Engineering = { branch_name: string; summary: string; files: FileChange[]; tests_required: string[] };
type Run = { id: string; status: string; provider: string; model: string; planning: Plan | null; architecture: Architecture | null; engineering: Engineering | null };
type Summary = { total_workflows: number; active_workflows: number; blocked_workflows: number; pending_approvals: number; ci_failures: number; review_failures: number; total_tokens: number; estimated_actual_cost_usd: number };

const API = "http://localhost:8000";
const example = "Add customer churn forecasting to our SaaS product and expose the results through the mobile app.";
const stages = ["Request", "Planning", "Architecture", "Engineering", "QA + Security", "Review", "Approval", "Deploy"];

export default function Home() {
  const [request, setRequest] = useState(example);
  const [run, setRun] = useState<Run | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function refreshSummary() {
    const response = await fetch(`${API}/api/v1/management/summary`);
    if (response.ok) setSummary(await response.json());
  }

  useEffect(() => { void refreshSummary(); }, []);

  async function submit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError("");
    try {
      const response = await fetch(`${API}/api/v1/runs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ request }) });
      if (!response.ok) throw new Error(`Workflow failed (${response.status})`);
      setRun(await response.json()); await refreshSummary();
    } catch (err) { setError(err instanceof Error ? err.message : "Unexpected error"); }
    finally { setLoading(false); }
  }

  const cards = [
    ["Workflows", summary?.total_workflows ?? 0],
    ["Active", summary?.active_workflows ?? 0],
    ["Blocked", summary?.blocked_workflows ?? 0],
    ["Pending approvals", summary?.pending_approvals ?? 0],
    ["CI failures", summary?.ci_failures ?? 0],
    ["Tokens", (summary?.total_tokens ?? 0).toLocaleString()],
    ["Model cost", `$${(summary?.estimated_actual_cost_usd ?? 0).toFixed(4)}`],
  ];

  return <main>
    <header><div><p className="eyebrow">AI-NATIVE ENGINEERING</p><h1>Executive Command Center</h1><p className="subtitle">Governed autonomy, quality evidence, cost control, and human decision rights.</p></div><span className="status">READ-ONLY GOVERNANCE VIEW</span></header>
    <section className="metrics">{cards.map(([label, value]) => <article className="metric" key={label}><span>{label}</span><strong>{value}</strong></article>)}</section>
    <section className="pipeline">{stages.map((stage, index) => <div className={index < 4 ? "stage active" : "stage"} key={stage}><span>{String(index + 1).padStart(2, "0")}</span>{stage}</div>)}</section>
    <section className="workspace">
      <form className="panel request" onSubmit={submit}><p className="label">PRODUCT REQUEST</p><textarea value={request} onChange={(e) => setRequest(e.target.value)} /><button disabled={loading || request.trim().length < 10}>{loading ? "Orchestrating…" : "Start Governed Workflow"}</button>{error && <p className="error">{error}</p>}<div className="guardrail"><strong>Authority boundary:</strong> this interface can initiate workflow reasoning and read governance evidence. Merge and deployment authority remain unavailable.</div></form>
      <div className="panel output"><div className="outputHeader"><div><p className="label">WORKFLOW EVIDENCE</p><h2>{run ? run.status.toUpperCase() : "PORTFOLIO READY"}</h2></div>{run && <code>{run.provider}/{run.model}</code>}</div>
        {!run?.planning ? <div className="empty">Executive metrics are live. Start a workflow to inspect Planning → Architecture → Engineering evidence.</div> : <div className="plan">
          <article><h3>Planning · Business objective</h3><p>{run.planning.business_objective}</p></article>
          <List title="Acceptance criteria" items={run.planning.acceptance_criteria.map((x) => `${x.id} — ${x.statement}`)} />
          {run.architecture && <><article><h3>Architecture · Summary</h3><p>{run.architecture.summary}</p></article><List title="Components" items={run.architecture.affected_components} /><List title="Architecture decisions" items={run.architecture.decisions.map((x) => `${x.id}: ${x.title} — ${x.decision}`)} /><List title="Security controls" items={run.architecture.security_controls} /></>}
          {run.engineering && <><article><h3>Engineering · Proposed change set</h3><p>{run.engineering.summary}</p><p><b>Isolated branch:</b> {run.engineering.branch_name}</p></article><List title="Files" items={run.engineering.files.map((x) => `${x.operation.toUpperCase()} ${x.path} — ${x.purpose}`)} /><List title="Tests required" items={run.engineering.tests_required} /></>}
        </div>}
      </div>
    </section>
  </main>;
}

function List({ title, items }: { title: string; items: string[] }) { return <article><h3>{title}</h3><ul>{items.map((item) => <li key={item}>{item}</li>)}</ul></article>; }
