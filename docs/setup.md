# Setup Guide

## Prerequisites

- Python 3.12+
- Node.js 18+ (for web dashboard)
- [Telnyx](https://telnyx.com) account with a phone number
- [LiveKit Cloud](https://cloud.livekit.io) account
- [Deepgram](https://deepgram.com) API key
- [Cartesia](https://cartesia.ai) API key
- [Anthropic](https://anthropic.com) or [OpenAI](https://openai.com) API key

## 1. Clone and Install

```bash
git clone https://github.com/your-repo/PROXIMUS.git
cd PROXIMUS

# Backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd web
npm install
cd ..
```

## 2. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Telnyx
TELNYX_API_KEY=your-telnyx-key
TELNYX_PHONE_NUMBER=+1234567890
TELNYX_SIP_URI=your-sip-uri.sip.telnyx.com
TELNYX_SIP_USERNAME=your-sip-username
TELNYX_SIP_PASSWORD=your-sip-password

# AI Provider
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

# Speech Services
DEEPGRAM_API_KEY=your-deepgram-key
CARTESIA_API_KEY=your-cartesia-key
```

## 3. Telnyx Configuration

1. **Create a SIP Connection** in the Telnyx portal:
   - Go to SIP Connections → Add SIP Connection
   - Type: **FQDN**
   - Enable **Receive** (inbound calls)
   - Set Digest Authentication credentials (username + password)

2. **Purchase a phone number** (or use an existing one)

3. **Link the phone number** to your SIP Connection:
   - Go to Numbers → Select your number
   - Set Connection: your SIP connection

## 4. LiveKit SIP Configuration

Install the LiveKit CLI:

```bash
brew install livekit-cli
```

Configure your project:

```bash
lk project add
# Follow prompts to add your LiveKit Cloud project
```

Create an inbound SIP trunk:

```bash
python -m proximus sip setup
# Follow the generated commands
```

Or manually:

```bash
lk sip inbound create inbound-trunk.json
lk sip dispatch create dispatch-rule.json
```

## 5. Running the Application

Start all three services:

```bash
# Terminal 1: REST API
python -m proximus api

# Terminal 2: Voice Agent
python -m proximus agent dev

# Terminal 3: Web Dashboard
cd web && npm run dev
```

Access the dashboard at http://localhost:5173

## 6. First Use

1. Open http://localhost:5173
2. Go to **Resumes** → Upload your resume (PDF, DOCX, or TXT)
3. Go to **Phone Links** → Link your phone number to your resume
4. Have a recruiter bot call your Telnyx number
5. PROXIMUS answers as you, using your resume context

## Troubleshooting

### Agent not connecting
- Verify `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` are correct
- Check that the agent name in your dispatch rule matches `proximus-agent`

### Calls not routing
- Verify your Telnyx SIP connection is set to receive calls
- Check that the inbound trunk number matches your Telnyx number (E.164 format)
- Verify the dispatch rule is active in LiveKit

### Upload fails
- Ensure `python-multipart` is installed: `pip install python-multipart`
- Check API logs for detailed error messages
