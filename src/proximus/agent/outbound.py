"""Outbound call initiation for PROXIMUS."""

from __future__ import annotations

import json
import logging
import uuid

from livekit import api

from proximus.config import get_settings

logger = logging.getLogger(__name__)


async def initiate_outbound_call(
    phone: str, resume_id: str, caller_id: str | None = None, job_detail: str | None = None
) -> dict:
    """Initiate an outbound SIP call to a recruiter.

    Creates a LiveKit room with metadata and dials the target phone number
    into it. An agent dispatch assigns the proximus-agent to the room.

    Args:
        phone: Target phone number in E.164 format.
        resume_id: Resume ID to use for the agent.
        caller_id: Optional caller ID to display (E.164 format).

    Returns:
        Dict with call_id (room_name) and status.

    Raises:
        ValueError: If outbound trunk is not configured.
    """
    settings = get_settings()

    # AFTER:
    if not settings.outbound_trunk_id:
        provider = settings.sip_provider
        if provider == "twilio":
            hint = "proximus sip trunk-outbound --provider twilio"
        else:
            hint = "proximus sip trunk-outbound --provider telnyx"
        raise ValueError(
            "Outbound SIP trunk not configured. "
            f"Set OUTBOUND_TRUNK_ID in .env after creating a trunk with: {hint}"
        )

    room_name = f"proximus-outbound-{uuid.uuid4().hex[:12]}"

    lk = api.LiveKitAPI(
        url=settings.livekit_url,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret.get_secret_value(),
    )

    try:
        metadata_dict = {
            "resume_id": resume_id,
            "direction": "outbound",
            "target_phone": phone,
        }
        if job_detail:
            metadata_dict["job_detail"] = job_detail
        room_metadata = json.dumps(metadata_dict)

        # Create the room with metadata so the agent knows the resume + direction
        await lk.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                metadata=room_metadata,
            )
        )
        logger.info(f"Created outbound room: {room_name}")

        # Explicitly dispatch the agent to this room
        await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=settings.agent_name,
                room=room_name,
                metadata=room_metadata,
            )
        )
        logger.info(f"Dispatched agent to room: {room_name}")

        # Dial the target phone into the room
        # Caller ID is managed via Telnyx ANI override on the credential connection.
        # To change it dynamically, update via Telnyx API: PATCH /v2/credential_connections/{id}
        await lk.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=settings.outbound_trunk_id,
                sip_call_to=phone,
                room_name=room_name,
                participant_identity=f"sip_{phone}",
                participant_name="Recruiter",
            )
        )
        logger.info(f"Dialed {phone} into room {room_name} (caller_id={caller_id})")

        return {
            "call_id": room_name,
            "phone": phone,
            "resume_id": resume_id,
            "status": "dialing",
        }
    finally:
        await lk.aclose()
