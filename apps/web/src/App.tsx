import { startTransition, useDeferredValue, useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type LeadProfile = {
  id: string;
  full_name: string;
  local_hour: number;
  city: string;
  state: string;
  interest: string;
  budget_band: string;
  consent_status: "consented" | "unknown" | "revoked";
  do_not_call: boolean;
  persona: string;
  notes: string;
};

type DashboardMetric = {
  label: string;
  value: string;
  tone: "primary" | "neutral" | "warning";
};

type DashboardSummary = {
  repo_name: string;
  narrative: string;
  metrics: DashboardMetric[];
  leads: LeadProfile[];
  provider_defaults: Record<string, string>;
  compliance_rules: string[];
  cascade_map: Array<Record<string, string>>;
};

type ComplianceResult = {
  allowed: boolean;
  risk_level: "low" | "medium" | "high" | "blocked";
  reasons: string[];
  missing_requirements: string[];
};

type ProviderTrace = {
  provider: "gemini" | "openai" | "local";
  model: string;
  confidence: number;
  route_reason: string;
  used_fallback: boolean;
};

type ConversationTurn = {
  speaker: "agent" | "customer" | "system";
  text: string;
};

type SessionPayload = {
  session_id: string;
  lead: LeadProfile;
  stage: string;
  turns: ConversationTurn[];
  compliance: ComplianceResult;
  latest_reply: string;
  latest_disposition: string;
  summary_note: string;
  route_trace: ProviderTrace[];
};

type AgentReply = {
  reply: string;
  next_stage: string;
  disposition: string;
  confidence: number;
  call_risk: "low" | "medium" | "high";
  follow_up_action: string;
  route_trace: ProviderTrace[];
};

type SessionView = {
  session: SessionPayload;
  agent_reply: AgentReply | null;
};

type CallPlan = {
  opening_line: string;
  recommended_provider: string;
  escalation_provider: string;
  compliance: ComplianceResult;
  notes: string[];
};

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`GET ${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`POST ${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function App() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [activeLeadId, setActiveLeadId] = useState("lead-001");
  const [callPlan, setCallPlan] = useState<CallPlan | null>(null);
  const [sessionView, setSessionView] = useState<SessionView | null>(null);
  const [composer, setComposer] = useState("I am interested but what does this cost?");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const deferredComposer = useDeferredValue(composer);

  useEffect(() => {
    void (async () => {
      try {
        const dashboard = await apiGet<DashboardSummary>("/api/dashboard/summary");
        startTransition(() => {
          setSummary(dashboard);
        });
      } catch (fetchError) {
        setError(fetchError instanceof Error ? fetchError.message : "Unable to load summary.");
      }
    })();
  }, []);

  useEffect(() => {
    if (!activeLeadId) {
      return;
    }

    void (async () => {
      try {
        const plan = await apiPost<CallPlan>("/api/call-plan", { lead_id: activeLeadId });
        startTransition(() => {
          setCallPlan(plan);
        });
      } catch (fetchError) {
        setError(fetchError instanceof Error ? fetchError.message : "Unable to load plan.");
      }
    })();
  }, [activeLeadId]);

  async function launchSimulator(): Promise<void> {
    setLoading(true);
    setError(null);
    try {
      const session = await apiPost<SessionView>("/api/sessions", { lead_id: activeLeadId });
      startTransition(() => {
        setSessionView(session);
      });
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Unable to start session.");
    } finally {
      setLoading(false);
    }
  }

  async function runNextTurn(): Promise<void> {
    if (!sessionView) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const nextSession = await apiPost<SessionView>(
        `/api/sessions/${sessionView.session.session_id}/respond`,
        { callee_text: composer },
      );
      startTransition(() => {
        setSessionView(nextSession);
      });
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Unable to run next turn.");
    } finally {
      setLoading(false);
    }
  }

  const activeLead = summary?.leads.find((lead) => lead.id === activeLeadId) ?? null;
  const routeTrace = sessionView?.agent_reply?.route_trace ?? [];
  const complianceReasons =
    sessionView?.session.compliance.reasons.length
      ? sessionView.session.compliance.reasons
      : callPlan?.compliance.reasons.length
        ? callPlan.compliance.reasons
        : summary?.compliance_rules ?? [];
  const missingRequirements =
    sessionView?.session.compliance.missing_requirements ??
    callPlan?.compliance.missing_requirements ??
    [];

  return (
    <div className="shell">
      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">B2C outbound AI orchestration / compliance-first / cascade mode</p>
          <h1>Cascade Cold Calling Agent</h1>
          <p className="hero-body">
            A dual-provider cold-calling stack that routes fast, lower-cost turns through Gemini and escalates
            sensitive turns into OpenAI when confidence, pricing pressure, or compliance risk rises.
          </p>
        </div>

        <div className="hero-actions">
          <button type="button" className="primary-action" onClick={() => void launchSimulator()}>
            Launch Simulator
          </button>
          <div className="api-badge">
            <span>OpenAI</span>
            <span>Gemini</span>
            <span>Twilio-ready</span>
          </div>
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <main className="grid">
        <section className="main-column">
          <section className="panel intro-panel">
            <div className="section-header">
              <span>Control narrative</span>
              <strong>{summary?.repo_name ?? "loading..."}</strong>
            </div>
            <p>{summary?.narrative ?? "Loading dashboard summary..."}</p>
            <div className="metrics-grid">
              {summary?.metrics.map((metric) => (
                <article key={metric.label} className={`metric-card metric-${metric.tone}`}>
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                </article>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="section-header">
              <span>Lead selector</span>
              <strong>{activeLead?.full_name ?? "Choose a lead"}</strong>
            </div>
            <div className="lead-grid">
              {summary?.leads.map((lead) => (
                <button
                  type="button"
                  key={lead.id}
                  className={`lead-card ${lead.id === activeLeadId ? "lead-card-active" : ""}`}
                  onClick={() => setActiveLeadId(lead.id)}
                >
                  <span className="lead-status">{lead.do_not_call ? "Blocked lead" : `${lead.city}, ${lead.state}`}</span>
                  <strong>{lead.full_name}</strong>
                  <p>{lead.interest}</p>
                  <small>{lead.persona}</small>
                </button>
              ))}
            </div>
          </section>

          <section className="panel simulator-panel">
            <div className="section-header">
              <span>Simulator console</span>
              <strong>{sessionView ? sessionView.session.stage : "No session yet"}</strong>
            </div>

            <div className="sim-layout">
              <div className="transcript-card">
                <h2>Conversation stream</h2>
                <div className="transcript-feed">
                  {sessionView?.session.turns.length ? (
                    sessionView.session.turns.map((turn, index) => (
                      <article key={`${turn.speaker}-${index}`} className={`bubble bubble-${turn.speaker}`}>
                        <span>{turn.speaker}</span>
                        <p>{turn.text}</p>
                      </article>
                    ))
                  ) : (
                    <div className="empty-state">
                      Start the simulator to generate the disclosure opener and test the cascade router.
                    </div>
                  )}
                </div>
              </div>

              <div className="sim-actions">
                <h2>Operator input</h2>
                <textarea
                  value={composer}
                  onChange={(event) => setComposer(event.target.value)}
                  placeholder="Type the callee response here..."
                />
                <button type="button" className="secondary-action" onClick={() => void runNextTurn()} disabled={!sessionView || loading}>
                  Run Next Turn
                </button>
                <div className="hint-box">
                  <span>Deferred preview</span>
                  <p>{deferredComposer}</p>
                </div>
              </div>
            </div>
          </section>
        </section>

        <aside className="rail">
          <section className="panel">
            <div className="section-header">
              <span>Cascade route</span>
              <strong>Live provider trace</strong>
            </div>
            <div className="trace-list">
              {routeTrace.length ? (
                routeTrace.map((trace, index) => (
                  <article key={`${trace.provider}-${index}`} className="trace-card">
                    <div className="trace-topline">
                      <strong>
                        {trace.provider === "openai"
                          ? "OpenAI escalation"
                          : trace.provider === "gemini"
                            ? "Gemini primary"
                            : "Local policy engine"}
                      </strong>
                      <span>{Math.round(trace.confidence * 100)}%</span>
                    </div>
                    <p>{trace.model}</p>
                    <small>{trace.route_reason}</small>
                  </article>
                ))
              ) : (
                <article className="trace-card">
                  <div className="trace-topline">
                    <strong>{callPlan?.recommended_provider === "gemini" ? "Gemini primary" : "OpenAI primary"}</strong>
                    <span>84%</span>
                  </div>
                  <p>{callPlan?.recommended_provider ?? "gemini"}</p>
                  <small>Initial planning route based on stage and cost profile.</small>
                </article>
              )}
            </div>
          </section>

          <section className="panel">
            <div className="section-header">
              <span>Compliance watch</span>
              <strong>{sessionView?.session.compliance.risk_level ?? callPlan?.compliance.risk_level ?? "low"}</strong>
            </div>
            <div className="compliance-stack">
              <div className={`risk-pill risk-${sessionView?.session.compliance.risk_level ?? callPlan?.compliance.risk_level ?? "low"}`}>
                {(sessionView?.session.compliance.allowed ?? callPlan?.compliance.allowed) === false ? "Blocked" : "Allowed"}
              </div>
              <ul>
                {complianceReasons.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
              {missingRequirements.length ? (
                <>
                  <h3>Missing requirements</h3>
                  <ul>
                    {missingRequirements.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </>
              ) : null}
            </div>
          </section>

          <section className="panel">
            <div className="section-header">
              <span>Lead brief</span>
              <strong>{activeLead?.budget_band ?? "n/a"}</strong>
            </div>
            <div className="brief-stack">
              <p><strong>Interest:</strong> {activeLead?.interest}</p>
              <p><strong>Consent:</strong> {activeLead?.consent_status}</p>
              <p><strong>Local hour:</strong> {activeLead?.local_hour ?? "--"}:00</p>
              <p><strong>Notes:</strong> {activeLead?.notes}</p>
            </div>
          </section>

          <section className="panel">
            <div className="section-header">
              <span>Call plan</span>
              <strong>Provider-first opening</strong>
            </div>
            <p className="plan-line">{callPlan?.opening_line ?? "Loading opening line..."}</p>
            <ul className="plan-list">
              {(callPlan?.notes ?? []).map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          </section>
        </aside>
      </main>
    </div>
  );
}

export default App;
