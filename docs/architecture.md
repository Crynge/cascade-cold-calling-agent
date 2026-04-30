# Architecture

## Product shape

The repo is built around one operator workflow:

1. choose a lead
2. start a simulated or live-ready call session
3. let the orchestrator decide which model should answer
4. inspect compliance state, routing trace, and next action
5. export or speak the answer through telephony

## Backend layers

### `providers/`

- `OpenAIProvider`
  - uses the OpenAI API when `OPENAI_API_KEY` is present
  - otherwise falls back to deterministic local generation while preserving provider identity
- `GeminiProvider`
  - uses the Gemini API when `GEMINI_API_KEY` is present
  - otherwise falls back the same way

### `services/compliance.py`

Per-turn policy gates:

- DNC and consent checks
- quiet hours
- mandatory disclosure enforcement
- opt-out detection
- high-risk claims detection

### `services/cascade.py`

The route planner decides:

- current stage
- primary provider
- escalation triggers
- fallback provider
- human handoff conditions

### `services/twilio_adapter.py`

Generates deploy-ready TwiML-like XML responses so the repo can be connected to outbound PSTN flows later without rewriting the core logic.

## Frontend

The operator console is intentionally styled like a command center instead of a generic admin page. It emphasizes:

- cascade routing visibility
- compliance state
- lead context
- simulated turn execution
- recent provider traces

## Verification model

Local verification covers:

- route selection
- policy blocking
- API contract correctness
- UI rendering and simulation workflow

It does not claim to verify:

- production call deliverability
- telecom carrier behavior
- regional telemarketing law compliance for every jurisdiction
- real paid API quota behavior
