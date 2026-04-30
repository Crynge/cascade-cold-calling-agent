from apps.api.app.data import get_lead
from apps.api.app.schemas import CallSession, CallStage, ComplianceResult, ConversationTurn
from apps.api.app.services.cascade import CascadeOrchestrator


def build_session(lead_id: str) -> CallSession:
    lead = get_lead(lead_id)
    return CallSession(
        session_id="session-test",
        lead=lead,
        stage=CallStage.OPENER,
        started=True,
        turns=[
            ConversationTurn(
                speaker="agent",
                text="Hi, this is an AI calling assistant from Cascade Home Services on a recorded sales call.",
            )
        ],
        route_trace=[],
        compliance=ComplianceResult(allowed=True, risk_level="low"),
    )


def test_dnc_lead_blocks_immediately() -> None:
    lead = get_lead("lead-003")
    blocked = CallSession(
        session_id="blocked",
        lead=lead,
        stage=CallStage.OPENER,
        started=True,
        turns=[],
        route_trace=[],
        compliance=ComplianceResult(allowed=True, risk_level="low"),
    )
    orchestrator = CascadeOrchestrator()
    reply = orchestrator.next_turn(blocked, "hello")
    assert reply.disposition == "stop"
    assert reply.next_stage == CallStage.STOPPED


def test_gemini_handles_opener_path_by_default() -> None:
    session = build_session("lead-001")
    orchestrator = CascadeOrchestrator()
    reply = orchestrator.next_turn(session, "yes, what is this about?")
    assert reply.route_trace[0].provider.value == "gemini"
    assert reply.next_stage in {CallStage.QUALIFICATION, CallStage.DISCOVERY}


def test_openai_escalation_for_pricing_objection() -> None:
    session = build_session("lead-002")
    session.stage = CallStage.DISCOVERY
    orchestrator = CascadeOrchestrator()
    reply = orchestrator.next_turn(session, "What does this cost and what ROI can I expect?")
    providers = [trace.provider.value for trace in reply.route_trace]
    assert providers[0] == "openai"
    assert reply.call_risk in {"medium", "high", "low"}
