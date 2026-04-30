from __future__ import annotations

from dataclasses import dataclass
from ..schemas import CallStage, LeadProfile, ProviderName


@dataclass
class ProviderPrompt:
    stage: CallStage
    lead: LeadProfile
    business_name: str
    disclosure_line: str
    transcript: list[dict[str, str]]
    customer_text: str
    call_goal: str


@dataclass
class ProviderOutput:
    provider: ProviderName
    model: str
    reply: str
    next_stage: CallStage
    confidence: float
    disposition: str
    call_risk: str
    follow_up_action: str
    route_reason: str
    used_fallback: bool = False


class BaseProvider:
    provider_name: ProviderName
    model_name: str

    def generate(self, prompt: ProviderPrompt) -> ProviderOutput:
        raise NotImplementedError
