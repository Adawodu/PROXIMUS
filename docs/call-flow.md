# PROXIMUS Outbound Call Flow

## Sequence Diagram

```mermaid
sequenceDiagram
    participant UI as Dashboard UI
    participant API as FastAPI Server
    participant LK as LiveKit Cloud
    participant Agent as PROXIMUS Agent<br/>(Python Worker)
    participant SIP as LiveKit SIP Bridge
    participant Phone as Recruiter Phone/Bot

    Note over UI,Phone: 1. CALL INITIATION
    UI->>API: POST /calls/outbound {phone, resume_id}
    API->>LK: CreateRoom (metadata: resume_id, direction, target_phone)
    API->>LK: CreateAgentDispatch (agent_name: proximus-agent)
    API->>LK: CreateSIPParticipant (trunk_id, phone, room)
    LK->>Agent: Job dispatched → handle_call(ctx)
    LK->>SIP: Dial outbound via Telnyx SIP trunk
    SIP->>Phone: SIP INVITE (caller_id from Telnyx ANI)
    Phone-->>SIP: 200 OK (call answered)
    SIP-->>LK: SIP participant joins room

    Note over UI,Phone: 2. AGENT SESSION STARTUP
    Agent->>Agent: resolve_resume(ctx) → load resume from metadata
    Agent->>Agent: Create AgentSession(stt=Deepgram, llm=Claude, tts=Cartesia, vad=Silero)
    Agent->>LK: session.start(room) → publishes audio track
    Agent->>Agent: asyncio.sleep(2) — wait for TTS init
    Agent->>LK: session.generate_reply() → initial greeting

    Note over UI,Phone: 3. VOICE PIPELINE (per turn)
    Phone->>SIP: Recruiter speaks (RTP audio)
    SIP->>LK: Audio frames forwarded to room
    LK->>Agent: Audio frames via RoomIO subscription

    rect rgb(255, 240, 240)
        Note over Agent: ⚠️ BOTTLENECK AREA
        Agent->>Agent: Silero VAD: detect speech end (min_silence=0.8s)
        Agent->>Agent: Deepgram STT: transcribe audio → text
        Agent->>Agent: Claude LLM: generate response text
        Agent->>Agent: Cartesia TTS: synthesize speech audio
    end

    Agent->>LK: Publish TTS audio frames to room
    LK->>SIP: Forward audio to SIP participant
    SIP->>Phone: RTP audio → recruiter hears agent
    LK->>UI: Audio forwarded to listener (if connected)

    Note over UI,Phone: 4. TRANSCRIPT CAPTURE
    Agent->>Agent: conversation_item_added event → append to transcript[]
    Note right of Agent: Captures both role="user" and role="assistant"

    Note over UI,Phone: 5. CALL END
    Phone->>SIP: Recruiter hangs up / call timeout
    SIP->>LK: SIP participant leaves room
    LK->>Agent: Participant disconnect event
    Agent->>Agent: session "close" event fires
    Agent->>Agent: Save CallRecord to data/calls/{id}.json

    Note over UI,Phone: 6. LISTENER (INDEPENDENT)
    UI->>API: GET /calls/listen/{room_name} → get token
    UI->>LK: Connect to room (subscribe-only)
    Note right of UI: Listener hears both sides.<br/>Closing modal only disconnects browser,<br/>does NOT end the agent↔recruiter call.
```

## Timing Analysis — Identified Gaps

From the outbound call transcript `8afc96f4b51d`:

| Gap | Between | Duration | Cause |
|-----|---------|----------|-------|
| **Gap 1** | Recruiter finishes greeting → Agent first reply | **23.1s** | VAD (0.8s) + STT + LLM cold start + TTS |
| **Gap 2** | Recruiter asks question → Agent reply | **26.9s** | VAD waits for long silence after multi-sentence speech |
| **Gap 3** | Recruiter asks about role → Agent reply | **63.5s** | LLM generating long response + TTS synthesis |
| **Gap 4** | Recruiter asks about Laffa.io → Agent reply | **89.6s** | LLM generating very long response |

### Root Causes

1. **VAD `min_silence_duration=0.8s` is too conservative** — The recruiter bot speaks in
   multiple short sentences with pauses between them. The VAD keeps waiting for 0.8s of
   silence, but each new sentence resets the timer. The agent can't start processing
   until VAD confirms the speaker is done.

2. **LLM response too long** — Claude is generating multi-paragraph responses. The TTS
   must synthesize all of it before (or while) playing. Long responses = long gaps.

3. **No streaming TTS** — If TTS isn't streaming chunks as they're generated, the full
   response must be synthesized before playback begins.

4. **User turns are fragmented** — The recruiter bot's speech arrives as many small
   `conversation_item_added` events (56 "user" turns for ~6 actual statements), suggesting
   STT is emitting partial/sentence-level segments rather than full turns.

### Recommended Fixes

| Fix | Change | Impact |
|-----|--------|--------|
| Reduce VAD silence | `min_silence_duration=0.5` for outbound | Agent responds faster after recruiter stops |
| Shorten LLM responses | Add instruction: "Keep responses under 3 sentences" | Reduces TTS synthesis time |
| Tune `max_endpointing_delay` | Set on AgentSession to cap wait time | Prevents 60s+ gaps |
| Reduce `min_endpointing_delay` | Lower from default to respond sooner | Faster turn-taking |
