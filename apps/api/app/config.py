from pydantic import BaseModel
import os


class Settings(BaseModel):
    business_name: str = os.getenv("BUSINESS_NAME", "Cascade Home Services")
    disclosure_line: str = os.getenv(
        "DISCLOSURE_LINE",
        "Hi, this is an AI calling assistant from Cascade Home Services on a recorded sales call.",
    )
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    openai_realtime_model: str = os.getenv("OPENAI_REALTIME_MODEL", "gpt-realtime-1.5")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_live_model: str = os.getenv(
        "GEMINI_LIVE_MODEL",
        "gemini-2.5-flash-native-audio-preview-12-2025",
    )
    quiet_hours_start: int = int(os.getenv("QUIET_HOURS_START", "9"))
    quiet_hours_end: int = int(os.getenv("QUIET_HOURS_END", "20"))


settings = Settings()
