# PROXIMUS

AI voice agent that handles incoming recruiter screening calls using candidate resume context. When a recruiter bot calls your phone number, PROXIMUS answers as you — using your resume to respond naturally and accurately.

## Features

- **AI Voice Agent** — Answers recruiter screening calls using Claude or GPT with your resume as context
- **Speech Pipeline** — Deepgram STT + LLM + Cartesia TTS for natural conversation
- **Phone Integration** — Telnyx SIP trunking with LiveKit for reliable telephony
- **Resume Management** — Upload PDF, DOCX, or TXT resumes via API or web dashboard
- **Phone Linking** — Map phone numbers to resumes for automatic call routing
- **Web Dashboard** — React-based UI for managing resumes, phone links, and monitoring

## Architecture

```
Recruiter Bot → Telnyx → LiveKit SIP → LiveKit Room → PROXIMUS Agent
                                                       (Deepgram STT → Claude/GPT → Cartesia TTS)
```

**Components:**
- `src/proximus/agent/` — LiveKit voice agent (STT/LLM/TTS pipeline)
- `src/proximus/api/` — FastAPI REST API for resume and phone management
- `src/proximus/context/` — Resume parsing and phone-to-resume mapping
- `src/proximus/sip/` — SIP trunk/dispatch configuration helpers
- `web/` — React + Vite web dashboard

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (for web dashboard)
- Accounts: [Telnyx](https://telnyx.com), [LiveKit Cloud](https://cloud.livekit.io), [Deepgram](https://deepgram.com), [Cartesia](https://cartesia.ai), and [Anthropic](https://anthropic.com) or [OpenAI](https://openai.com)

### Backend

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Edit .env with your API keys

python -m proximus api          # Start REST API (port 8000)
python -m proximus agent dev    # Start voice agent
```

### Web Dashboard

```bash
cd web
npm install
npm run dev                     # Start dev server (port 5173)
```

### SIP Setup

```bash
python -m proximus sip setup    # Show Telnyx/LiveKit setup instructions
python -m proximus sip config   # Show current SIP configuration
```

## Documentation

- [Architecture](docs/architecture.md) — System design, call flow, component details
- [Setup Guide](docs/setup.md) — Full installation and configuration walkthrough
- [API Reference](docs/api-reference.md) — All REST API endpoints
- [Development](docs/development.md) — Dev workflow, testing, contributing

## License

MIT
