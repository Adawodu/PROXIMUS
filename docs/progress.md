# PROXIMUS — Development Progress

## What's Built

### Core Agent (`src/proximus/agent/`)
- **Voice agent** — LiveKit-based agent that joins SIP calls and responds as the candidate using their resume context
- **Inbound calls** — Agent auto-dispatched when a recruiter dials the Telnyx SIP number
- **Outbound calls** — Agent dials a recruiter's number, waits for SIP connect, then introduces itself
- **Job detail injection** — Optional job description passed into agent instructions for contextual answers
- **Concise response tuning** — System prompt constrains replies to 2-3 sentences; endpointing delays tuned (0.5s–5s)
- **Transcript capture** — `conversation_item_added` event captures both agent and recruiter turns, persisted to disk on call close

### API (`src/proximus/api/`)
- `GET /health` — Service status
- `GET /resumes` / `POST /resumes/upload` / `DELETE /resumes/{id}` — Resume CRUD + PDF upload
- `GET /phone-links` / `POST /phone-links` / `DELETE /phone-links/{id}` — Map phone numbers to resumes
- `POST /calls/outbound` — Initiate outbound call (phone, resume_id, caller_id, job_detail)
- `GET /calls` / `GET /calls/{id}` — Call history with transcripts

### Dashboard (`web/`)
- React + TypeScript + Vite
- Pages: Dashboard, Resumes, Phone Links, Call History, Configuration, Guide
- Outbound call modal with resume selector, phone input, caller ID, and job detail textarea
- Call history table with expandable transcript view

### Infrastructure
- **SIP**: Telnyx trunk → LiveKit Cloud SIP inbound + dispatch rules
- **STT**: Deepgram Nova 3
- **LLM**: Anthropic Claude Sonnet (configurable to OpenAI GPT-4o)
- **TTS**: Cartesia (voice ID `5ee9feff-1265-424a-9d7f-8e4d431a12c7`)
- **VAD**: Silero (0.5s min silence)

## Key Issues Resolved
- **Agent audio not reaching SIP callers** — Root cause: Cartesia TTS credits exhausted (402). Temporarily swapped to OpenAI TTS until credits restored.
- **Agent linked to browser listener instead of SIP participant** — Fixed with `RoomInputOptions(participant_kinds=[PARTICIPANT_KIND_SIP])` for outbound calls.
- **Transcript missing recruiter dialogue** — Consolidated to single `conversation_item_added` handler capturing both roles.
- **Long response latency** — Added concise response instructions + endpointing delay tuning.

## Not Yet Built
- **Auth / user accounts** — No login, no multi-tenancy
- **Database** — All data stored as JSON files on disk (`data/resumes/`, `data/calls/`)
- **Deployment** — Runs locally only (uvicorn + LiveKit dev mode)
- **Supabase migration** — Planned: Postgres for resumes/calls/users, Supabase Auth, Storage for PDFs
- **Payment / billing** — No paywall or usage tracking
- **Call recording playback** — Requires LiveKit Cloud recording plan
- **Analytics** — No call duration stats, success rates, or usage dashboards
- **Testing** — No unit or integration tests

## Repo
- GitHub: https://github.com/Adawodu/PROXIMUS (private)
- Branch: `main`
- 64 files, initial commit
