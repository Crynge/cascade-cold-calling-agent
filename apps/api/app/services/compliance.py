from __future__ import annotations

from ..config import settings
from ..schemas import ComplianceResult, LeadProfile


OPT_OUT_PHRASES = ["stop", "do not call", "remove me", "unsubscribe", "don't call"]
HIGH_RISK_PHRASES = ["guaranteed return", "government approved", "act now or lose", "risk free forever"]


def evaluate_compliance(
    lead: LeadProfile,
    transcript: list[dict[str, str]],
    customer_text: str = "",
) -> ComplianceResult:
    reasons: list[str] = []
    missing_requirements: list[str] = []

    if lead.do_not_call or lead.consent_status == "revoked":
        reasons.append("Lead is flagged as do-not-call or revoked consent.")
        return ComplianceResult(
            allowed=False,
            risk_level="blocked",
            reasons=reasons,
            missing_requirements=[],
        )

    if lead.local_hour < settings.quiet_hours_start or lead.local_hour >= settings.quiet_hours_end:
        reasons.append("Lead is outside the allowed local calling window.")
        return ComplianceResult(
            allowed=False,
            risk_level="blocked",
            reasons=reasons,
            missing_requirements=[],
        )

    normalized_text = customer_text.lower()
    if any(phrase in normalized_text for phrase in OPT_OUT_PHRASES):
        reasons.append("Customer asked to opt out or end contact.")
        return ComplianceResult(
            allowed=False,
            risk_level="blocked",
            reasons=reasons,
            missing_requirements=[],
        )

    if transcript:
        first_agent_turn = next(
            (turn["text"] for turn in transcript if turn["speaker"] == "agent"),
            "",
        ).lower()
        if "recorded sales call" not in first_agent_turn:
            missing_requirements.append("Opening disclosure must identify the business and recorded sales purpose.")

    if any(phrase in normalized_text for phrase in HIGH_RISK_PHRASES):
        reasons.append("High-risk claim language detected.")

    risk_level = "medium" if reasons or missing_requirements else "low"
    return ComplianceResult(
        allowed=True,
        risk_level=risk_level,
        reasons=reasons,
        missing_requirements=missing_requirements,
    )
