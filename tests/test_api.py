from fastapi.testclient import TestClient

from apps.api.app.main import app


client = TestClient(app)


def test_dashboard_summary() -> None:
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload["repo_name"] == "cascade-cold-calling-agent"
    assert len(payload["leads"]) >= 3


def test_session_flow() -> None:
    start = client.post("/api/sessions", json={"lead_id": "lead-001"})
    assert start.status_code == 200
    session_id = start.json()["session"]["session_id"]

    reply = client.post(
        f"/api/sessions/{session_id}/respond",
        json={"callee_text": "I am interested but what does it cost?"},
    )
    assert reply.status_code == 200
    payload = reply.json()
    assert payload["agent_reply"]["reply"]
    assert payload["session"]["latest_reply"]


def test_blocked_plan_for_dnc_lead() -> None:
    response = client.post("/api/call-plan", json={"lead_id": "lead-003"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["compliance"]["allowed"] is False
