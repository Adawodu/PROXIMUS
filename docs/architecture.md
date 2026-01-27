# Architecture

## System Overview

PROXIMUS is an AI voice agent that answers recruiter screening calls on behalf of job candidates. It uses the candidate's resume as context to respond naturally to questions.

## Call Flow

```
1. Recruiter bot dials candidate's phone number
2. Telnyx receives the call via SIP
3. Telnyx forwards to LiveKit SIP trunk
4. LiveKit dispatch rule creates a room and assigns the PROXIMUS agent
5. Agent extracts caller's phone number from SIP attributes
6. Agent looks up the linked resume for that phone number
7. Agent starts voice pipeline: Deepgram STT → Claude/GPT → Cartesia TTS
8. Agent greets the caller and handles the conversation using resume context
```

## Component Architecture

```
┌─────────────────────────────────────────────────────┐
│                    PROXIMUS                          │
├──────────────┬──────────────┬───────────────────────┤
│  Web UI      │  REST API    │  Voice Agent          │
│  (React)     │  (FastAPI)   │  (LiveKit Agents)     │
│  :5173       │  :8000       │                       │
├──────────────┴──────────────┴───────────────────────┤
│               Core Services                          │
│  ┌─────────────────┐  ┌──────────────────────┐      │
│  │ ResumeManager   │  │ SIP Configuration    │      │
│  │ - Parse resumes │  │ - Trunk setup        │      │
│  │ - Phone linking │  │ - Dispatch rules     │      │
│  └─────────────────┘  └──────────────────────┘      │
├─────────────────────────────────────────────────────┤
│               External Services                      │
│  Telnyx (SIP) │ LiveKit │ Deepgram │ Cartesia │ LLM │
└─────────────────────────────────────────────────────┘
```

## Module Details

### `src/proximus/agent/voice.py`
The voice agent is the core of the system. It:
- Registers with LiveKit as `proximus-agent`
- Handles incoming SIP calls via `@server.rtc_session`
- Resolves which resume to use (phone lookup → metadata → fallback)
- Creates an `AgentSession` with STT/LLM/TTS pipeline
- Generates an initial greeting as the candidate

### `src/proximus/context/resume.py`
Manages resume data and phone-to-resume mapping:
- Parses PDF (pdfplumber), DOCX (python-docx), and TXT files
- Stores resumes in memory with unique IDs (SHA256 hash)
- Maps phone numbers to resume IDs for call routing
- Generates system prompts that instruct the LLM to act as the candidate

### `src/proximus/api/main.py`
FastAPI REST API providing:
- Resume CRUD (upload, list, get, delete)
- Phone link management (create, list, delete)
- Health check endpoint
- CORS enabled for web dashboard

### `src/proximus/sip/config.py`
Helpers for SIP trunk configuration:
- Generates LiveKit CLI commands for trunk/dispatch setup
- Stores Telnyx SIP IP ranges for trunk configuration
- Provides setup instructions

### `web/`
React + Vite dashboard:
- Dashboard with status overview
- Resume upload (drag-and-drop) and management
- Phone number linking interface
- Configuration reference page

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Voice Agent | LiveKit Agents v1.3 | Real-time voice communication |
| STT | Deepgram Nova-3 | Speech-to-text |
| LLM | Claude Sonnet / GPT-4o | Natural language understanding |
| TTS | Cartesia Sonic | Text-to-speech |
| Telephony | Telnyx | SIP trunking, phone numbers |
| API | FastAPI + Uvicorn | REST API server |
| Frontend | React + Vite + Tailwind | Web dashboard |
| Config | pydantic-settings | Environment-based configuration |

## Data Flow

### Resume Upload
```
User → Web UI/API → ResumeManager.parse_resume() → In-memory storage
```

### Phone Linking
```
User → Web UI/API → ResumeManager.link_phone() → Phone-to-resume map
```

### Incoming Call
```
SIP Call → LiveKit Room → handle_call() → resolve_resume() → CandidateAgent
                                              ↓
                                    Phone lookup from SIP attributes
                                              ↓
                                    Resume → System prompt → LLM
```

## Design Decisions

- **In-memory storage**: Resumes and phone links are stored in memory for simplicity. A database can be added later for persistence.
- **Provider-agnostic AI**: The LLM can be swapped between Anthropic and OpenAI via configuration.
- **Explicit agent dispatch**: LiveKit dispatch rules route calls to the specific `proximus-agent` by name, enabling multiple agent types in the future.
- **Phone-based routing**: Caller phone number (from SIP attributes) is the primary method for resolving which resume to use.
