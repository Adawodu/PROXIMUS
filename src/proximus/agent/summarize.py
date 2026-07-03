"""Best-effort post-call summarization via the Anthropic API."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from proximus.config import get_settings
from proximus.context.calls import CallTranscriptEntry

logger = logging.getLogger(__name__)

# Fast, cheap model — a screening-call summary is a short, non-latency-sensitive
# task, so Haiku is the right tier.
_SUMMARY_MODEL = "claude-haiku-4-5"

_SYSTEM_PROMPT = (
    "You summarize recruiter screening phone calls. Given a transcript, produce a "
    "concise summary (2-4 sentences) covering what was discussed, the candidate's "
    "key points, and any agreed follow-ups. Be factual; do not invent details."
)


def generate_call_summary(
    transcript: Sequence[CallTranscriptEntry],
    candidate_name: str,
) -> str | None:
    """Generate a short summary of a call transcript.

    Returns None (never raises) if summarization is unavailable — no API key,
    empty transcript, or any API error — so callers can treat it as optional.
    """
    settings = get_settings()
    api_key = settings.anthropic_api_key.get_secret_value()
    if not api_key or not transcript:
        return None

    conversation = "\n".join(f"{e.role}: {e.text}" for e in transcript)
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key, timeout=15.0)
        response = client.messages.create(
            model=_SUMMARY_MODEL,
            max_tokens=300,
            system=_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Screening call with {candidate_name}. Transcript:\n\n"
                        f"{conversation}\n\nSummarize this call."
                    ),
                }
            ],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        return text or None
    except Exception as exc:  # noqa: BLE001 — summary is best-effort
        logger.warning(f"Call summary generation failed: {exc}")
        return None
