# Contributing to PROXIMUS

Thanks for your interest in contributing! PROXIMUS is an open-source reference
implementation of a real-time AI voice agent, demonstrated through a personal
recruiter-screening assistant. Contributions of all kinds are welcome — code,
docs, bug reports, and ideas.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By
participating, you agree to uphold it.

## Ways to Contribute

- **Report bugs** — open an issue with steps to reproduce.
- **Suggest features** — open an issue describing the use case.
- **Add providers** — PROXIMUS has a provider-agnostic AI layer; new STT/TTS/LLM
  or telephony backends (e.g. Twilio as a Telnyx alternative) are great additions.
- **Improve docs** — setup walkthroughs, diagrams, and examples help everyone.
- **Write tests** — coverage is early; pure-logic tests need no API keys.

Check issues labeled [`good first issue`](https://github.com/Adawodu/PROXIMUS/labels/good%20first%20issue)
to get started.

## Development Setup

### Backend (Python 3.12+)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env   # fill in your keys for live testing (not needed for tests)
```

### Web dashboard (Node 18+)

```bash
cd web
npm install
npm run dev
```

## Before You Open a PR

Run the same checks CI runs:

```bash
ruff check .          # lint
ruff format --check . # formatting
mypy src              # type checking
pytest                # tests
```

For the web dashboard:

```bash
cd web && npm run lint && npm run build
```

## Pull Request Guidelines

1. Fork the repo and create a feature branch off `main`.
2. Keep PRs focused — one logical change per PR.
3. Add or update tests for behavior changes where practical.
4. Update docs (`README.md`, `docs/`) when you change behavior or config.
5. Ensure all checks above pass locally.
6. Fill out the PR template and link any related issues.

## Commit Messages

Use clear, present-tense messages (e.g. `Add Twilio outbound trunk support`).
Reference issues with `Fixes #123` where applicable.

## Project Layout

```
src/proximus/
  agent/      LiveKit voice agent (STT -> LLM -> TTS pipeline) + outbound dialing
  api/        FastAPI REST API
  ai/         Provider-agnostic AI layer (Anthropic / OpenAI)
  context/    Resume parsing, phone->resume mapping, call records
  sip/        Telnyx/LiveKit SIP setup helpers
web/          React + Vite dashboard
tests/        Pytest suite (pure logic — no live API keys required)
docs/         Architecture, setup, API reference, development notes
```

## Responsible Use

PROXIMUS speaks on a phone call using your resume. Please review
[RESPONSIBLE_USE.md](RESPONSIBLE_USE.md) before building features that change how
the agent represents a person on a call. Contributions that add deceptive or
non-consensual capabilities will not be accepted.

## Questions

Open a [discussion](https://github.com/Adawodu/PROXIMUS/discussions) or an issue.
We're happy to help.
