"""FastAPI application for PROXIMUS API."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from proximus.config import get_settings
from proximus.context import CallManager, CallRecord, Resume, ResumeManager

# Global manager instances
_resume_manager: ResumeManager | None = None
_call_manager: CallManager | None = None


def get_resume_manager() -> ResumeManager:
    """Get or create the resume manager instance."""
    global _resume_manager
    if _resume_manager is None:
        _resume_manager = ResumeManager()
    return _resume_manager


def get_call_manager() -> CallManager:
    """Get or create the call manager instance."""
    global _call_manager
    if _call_manager is None:
        _call_manager = CallManager()
    return _call_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler."""
    # Startup
    get_resume_manager()
    yield
    # Shutdown


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="PROXIMUS",
        description="AI voice agent for handling recruiter screening calls",
        version="0.1.0",
        lifespan=lifespan,
    )
    return application


app = create_app()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models
# ============================================================================


class ResumeResponse(BaseModel):
    """Response model for a resume."""

    id: str
    candidate_name: str
    file_path: str
    created_at: datetime
    content_preview: str  # First 500 chars


class ResumeListResponse(BaseModel):
    """Response model for listing resumes."""

    resumes: list[ResumeResponse]
    total: int


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    version: str


class UploadResponse(BaseModel):
    """Response model for resume upload."""

    id: str
    candidate_name: str
    message: str


class PhoneLinkRequest(BaseModel):
    """Request model for linking a phone number to a resume."""

    phone: str
    resume_id: str


class PhoneLinkResponse(BaseModel):
    """Response model for a phone link."""

    phone: str
    resume_id: str
    candidate_name: str


class PhoneLinksResponse(BaseModel):
    """Response model for listing phone links."""

    links: list[PhoneLinkResponse]
    total: int


class CallTranscriptEntryResponse(BaseModel):
    """A single transcript turn."""

    role: str
    text: str
    timestamp: float


class CallSummaryResponse(BaseModel):
    """Summary of a call record (no transcript)."""

    id: str
    room_name: str
    resume_id: str | None
    candidate_name: str
    caller_phone: str | None
    direction: str
    started_at: datetime
    ended_at: datetime | None
    turn_count: int


class CallDetailResponse(CallSummaryResponse):
    """Full call record with transcript."""

    transcript: list[CallTranscriptEntryResponse]


class CallListResponse(BaseModel):
    """Response model for listing calls."""

    calls: list[CallSummaryResponse]
    total: int


class OutboundCallRequest(BaseModel):
    """Request to initiate an outbound call."""

    phone: str
    resume_id: str
    caller_id: str | None = None  # Optional caller ID override
    job_detail: str | None = None  # Job description or context for the call


class OutboundCallResponse(BaseModel):
    """Response for an outbound call initiation."""

    call_id: str
    phone: str
    resume_id: str
    status: str


# ============================================================================
# Helper Functions
# ============================================================================


def resume_to_response(resume: Resume) -> ResumeResponse:
    """Convert a Resume to ResumeResponse."""
    return ResumeResponse(
        id=resume.id,
        candidate_name=resume.candidate_name,
        file_path=resume.file_path,
        created_at=resume.created_at,
        content_preview=resume.content[:500] + "..."
        if len(resume.content) > 500
        else resume.content,
    )


# ============================================================================
# Routes
# ============================================================================


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="0.1.0")


@app.get("/resumes", response_model=ResumeListResponse)
async def list_resumes() -> ResumeListResponse:
    """List all uploaded resumes."""
    manager = get_resume_manager()
    resumes = manager.list_resumes()
    return ResumeListResponse(
        resumes=[resume_to_response(r) for r in resumes],
        total=len(resumes),
    )


