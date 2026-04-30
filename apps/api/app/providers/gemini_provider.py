from __future__ import annotations

import json
import httpx

from .base import BaseProvider, ProviderOutput, ProviderPrompt
from .mock_llm import build_mock_output
from ..config import settings
from ..schemas import CallStage, ProviderName


class GeminiProvider(BaseProvider):
    provider_name = ProviderName.GEMINI
    model_name = settings.gemini_model

    def generate(self, prompt: ProviderPrompt) -> ProviderOutput:
        if not settings.gemini_api_key:
            fallback = build_mock_output(self.provider_name, self.model_name, prompt)
            fallback.route_reason = "Gemini API key absent; deterministic local fallback used."
            return fallback

        request_body = {
            "system_instruction": {
                "parts": [
                    {
                        "text": (
                            "You are a compliance-first B2C cold calling assistant. "
                            "Return strict JSON only with keys: reply, next_stage, confidence, "
                            "disposition, call_risk, follow_up_action."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "stage": prompt.stage.value,
                                    "business_name": prompt.business_name,
                                    "disclosure_line": prompt.disclosure_line,
                                    "lead": prompt.lead.model_dump(),
                                    "transcript": prompt.transcript,
                                    "customer_text": prompt.customer_text,
                                    "goal": prompt.call_goal,
                                }
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
            },
        }

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"
            f"?key={settings.gemini_api_key}"
        )

        with httpx.Client(timeout=30) as client:
            response = client.post(url, json=request_body)
            response.raise_for_status()
            parts = response.json()["candidates"][0]["content"]["parts"]
            parsed = json.loads(parts[0]["text"])

        return ProviderOutput(
            provider=self.provider_name,
            model=self.model_name,
            reply=parsed["reply"],
            next_stage=CallStage(parsed["next_stage"]),
            confidence=float(parsed["confidence"]),
            disposition=parsed["disposition"],
            call_risk=parsed["call_risk"],
            follow_up_action=parsed["follow_up_action"],
            route_reason="Gemini handled a low-latency or lower-cost turn.",
            used_fallback=False,
        )
