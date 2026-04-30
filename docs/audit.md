# Audit

## Scope

Audit target: `cascade-cold-calling-agent`

## Required checks

- backend unit and API tests
- frontend production build
- end-to-end browser smoke over live local servers
- repo-readiness review for docs and CI

## Expected commands

```bash
python -m pytest tests -q
npm run build:web
python -m playwright install chromium
python C:/Users/samee/.codex/skills/webapp-testing/scripts/with_server.py --server "python -m uvicorn apps.api.app.main:app --port 8000" --port 8000 --server "npm --workspace apps/web run dev -- --host 127.0.0.1 --port 5173" --port 5173 -- python tests/web_smoke.py
```

## Results

- `python -m pip install -r apps/api/requirements.txt`: passed
- `npm install`: passed
- `python -m pytest tests -q`: passed with `6/6`
- `npm run build:web`: passed
- `python -m playwright install chromium`: passed
- `python C:/Users/samee/.codex/skills/webapp-testing/scripts/with_server.py --server "python -m uvicorn apps.api.app.main:app --port 8000" --port 8000 --server "npm --workspace apps/web run dev -- --host 127.0.0.1 --port 5173" --port 5173 -- python tests/web_smoke.py`: passed

## Smoke artifact

- Playwright screenshot generated at `tests/artifacts/cascade-dashboard-smoke.png`

## Notes

- The provider adapters are locally verified in deterministic fallback mode unless real OpenAI and Gemini keys are present.
- Telephony delivery is represented through TwiML generation rather than a live PSTN audit, which would require external carrier credentials and real outbound calling infrastructure.