@app.get("/resumes/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: str) -> ResumeResponse:
    """Get a specific resume by ID."""
    manager = get_resume_manager()
    resume = manager.get_resume(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume_to_response(resume)


@app.post("/resumes", response_model=UploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    candidate_name: str | None = None,
) -> UploadResponse:
    """Upload a new resume.

    Supported formats: PDF, DOCX, TXT
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".docx", ".doc", ".txt"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Supported: .pdf, .docx, .doc, .txt",
        )

    # Save to temp file for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        manager = get_resume_manager()
        resume = manager.parse_resume(tmp_path, candidate_name)

        # Move to permanent storage
        storage_dir = manager.storage_dir
        permanent_path = storage_dir / f"{resume.id}{suffix}"
        shutil.move(tmp_path, permanent_path)
        resume.file_path = str(permanent_path)

        return UploadResponse(
            id=resume.id,
            candidate_name=resume.candidate_name,
            message=f"Resume uploaded successfully for {resume.candidate_name}",
        )
    except Exception as e:
        # Clean up temp file on error
        Path(tmp_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.delete("/resumes/{resume_id}")
async def delete_resume(resume_id: str) -> dict[str, str]:
    """Delete a resume by ID."""
    manager = get_resume_manager()
    resume = manager.get_resume(resume_id)

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    # Delete file if it exists
    file_path = Path(resume.file_path)
    if file_path.exists():
        file_path.unlink()

    manager.delete_resume(resume_id)
    return {"message": f"Resume {resume_id} deleted successfully"}


@app.get("/resumes/{resume_id}/context")
async def get_resume_context(resume_id: str) -> dict[str, str]:
    """Get the system prompt context for a resume.

    Useful for testing what the agent will see.
    """
    manager = get_resume_manager()
    resume = manager.get_resume(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"system_prompt": resume.to_system_prompt()}


# ============================================================================
# Phone Link Routes
# ============================================================================


@app.post("/phone-links", response_model=PhoneLinkResponse)
async def create_phone_link(request: PhoneLinkRequest) -> PhoneLinkResponse:
    """Link a phone number to a resume.

    When a call comes in from this phone number, the agent will use
    the linked resume for context.
    """
    manager = get_resume_manager()

    # Verify resume exists
    resume = manager.get_resume(request.resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    try:
        manager.link_phone(request.phone, request.resume_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    normalized_phone = manager.normalize_phone(request.phone)

    return PhoneLinkResponse(
        phone=normalized_phone,
        resume_id=request.resume_id,
        candidate_name=resume.candidate_name,
    )


@app.get("/phone-links", response_model=PhoneLinksResponse)
async def list_phone_links() -> PhoneLinksResponse:
    """List all phone number to resume links."""
    manager = get_resume_manager()
    links = manager.list_phone_links()

    responses: list[PhoneLinkResponse] = []
    for phone, resume_id in links.items():
        resume = manager.get_resume(resume_id)
        if resume:
            responses.append(
                PhoneLinkResponse(
                    phone=phone,
                    resume_id=resume_id,
                    candidate_name=resume.candidate_name,
                )
            )

    return PhoneLinksResponse(links=responses, total=len(responses))


@app.get("/phone-links/{phone}", response_model=PhoneLinkResponse)
async def get_phone_link(phone: str) -> PhoneLinkResponse:
    """Get the resume linked to a phone number."""
    manager = get_resume_manager()
    resume = manager.get_resume_by_phone(phone)

    if not resume:
        raise HTTPException(status_code=404, detail="No resume linked to this phone number")

    normalized_phone = manager.normalize_phone(phone)

    return PhoneLinkResponse(
        phone=normalized_phone,
        resume_id=resume.id,
        candidate_name=resume.candidate_name,
    )


@app.delete("/phone-links/{phone}")
async def delete_phone_link(phone: str) -> dict[str, str]:
    """Unlink a phone number from its resume."""
    manager = get_resume_manager()

    if not manager.unlink_phone(phone):
        raise HTTPException(status_code=404, detail="Phone link not found")

    return {"message": f"Phone link removed for {manager.normalize_phone(phone)}"}


@app.get("/resumes/{resume_id}/phones")
async def get_resume_phones(resume_id: str) -> dict[str, list[str]]:
    """Get all phone numbers linked to a resume."""
    manager = get_resume_manager()

    if not manager.get_resume(resume_id):
        raise HTTPException(status_code=404, detail="Resume not found")

    phones = manager.get_phones_for_resume(resume_id)
    return {"phones": phones}


# ============================================================================
# Call History Routes
# ============================================================================


def _call_to_summary(record: CallRecord) -> CallSummaryResponse:
    return CallSummaryResponse(
        id=record.id,
        room_name=record.room_name,
        resume_id=record.resume_id,
        candidate_name=record.candidate_name,
        caller_phone=record.caller_phone,
        direction=record.direction,
        started_at=record.started_at,
        ended_at=record.ended_at,
        turn_count=len(record.transcript),
    )


@app.get("/calls", response_model=CallListResponse)
async def list_calls() -> CallListResponse:
    """List all call records."""
    manager = get_call_manager()
    records = manager.list_calls()
    return CallListResponse(
        calls=[_call_to_summary(r) for r in records],
        total=len(records),
    )


@app.get("/calls/{call_id}", response_model=CallDetailResponse)
async def get_call(call_id: str) -> CallDetailResponse:
    """Get a specific call record with full transcript."""
    manager = get_call_manager()
    record = manager.get_call(call_id)
    if not record:
        raise HTTPException(status_code=404, detail="Call record not found")

    return CallDetailResponse(
        id=record.id,
        room_name=record.room_name,
        resume_id=record.resume_id,
        candidate_name=record.candidate_name,
        caller_phone=record.caller_phone,
        direction=record.direction,
        started_at=record.started_at,
        ended_at=record.ended_at,
        turn_count=len(record.transcript),
        transcript=[
            CallTranscriptEntryResponse(role=e.role, text=e.text, timestamp=e.timestamp)
            for e in record.transcript
        ],
    )


# ============================================================================
# Outbound Call Routes
# ============================================================================


@app.post("/calls/outbound", response_model=OutboundCallResponse)
async def make_outbound_call(request: OutboundCallRequest) -> OutboundCallResponse:
    """Initiate an outbound call to a recruiter."""
    from proximus.agent.outbound import initiate_outbound_call

    # Verify resume exists
    resume_manager = get_resume_manager()
    if not resume_manager.get_resume(request.resume_id):
        raise HTTPException(status_code=404, detail="Resume not found")

    # Update Telnyx ANI if caller_id provided
    if request.caller_id:
        import httpx

        settings = get_settings()
        connection_id = settings.telnyx_credential_connection_id
        if not connection_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "caller_id override requires TELNYX_CREDENTIAL_CONNECTION_ID to be set in .env"
                ),
            )
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"https://api.telnyx.com/v2/credential_connections/{connection_id}",
                headers={
                    "Authorization": f"Bearer KEY{settings.telnyx_api_key.get_secret_value()}"
                },
                json={
                    "outbound": {"ani_override": request.caller_id, "ani_override_type": "always"}
                },
            )

    try:
        result = await initiate_outbound_call(
            request.phone, request.resume_id, request.caller_id, request.job_detail
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate call: {e}") from e

    return OutboundCallResponse(**result)


@app.get("/calls/listen/{room_name}")
async def get_listen_token(room_name: str) -> dict[str, str]:
    """Generate a LiveKit join token to listen in on a call room."""
    from livekit.api import AccessToken, VideoGrants

    settings = get_settings()
    token = (
        AccessToken(
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret.get_secret_value(),
        )
        .with_identity("listener")
        .with_name("Listener")
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=False,
                can_subscribe=True,
            )
        )
    )
    jwt = token.to_jwt()
    ws_url = settings.livekit_url
    return {"token": jwt, "url": ws_url, "room_name": room_name}


def run_api():
    """Run the API server."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "proximus.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    run_api()
