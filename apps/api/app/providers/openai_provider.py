from __future__ import annotations

import json
import httpx

from .base import BaseProvider, ProviderOutput, ProviderPrompt
from .mock_llm import build_mock_output
from ..config import settings
from ..schemas import CallStage, ProviderName


class OpenAIProvider(BaseProvider):
    provider_name = ProviderName.OPENAI
    model_name = settings.openai_model

    def generate(self, prompt: ProviderPrompt) -> ProviderOutput:
        if not settings.openai_api_key:
            fallback = build_mock_output(self.provider_name, self.model_name, prompt)
            fallback.route_reason = "OpenAI API key absent; deterministic local fallback used."
            return fallback

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a compliance-first B2C cold calling assistant. "
                        "Return strict JSON only with keys: reply, next_stage, confidence, "
                        "disposition, call_risk, follow_up_action."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "stage": prompt.stage.value,
                            "business_name": prompt.business_name,
                            "disclosure_line": prompt.disclosure_line,
                            "lead": prompt.lead.model_dump(),
                            "transcript": prompt.transcript,
                            "customer_text": prompt.customer_text,
                            "goal": prompt.call_goal,
                        }
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "call_turn",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "reply": {"type": "string"},
                            "next_stage": {"type": "string"},
                            "confidence": {"type": "number"},
                            "disposition": {"type": "string"},
                            "call_risk": {"type": "string"},
                            "follow_up_action": {"type": "string"},
                        },
                        "required": [
                            "reply",
                            "next_stage",
                            "confidence",
                            "disposition",
                            "call_risk",
                            "follow_up_action",
                        ],
                        "additionalProperties": False,
                    },
                    "strict": True,
                },
            },
        }

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=30) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)

        return ProviderOutput(
            provider=self.provider_name,
            model=self.model_name,
            reply=parsed["reply"],
            next_stage=CallStage(parsed["next_stage"]),
            confidence=float(parsed["confidence"]),
            disposition=parsed["disposition"],
            call_risk=parsed["call_risk"],
            follow_up_action=parsed["follow_up_action"],
            route_reason="OpenAI handled a high-sensitivity or escalated turn.",
            used_fallback=False,
        )
