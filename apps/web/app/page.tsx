"use client";

import { FormEvent, useState } from "react";

type Criterion = { id: string; statement: string };
type Plan = {
  business_objective: string;
  scope: string[];
  assumptions: string[];
  functional_requirements: string[];
  non_functional_requirements: string[];
  acceptance_criteria: Criterion[];
  dependencies: string[];
  risks: string[];
  implementation_tasks: string[];
};
type Run = {
  id: string;
  original_request: string;
  status: string;
  provider: string;
  model: string;
  planning: Plan | null;
};

const example =
  "Add customer churn forecasting to our SaaS product and expose the results through the mobile app.";

export default function Home() {
  const [request, setRequest] = useState(example);
  const [run, setRun] = useState<Run | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetch("http://localhost:8000/api/v1/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request }),
      });
      if (!response.ok) throw new Error(`Planning failed (${response.status})`);
      setRun(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <header>
        <div>
          <p className="eyebrow">AI-NATIVE ENGINEERING</p>
          <h1>Command Center</h1>
          <p className="subtitle">Bounded autonomous engineering with auditable human control.</p>
        </div>
        <span className="status">MILESTONE 1 · MOCK MODE</span>
      </header>

      <section className="pipeline" aria-label="Engineering workflow">
        {[
          "Product Request",
          "Planning",
          "Architecture",
          "Engineering",
          "QA + Security",
          "Review",
          "Human Approval",
          "Deploy",
        ].map((stage, index) => (
          <div className={index < 2 ? "stage active" : "stage"} key={stage}>
            <span>{String(index + 1).padStart(2, "0")}</span>{stage}
          </div>
        ))}
      </section>

      <section className="workspace">
        <form className="panel request" onSubmit={submit}>
          <p className="label">FOUNDER / PRODUCT REQUEST</p>
          <textarea value={request} onChange={(event) => setRequest(event.target.value)} />
          <button disabled={loading || request.trim().length < 10}>
            {loading ? "Planning…" : "Start Engineering Workflow"}
          </button>
          {error && <p className="error">{error}</p>}
          <div className="guardrail">
            <strong>Governance:</strong> Mock mode makes no paid model calls and no production changes.
          </div>
        </form>

        <div className="panel output">
          <div className="outputHeader">
            <div>
              <p className="label">PLANNING AGENT OUTPUT</p>
              <h2>{run ? run.status.toUpperCase() : "WAITING FOR REQUEST"}</h2>
            </div>
            {run && <code>{run.provider}/{run.model}</code>}
          </div>

          {!run?.planning ? (
            <div className="empty">Submit a product request to create structured, traceable planning artifacts.</div>
          ) : (
            <div className="plan">
              <article>
                <h3>Business objective</h3>
                <p>{run.planning.business_objective}</p>
              </article>
              <List title="Functional requirements" items={run.planning.functional_requirements} />
              <article>
                <h3>Acceptance criteria</h3>
                <ul>{run.planning.acceptance_criteria.map((item) => <li key={item.id}><b>{item.id}</b> {item.statement}</li>)}</ul>
              </article>
              <List title="Dependencies" items={run.planning.dependencies} />
              <List title="Risks" items={run.planning.risks} />
              <List title="Implementation tasks" items={run.planning.implementation_tasks} />
            </div>
          )}
        </div>
      </section>
    </main>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return <article><h3>{title}</h3><ul>{items.map((item) => <li key={item}>{item}</li>)}</ul></article>;
}
