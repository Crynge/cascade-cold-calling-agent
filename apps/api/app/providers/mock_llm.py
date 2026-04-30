from __future__ import annotations

from .base import ProviderOutput, ProviderPrompt
from ..schemas import CallStage, ProviderName


def build_mock_output(
    provider: ProviderName,
    model_name: str,
    prompt: ProviderPrompt,
) -> ProviderOutput:
    customer_text = prompt.customer_text.lower().strip()
    lead_first_name = prompt.lead.full_name.split()[0]

    if prompt.stage == CallStage.OPENER:
        reply = (
            f"{prompt.disclosure_line} I am reaching out because you showed interest in "
            f"{prompt.lead.interest}. Do you have 30 seconds so I can see whether this is relevant for {lead_first_name}?"
        )
        return ProviderOutput(
            provider=provider,
            model=model_name,
            reply=reply,
            next_stage=CallStage.DISCOVERY,
            confidence=0.86,
            disposition="continue",
            call_risk="low",
            follow_up_action="Ask one permission-based discovery question.",
            route_reason="Permission-based opener with required disclosure.",
            used_fallback=True,
        )

    if any(token in customer_text for token in ["stop", "remove", "do not call", "unsubscribe"]):
        return ProviderOutput(
            provider=provider,
            model=model_name,
            reply="Understood. I will mark this number as do-not-call and end the conversation now.",
            next_stage=CallStage.STOPPED,
            confidence=0.99,
            disposition="stop",
            call_risk="low",
            follow_up_action="Persist DNC flag and suppress future campaigns.",
            route_reason="Customer requested opt-out.",
            used_fallback=True,
        )

    if any(token in customer_text for token in ["price", "cost", "expensive", "roi", "worth"]):
        return ProviderOutput(
            provider=provider,
            model=model_name,
            reply=(
                f"That makes sense. Instead of guessing on price, I can qualify what matters most to you "
                f"and then offer either a quick ballpark or a callback with a specialist. Which would you prefer?"
            ),
            next_stage=CallStage.OBJECTION,
            confidence=0.78,
            disposition="continue",
            call_risk="medium",
            follow_up_action="Handle pricing objection and offer specialist handoff if requested.",
            route_reason="Pricing objection detected.",
            used_fallback=True,
        )

    if any(token in customer_text for token in ["not interested", "busy", "later"]):
        return ProviderOutput(
            provider=provider,
            model=model_name,
            reply=(
                "No problem. Before I let you go, would a short callback window later this week be better, "
                "or should I close this out for now?"
            ),
            next_stage=CallStage.HANDOFF,
            confidence=0.74,
            disposition="book_followup",
            call_risk="low",
            follow_up_action="Offer callback or gracefully end the call.",
            route_reason="Soft objection detected.",
            used_fallback=True,
        )

    if any(token in customer_text for token in ["yes", "sure", "okay", "go ahead", "interested"]):
        return ProviderOutput(
            provider=provider,
            model=model_name,
            reply=(
                f"Great. For {prompt.lead.interest}, what matters more right now: monthly savings, speed of setup, or long-term reliability?"
            ),
            next_stage=CallStage.QUALIFICATION,
            confidence=0.84,
            disposition="continue",
            call_risk="low",
            follow_up_action="Collect one buying signal and continue qualification.",
            route_reason="Positive engagement detected.",
            used_fallback=True,
        )

    return ProviderOutput(
        provider=provider,
        model=model_name,
        reply=(
            "I want to keep this brief. Would you like a 15-second summary of the offer, or should I schedule a better time?"
        ),
        next_stage=CallStage.DISCOVERY,
        confidence=0.67,
        disposition="continue",
        call_risk="low",
        follow_up_action="Clarify interest without pressuring the customer.",
        route_reason="Neutral customer response.",
        used_fallback=True,
    )
