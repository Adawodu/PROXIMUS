"""LiveKit voice agent for handling screening calls."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time

from dotenv import load_dotenv

load_dotenv()

from livekit import agents, rtc
from livekit.agents import Agent, AgentServer, AgentSession, room_io
from livekit.plugins import anthropic, cartesia, deepgram, openai, silero

from proximus.agent.summarize import generate_call_summary
from proximus.config import get_settings
from proximus.context import Resume, ResumeManager
from proximus.context.calls import CallManager, CallRecord, CallTranscriptEntry

logger = logging.getLogger(__name__)

# Default Cartesia TTS voice, used when a resume doesn't specify its own.
DEFAULT_TTS_VOICE = "5ee9feff-1265-424a-9d7f-8e4d431a12c7"


def _add_call_summary(record: CallRecord) -> None:
    """Generate and persist a post-call summary (best-effort, off the event loop)."""
    summary = generate_call_summary(record.transcript, record.candidate_name)
    if summary:
        record.summary = summary
        get_call_manager().save_call(record)
        logger.info(f"Added summary to call {record.id}")


# Global managers - shared across calls
_resume_manager: ResumeManager | None = None
_call_manager: CallManager | None = None


def get_resume_manager() -> ResumeManager:
    """Get or create the global resume manager."""
    global _resume_manager
    if _resume_manager is None:
        _resume_manager = ResumeManager()
    return _resume_manager


def get_call_manager() -> CallManager:
    """Get or create the global call manager."""
    global _call_manager
    if _call_manager is None:
        _call_manager = CallManager()
    return _call_manager


def get_llm():
    """Get the LLM plugin instance based on config."""
    settings = get_settings()
    if settings.ai_provider == "openai":
        return openai.LLM(model=settings.openai_model)
    return anthropic.LLM(model=settings.anthropic_model)


def extract_caller_phone(participant: rtc.RemoteParticipant) -> str | None:
    """Extract the caller's phone number from SIP participant attributes.

    Args:
        participant: The remote participant (SIP caller).

    Returns:
        Phone number if found, None otherwise.
    """
    attrs = participant.attributes
    if not attrs:
        return None

    for key in ["sip.phoneNumber", "sip.callerNumber", "sip.from", "phoneNumber"]:
        if key in attrs:
            return attrs[key]

    return None


class CandidateAgent(Agent):
    """Agent that represents a candidate in a screening call."""

    def __init__(
        self, resume: Resume, direction: str = "inbound", job_detail: str | None = None
    ) -> None:
        instructions = resume.to_system_prompt()
        if job_detail:
            instructions += f"\n\nJOB CONTEXT: The following is the job you are discussing on this call:\n{job_detail}"
        instructions += (
            "\n\nCRITICAL RESPONSE RULES: "
            "Keep every response to 2-3 sentences maximum. Be conversational and concise. "
            "Never give long monologues. Answer the question asked, then stop. "
            "If asked about experience, give one concrete highlight, not a full history."
        )
        if direction == "outbound":
            instructions += (
                "\n\nYou are making an OUTBOUND call to a recruiter. "
                "You initiated this call. Listen carefully and respond naturally. "
                "Let them lead the conversation."
            )
        super().__init__(instructions=instructions)
        self.resume = resume


def resolve_resume(ctx: agents.JobContext) -> Resume:
    """Resolve which resume to use for this call.

    Priority:
    1. Phone number lookup from SIP participant
    2. Resume ID from room metadata
    3. First available resume (fallback for testing)
    4. Default empty resume
    """
    # Priority 0: governed Proof-of-Me persona (opt-in). Overrides everything so the twin
    # only ever speaks from the curated, guardrailed export — never a raw resume.
    gp = get_settings().governed_persona_path
    if gp:
        from proximus.context.governed import load_governed_resume

        try:
            resume = load_governed_resume(gp)
            logger.info(f"Using governed Proof-of-Me persona: {resume.candidate_name}")
            return resume
        except Exception as exc:  # never break a call on a bad path — fall through
            logger.error(f"Governed persona load failed ({gp}): {exc}")

    resume_manager = get_resume_manager()
    # Reload from disk so we pick up resumes added via the API
    resume_manager._load_registry()

    # Priority 1: Look up by caller phone number
    for participant in ctx.room.remote_participants.values():
        caller_phone = extract_caller_phone(participant)
        if caller_phone:
            logger.info(f"Caller phone detected: {caller_phone}")
            resume = resume_manager.get_resume_by_phone(caller_phone)
            if resume:
                logger.info(f"Found resume for phone {caller_phone}: {resume.candidate_name}")
                return resume

    # Priority 2: Resume ID from room metadata
    if ctx.room.metadata:
        try:
            metadata = json.loads(ctx.room.metadata)
            resume_id = metadata.get("resume_id")
        except json.JSONDecodeError:
            resume_id = ctx.room.metadata

        if resume_id:
            resume = resume_manager.get_resume(resume_id)
            if resume:
                logger.info(f"Found resume from metadata: {resume.candidate_name}")
                return resume

    # Priority 3: Any available resume (testing fallback)
    resumes = resume_manager.list_resumes()
    if resumes:
        logger.warning(f"No phone match, using fallback resume: {resumes[0].candidate_name}")
        return resumes[0]

    # Priority 4: Default
    logger.error("No resume found for this call")
    return Resume(
        id="default",
        candidate_name="Candidate",
        content="No resume information available. Please ask the caller to set up their profile.",
        file_path="",
    )


# Create the agent server
server = AgentServer()


@server.rtc_session(agent_name="proximus-agent")
async def handle_call(ctx: agents.JobContext):
    """Handle an incoming screening call."""
    from datetime import datetime

    logger.info(f"New call connected: room={ctx.room.name}")

    # Event loop captured so the (sync) transcript callback can schedule the
    # live-transcript data publish safely from any thread.
    loop = asyncio.get_running_loop()

    async def _publish_transcript_turn(role: str, text: str) -> None:
        """Publish a transcript turn to the room as data (best-effort).

        Never raises — a publish failure must not affect the call.
        """
        try:
            payload = json.dumps({"type": "transcript", "role": role, "text": text}).encode()
            await ctx.room.local_participant.publish_data(payload, topic="transcript")
        except Exception as exc:  # noqa: BLE001 — live transcript is best-effort
            logger.debug(f"Live transcript publish failed: {exc}")

    # Determine call direction from room name and metadata
    direction = "outbound" if ctx.room.name.startswith("proximus-outbound-") else "inbound"
    target_phone: str | None = None
    job_detail: str | None = None
    if ctx.room.metadata:
        try:
            meta = json.loads(ctx.room.metadata)
            direction = meta.get("direction", direction)
            target_phone = meta.get("target_phone")
            job_detail = meta.get("job_detail")
        except json.JSONDecodeError:
            pass

    # Resolve which resume to use
    resume = resolve_resume(ctx)

    # Extract caller/target phone
    caller_phone: str | None = target_phone  # For outbound, use target from metadata
    if not caller_phone:
        for participant in ctx.room.remote_participants.values():
            caller_phone = extract_caller_phone(participant)
            if caller_phone:
                break

    # Prepare call record for transcript capture
    call_record = CallRecord(
        id=CallRecord.generate_id(),
        room_name=ctx.room.name,
        resume_id=resume.id if resume.id != "default" else None,
        candidate_name=resume.candidate_name,
        caller_phone=caller_phone,
        direction=direction,
        started_at=datetime.now(),
    )
    transcript: list[CallTranscriptEntry] = []

    # Create the agent session using direct API keys (not LiveKit hosted inference)
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=get_llm(),
        tts=cartesia.TTS(voice=resume.voice or DEFAULT_TTS_VOICE),
        vad=silero.VAD.load(
            min_silence_duration=0.5,
        ),
        min_endpointing_delay=0.5,
        max_endpointing_delay=5.0,
    )

    # Hook transcript events via conversation_item_added (captures both user and agent)
    @session.on("conversation_item_added")
    def _on_conversation_item(event):
        item = event.item
        if not hasattr(item, "role") or not hasattr(item, "text_content"):
            return
        text = item.text_content
        if not text or not text.strip():
            return
        role = "agent" if item.role == "assistant" else "user"
        clean = text.strip()
        transcript.append(
            CallTranscriptEntry(
                role=role,
                text=clean,
                timestamp=time.time(),
            )
        )
        logger.debug(f"[transcript] {role}: {clean}")
        # Stream the turn to any dashboard listeners in the room (best-effort).
        try:
            asyncio.run_coroutine_threadsafe(_publish_transcript_turn(role, clean), loop)
        except Exception as exc:  # noqa: BLE001 — never let streaming break capture
            logger.debug(f"Live transcript scheduling failed: {exc}")

    @session.on("close")
    def _on_close(*args):
        call_record.ended_at = datetime.now()
        call_record.transcript = transcript
        # Persist the transcript immediately so it's never lost, then add an AI
        # summary in the background (best-effort, off the event loop).
        get_call_manager().save_call(call_record)
        logger.info(f"Call ended, saved transcript with {len(transcript)} turns: {call_record.id}")
        threading.Thread(target=_add_call_summary, args=(call_record,), daemon=True).start()

    # Start the session — for outbound, only link to SIP participants (not browser listeners)
    input_opts = (
        room_io.RoomInputOptions(
            participant_kinds=[rtc.ParticipantKind.PARTICIPANT_KIND_SIP],
        )
        if direction == "outbound"
        else None
    )

    start_kwargs = dict(
        room=ctx.room,
        agent=CandidateAgent(resume, direction=direction, job_detail=job_detail),
    )
    if input_opts:
        start_kwargs["room_input_options"] = input_opts

    await session.start(**start_kwargs)
    logger.info(f"Session started (direction={direction})")

    if direction == "outbound":
        # Wait for SIP participant before speaking
        for _ in range(15):
            sip_parts = [
                p
                for p in ctx.room.remote_participants.values()
                if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
            ]
            if sip_parts:
                logger.info(f"SIP participant ready: {sip_parts[0].identity}")
                break
            await asyncio.sleep(1)
        else:
            logger.warning("No SIP participant joined after 15s")

        # For outbound calls, introduce yourself to the recruiter
        await session.generate_reply(
            instructions=(
                f"You are {resume.candidate_name} and you are calling a recruiter. "
                f'Say hello briefly - for example "Hi, this is {resume.candidate_name}, '
                "I'm returning your call about the role you reached out about.\" "
                "Keep it short and natural, then let them lead the conversation."
            )
        )
        logger.info(f"Outbound call: greeted recruiter ({resume.candidate_name})")
    else:
        # For inbound calls, greet the caller
        await session.generate_reply(
            instructions=f"Greet the caller. You are {resume.candidate_name}. Say hello and thank them for calling. Ask how you can help."
        )

    logger.info(f"Agent started for candidate: {resume.candidate_name}")


def run_agent():
    """Run the LiveKit agent worker."""
    agents.cli.run_app(server)


if __name__ == "__main__":
    run_agent()
