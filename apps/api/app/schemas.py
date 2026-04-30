from __future__ import annotations

from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class ProviderName(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    LOCAL = "local"


class CallStage(str, Enum):
    OPENER = "opener"
    DISCOVERY = "discovery"
    OBJECTION = "objection"
    QUALIFICATION = "qualification"
    CLOSE = "close"
    HANDOFF = "handoff"
    SUMMARY = "summary"
    STOPPED = "stopped"


class LeadProfile(BaseModel):
    id: str
    full_name: str
    local_hour: int
    phone: str
    city: str
    state: str
    interest: str
    budget_band: str
    consent_status: Literal["consented", "unknown", "revoked"]
    do_not_call: bool = False
    persona: str
    notes: str = ""


class ConversationTurn(BaseModel):
    speaker: Literal["agent", "customer", "system"]
    text: str


class ComplianceResult(BaseModel):
    allowed: bool
    risk_level: Literal["low", "medium", "high", "blocked"]
    reasons: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)


class ProviderTrace(BaseModel):
    provider: ProviderName
    model: str
    confidence: float
    used_fallback: bool = False
    route_reason: str


class AgentReply(BaseModel):
    reply: str
    next_stage: CallStage
    disposition: Literal["continue", "book_followup", "handoff", "stop"]
    confidence: float
    call_risk: Literal["low", "medium", "high"]
    follow_up_action: str
    route_trace: list[ProviderTrace]


class CallSession(BaseModel):
    session_id: str
    lead: LeadProfile
    stage: CallStage
    started: bool = False
    turns: list[ConversationTurn] = Field(default_factory=list)
    route_trace: list[ProviderTrace] = Field(default_factory=list)
    compliance: ComplianceResult
    latest_reply: str = ""
    latest_disposition: str = "continue"
    summary_note: str = ""


class StartSessionRequest(BaseModel):
    lead_id: str


class RespondRequest(BaseModel):
    callee_text: str


class SessionView(BaseModel):
    session: CallSession
    agent_reply: AgentReply | None = None


class DashboardMetric(BaseModel):
    label: str
    value: str
    tone: Literal["primary", "neutral", "warning"]


class DashboardSummary(BaseModel):
    repo_name: str
    narrative: str
    metrics: list[DashboardMetric]
    leads: list[LeadProfile]
    provider_defaults: dict[str, str]
    compliance_rules: list[str]
    cascade_map: list[dict[str, str]]


class CallPlanResponse(BaseModel):
    lead: LeadProfile
    opening_line: str
    recommended_provider: ProviderName
    escalation_provider: ProviderName
    compliance: ComplianceResult
    notes: list[str]
