from __future__ import annotations

from ..config import settings
from ..providers.base import ProviderOutput, ProviderPrompt
from ..providers.gemini_provider import GeminiProvider
from ..providers.openai_provider import OpenAIProvider
from ..schemas import (
    AgentReply,
    CallSession,
    CallStage,
    LeadProfile,
    ProviderName,
    ProviderTrace,
)
from .compliance import evaluate_compliance


class CascadeOrchestrator:
    def __init__(self) -> None:
        self.gemini = GeminiProvider()
        self.openai = OpenAIProvider()

    def build_opening_line(self, lead: LeadProfile) -> str:
        return (
            f"{settings.disclosure_line} We noticed possible interest in {lead.interest}. "
            "Do you have half a minute to see whether this is relevant?"
        )

    def next_turn(self, session: CallSession, customer_text: str) -> AgentReply:
        transcript = [turn.model_dump() for turn in session.turns]
        compliance = evaluate_compliance(session.lead, transcript, customer_text)
        session.compliance = compliance

        if not compliance.allowed:
            trace = ProviderTrace(
                provider=ProviderName.LOCAL,
                model="local-policy-engine",
                confidence=1.0,
                used_fallback=False,
                route_reason=", ".join(compliance.reasons) or "Policy engine blocked the turn.",
            )
            return AgentReply(
                reply="I will stop the call and mark the contact accordingly.",
                next_stage=CallStage.STOPPED,
                disposition="stop",
                confidence=1.0,
                call_risk="low",
                follow_up_action="Suppress the lead and end the session.",
                route_trace=[trace],
            )

        stage = session.stage
        customer_text_normalized = customer_text.lower()
        objection_like = any(
            token in customer_text_normalized
            for token in ["price", "cost", "expensive", "busy", "not interested", "roi", "later"]
        )
        high_sensitivity = objection_like or bool(compliance.missing_requirements) or compliance.risk_level == "medium"

        provider_order = (
            [self.openai, self.gemini]
            if stage in {CallStage.OBJECTION, CallStage.CLOSE, CallStage.HANDOFF} or high_sensitivity
            else [self.gemini, self.openai]
        )

        prompt = ProviderPrompt(
            stage=stage,
            lead=session.lead,
            business_name=settings.business_name,
            disclosure_line=settings.disclosure_line,
            transcript=transcript,
            customer_text=customer_text,
            call_goal=f"Convert interest in {session.lead.interest} into a qualified callback or next step.",
        )

        primary_output = provider_order[0].generate(prompt)
        outputs: list[ProviderOutput] = [primary_output]

        should_escalate = (
            primary_output.confidence < 0.72
            or primary_output.call_risk == "high"
            or (primary_output.provider == ProviderName.GEMINI and high_sensitivity)
        )

        selected_output = primary_output
        if should_escalate:
            secondary_output = provider_order[1].generate(prompt)
            outputs.append(secondary_output)
            if secondary_output.confidence >= primary_output.confidence:
                selected_output = secondary_output

        traces = [
            ProviderTrace(
                provider=output.provider,
                model=output.model,
                confidence=output.confidence,
                used_fallback=output.used_fallback,
                route_reason=output.route_reason,
            )
            for output in outputs
        ]

        return AgentReply(
            reply=selected_output.reply,
            next_stage=selected_output.next_stage,
            disposition=selected_output.disposition,  # type: ignore[arg-type]
            confidence=selected_output.confidence,
            call_risk=selected_output.call_risk,  # type: ignore[arg-type]
            follow_up_action=selected_output.follow_up_action,
            route_trace=traces,
        )
