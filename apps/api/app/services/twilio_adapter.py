from __future__ import annotations

from xml.sax.saxutils import escape


def build_twiml_reply(message: str) -> str:
    safe_message = escape(message)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f"<Say voice=\"Polly.Joanna\">{safe_message}</Say>"
        "<Pause length=\"1\"/>"
        "<Gather input=\"speech\" actionOnEmptyResult=\"true\" method=\"POST\" timeout=\"4\" />"
        "</Response>"
    )
