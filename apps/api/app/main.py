from __future__ import annotations

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .data import SAMPLE_LEADS, get_lead
from .schemas import (
    CallPlanResponse,
    ConversationTurn,
    DashboardMetric,
    DashboardSummary,
    SessionView,
    StartSessionRequest,
    RespondRequest,
)
from .services.cascade import CascadeOrchestrator
from .services.compliance import evaluate_compliance
from .services.store import SessionStore
from .services.twilio_adapter import build_twiml_reply

app = FastAPI(title="Cascade Cold Calling Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = SessionStore()
orchestrator = CascadeOrchestrator()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary() -> DashboardSummary:
    return DashboardSummary(
        repo_name="cascade-cold-calling-agent",
        narrative=(
            "A compliance-first outbound sales agent that routes low-cost turns through Gemini "
            "and escalates sensitive turns to OpenAI."
        ),
        metrics=[
            DashboardMetric(label="Primary low-cost engine", value="Gemini 2.5 Flash", tone="primary"),
            DashboardMetric(label="Escalation engine", value="OpenAI GPT-5.4 mini", tone="primary"),
            DashboardMetric(label="Blocked lead ratio", value="1 / 3 demo leads", tone="warning"),
            DashboardMetric(label="Verification mode", value="Simulator + smoke test", tone="neutral"),
        ],
        leads=SAMPLE_LEADS,
        provider_defaults={
            "openai_text": settings.openai_model,
            "openai_realtime": settings.openai_realtime_model,
            "gemini_text": settings.gemini_model,
            "gemini_live": settings.gemini_live_model,
        },
        compliance_rules=[
            "Block DNC and revoked-consent leads",
            "Block calls outside local quiet hours",
            "Require recorded-sales disclosure in opening line",
            "Stop immediately on opt-out language",
        ],
        cascade_map=[
            {"stage": "opener", "primary": "gemini", "fallback": "openai"},
            {"stage": "discovery", "primary": "gemini", "fallback": "openai"},
            {"stage": "objection", "primary": "openai", "fallback": "gemini"},
            {"stage": "close/handoff", "primary": "openai", "fallback": "gemini"},
        ],
    )


@app.post("/api/call-plan", response_model=CallPlanResponse)
def call_plan(request: StartSessionRequest) -> CallPlanResponse:
    try:
        lead = get_lead(request.lead_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    compliance = evaluate_compliance(lead, [])
    notes = [
        "Lead interest should be acknowledged without over-claiming outcomes.",
        "Keep the first turn permission-based and brief.",
        "Escalate pricing or legal objections to the OpenAI path.",
    ]

    return CallPlanResponse(
        lead=lead,
        opening_line=orchestrator.build_opening_line(lead),
        recommended_provider="gemini",
        escalation_provider="openai",
        compliance=compliance,
        notes=notes,
    )


@app.post("/api/sessions", response_model=SessionView)
def start_session(request: StartSessionRequest) -> SessionView:
    try:
        lead = get_lead(request.lead_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    compliance = evaluate_compliance(lead, [])
    session = store.create(lead, compliance)

    opening_line = orchestrator.build_opening_line(lead)
    session.turns.append(ConversationTurn(speaker="agent", text=opening_line))
    session.started = True
    session.latest_reply = opening_line
    store.save(session)

    return SessionView(session=session, agent_reply=None)


@app.post("/api/sessions/{session_id}/respond", response_model=SessionView)
def respond(session_id: str, request: RespondRequest) -> SessionView:
    try:
        session = store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    session.turns.append(ConversationTurn(speaker="customer", text=request.callee_text))
    reply = orchestrator.next_turn(session, request.callee_text)

    session.turns.append(ConversationTurn(speaker="agent", text=reply.reply))
    session.stage = reply.next_stage
    session.route_trace = reply.route_trace
    session.latest_reply = reply.reply
    session.latest_disposition = reply.disposition
    session.summary_note = reply.follow_up_action
    store.save(session)

    return SessionView(session=session, agent_reply=reply)


@app.post("/api/twilio/twiml/{session_id}")
def twiml(session_id: str) -> Response:
    try:
        session = store.get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(
        content=build_twiml_reply(session.latest_reply or orchestrator.build_opening_line(session.lead)),
        media_type="application/xml",
    )
