# PROXIMUS — Hardening & Evolution Roadmap

A code review of the backend and React dashboard produced a 27-item roadmap,
delivered across six PRs (all behind required CI checks). This document records
what shipped.

Legend: 🔴 security/correctness · 🟡 robustness/perf · 🟢 feature/quality

## Phase 0 — Pipeline
- Verified the CI workflow and enabled **branch protection** (required `Backend (Python)` + `Web dashboard` checks).
- Merged the contributor Twilio SIP backend (PR #6) after fixing syntax errors and formatting.

## Phase 1 — Security & correctness (PR #7)
- 🔴 API-key authentication (`X-API-Key`; no-op when unset for local dev).
- 🔴 Configurable LLM models; replaced the deprecated default with `claude-haiku-4-5`.
- 🔴 Removed the dead `proximus.ai` provider layer.
- Dropped unsupported `.doc` uploads; hardened the Telnyx ANI PATCH.
- Frontend: stale-closure fix, Dashboard/modal loading+error states, removed hardcoded caller ID.

## Phase 2 — Robustness & performance (PR #8)
- 🟡 Streamed uploads with a 10 MB cap; parsing moved off the event loop.
- Rebuilt the resume registry from disk (no stale in-memory state); prompt fix; Python 3.12 alignment.
- Frontend: **TanStack Query** for caching; client-side validation.

## Phase 3A — Data & features (PR #9)
- 🟢 **SQLite** storage for resumes and calls, auto-migrating legacy JSON on first run; pagination.
- Post-call AI summaries; outbound rate limiting; configurable CORS; per-resume TTS voice.

## Phase 3B — Infrastructure (PR #10)
- 🟢 Dockerfiles (backend + nginx web) and `docker-compose.yml`.
- FastAPI endpoint test coverage (isolated from real data).

## Phase 3C — Frontend polish (PR #11)
- 🟢 Modal accessibility (dialog roles, Escape-to-close, labels); accessible Call History list.
- **Vitest + React Testing Library** (wired into CI); surfaced call summaries in the UI.

## Phase 3D — Follow-ups (PR #12)
- 🟢 **Live transcript streaming**: the agent publishes transcript turns as LiveKit room
  data messages (best-effort; never disrupts a call), rendered live in the call modal.
- Voice-picker UI in the resume detail modal.

## Testing
- Backend: 25 → 67 pytest. Frontend: 6 Vitest specs. Both gate every PR via CI.
