from __future__ import annotations

import uuid
from ..schemas import CallSession, CallStage, ComplianceResult, LeadProfile


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, CallSession] = {}

    def create(self, lead: LeadProfile, compliance: ComplianceResult) -> CallSession:
        session = CallSession(
            session_id=f"session-{uuid.uuid4().hex[:10]}",
            lead=lead,
            stage=CallStage.OPENER,
            started=False,
            turns=[],
            route_trace=[],
            compliance=compliance,
            latest_reply="",
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> CallSession:
        return self._sessions[session_id]

    def save(self, session: CallSession) -> CallSession:
        self._sessions[session.session_id] = session
        return session
