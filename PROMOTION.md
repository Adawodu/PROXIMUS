# PROXIMUS — Promotion & Amplification To-Do

> Personal notes — gitignored, not part of the public repo.
> Created 2026-06-21. Repo: https://github.com/Adawodu/PROXIMUS

## ⭐ Do first (highest leverage)
- [ ] **Record a 60–90s demo video** of an outbound call (dashboard + agent audio). This is the #1 asset — nothing else should ship without it.
- [ ] Make a short **GIF** for the README + a full **video** (YouTube/Loom).
- [ ] Embed the GIF/video at the top of the README and in `docs/demo-transcript.md`.
- [ ] **Upload the social-preview image** (manual): Settings → General → Social preview → `docs/assets/social-preview.png`.

## 📣 Launch channels (in order)
- [ ] **Show HN** — post Tue–Thu ~8–10am ET, add the first comment immediately, stay in the thread all day. (Draft below.)
- [ ] **X / Twitter thread** — post 1/ then reply-chain the rest. Verify @ handles first. (Draft below.)
- [ ] **LinkedIn post** with the demo video. (Draft below.)
- [ ] **Reddit** — r/selfhosted, r/LocalLLaMA, r/artificial, r/SideProject (tailor per sub, lead with the demo).
- [ ] **Ecosystem communities** — LiveKit Slack/Discord, Telnyx, Anthropic. Warmest, most relevant audience; ask if they'll feature it.

## 🔎 Discoverability (passive, compounding)
- [ ] Submit PRs to awesome lists: awesome-livekit, awesome-ai-agents, awesome-selfhosted, awesome-voice-ai.
- [ ] Write a dev.to / Hashnode tutorial: "How I built an AI voice agent with LiveKit + Telnyx + Claude."

## 🔁 Contributor flywheel
- [ ] Pin a **"Contributions welcome 👋" Discussion** pointing at the good-first-issues.
- [ ] Lower setup friction: **docker-compose** and/or a **no-telephony demo mode** (biggest contribution unlock).
- [ ] Add a **ROADMAP.md** (source it from `docs/progress.md`).
- [ ] Label more issues `help wanted`; add 1–2 bigger "epic" issues.
- [ ] **Respond to first PRs in < 48h** (top predictor of repeat contributors).

## 🧭 Messaging reminder
Keep the dual framing: **voice-agent reference implementation + personal screening assistant**. Avoid "AI pretends to be you" phrasing.

---

# Drafts (ready to post)

## Show HN

**Title:** `Show HN: Proximus – Open-source AI voice agent for recruiter screening calls`

**First comment:**

> Hi HN, I'm Adebayo — author of Proximus.
>
> It's an open-source real-time AI voice agent. The flagship use case: a personal screening assistant that answers recruiter screening calls using your own resume as context — concise, first-person, and constrained to only state what's actually on the resume (it defers instead of fabricating). The same stack works for any voice agent; the screening assistant is just the example.
>
> The pipeline is SIP telephony → speech-to-text → LLM → text-to-speech, wired up with LiveKit Agents (Telnyx for the trunk, Deepgram STT, Claude or GPT, Cartesia TTS). It handles inbound and outbound calls, captures transcripts, and ships with a small React dashboard for managing resumes, phone links, and call history.
>
> Why I built it: I wanted to actually understand the moving parts of a production voice agent — barge-in, endpointing, turn-taking latency, SIP plumbing — and the recruiter-screening scenario was a concrete, testable target. I'm releasing it as a reference implementation because most "AI voice agent" content stops at a demo and skips the real telephony/latency wiring.
>
> What's interesting technically:
> - Tuning endpointing/VAD so the agent doesn't talk over people or feel laggy
> - Linking inbound caller numbers to the right resume context
> - Provider-agnostic LLM layer (swap Claude/GPT), with STT/TTS pluggability in progress
>
> Honest limitations (it's v0.1): no auth on the API, JSON-file storage (no DB yet), local-only deployment, and test coverage is just the pure logic so far. These are all filed as good-first-issues.
>
> On ethics: it speaks on live phone calls, so there's a RESPONSIBLE_USE.md — the intended use is your own calls with your own resume, and the prompt is built to be truthful and to disclose it's an AI if asked. Not for impersonating other people.
>
> Repo (MIT): https://github.com/Adawodu/PROXIMUS
> [Demo video: <-- paste clip link; do not post without it]
>
> Would love feedback on the voice-pipeline architecture and the storage/auth direction. Happy to answer anything.

## X / Twitter thread

1/ I open-sourced Proximus: a real-time AI voice agent that answers recruiter screening calls using your resume. SIP phone call → speech-to-text → LLM → text-to-speech, in real time. Watch it take a call 👇 (sound on) [attach 30–60s demo]

2/ The flagship use case is a personal screening assistant — it answers in first person from your resume, stays concise, and only says what's actually on the resume (it defers instead of making things up). But the stack underneath is a general-purpose voice-agent reference impl.

3/ Under the hood:
• LiveKit Agents — orchestration + SIP
• Telnyx — phone trunk
• Deepgram — speech-to-text
• Claude / GPT — the brain (provider-agnostic)
• Cartesia — text-to-speech
• FastAPI + React — API & dashboard
Inbound + outbound calls, with transcripts captured.

4/ The fun engineering wasn't the LLM — it was the voice plumbing:
• endpointing/VAD tuning so it doesn't talk over you
• keeping turn-taking latency low enough to feel human
• routing inbound numbers to the right resume context
Most "voice agent" demos skip this. This is the real wiring.

5/ It's MIT-licensed and built to be contributed to:
• CI, tests, CONTRIBUTING, Code of Conduct
• 5 good-first-issues ready to grab
• clear roadmap (DB backend, more STT/TTS providers, Twilio support)
If you build voice AI, I'd love your eyes on it. ⭐ https://github.com/Adawodu/PROXIMUS

6/ Yes, it speaks on live calls — so it ships with a Responsible Use policy. It's for your own calls, with your own resume. The prompt is built to be truthful and to disclose it's an AI if asked. Not for impersonating anyone. Built with @livekit @telnyx @AnthropicAI.

## LinkedIn post

> I just open-sourced Proximus — a real-time AI voice agent that answers recruiter screening calls using your resume as context.
>
> When a recruiter calls, it picks up, answers their questions in first person from your resume — concise, natural, and importantly, truthful: it only states what's actually on the resume and defers rather than fabricating.
>
> The interesting part for me was the engineering underneath. A production voice agent isn't just "call an LLM." It's a real-time pipeline:
>
> 📞 SIP telephony (Telnyx) → 🗣️ speech-to-text (Deepgram) → 🧠 LLM (Claude/GPT) → 🔊 text-to-speech (Cartesia), orchestrated with LiveKit Agents.
>
> The genuinely hard problems were endpointing and turn-taking — getting the timing right so the agent doesn't interrupt you and doesn't feel laggy. Most voice-AI demos skip that wiring; I wanted a reference implementation that doesn't.
>
> It's MIT-licensed, with CI, tests, docs, and a handful of good-first-issues for anyone who wants to build on it. There's also a Responsible Use policy — it speaks on live calls, so it's designed for your own calls with your own resume, and to disclose it's an AI if asked.
>
> If you work on voice AI, agents, or telephony, I'd love your feedback — and contributions are very welcome.
>
> 🔗 https://github.com/Adawodu/PROXIMUS
> [attach the demo video]
>
> #OpenSource #AI #VoiceAI #LiveKit #SoftwareEngineering
