# Responsible Use

PROXIMUS is a real-time AI voice agent that can speak on a phone call using your
own resume as context. Voice AI is powerful, and using it on live phone calls
carries real responsibilities. Please read this before deploying.

## Intended Use

PROXIMUS is intended as:

- A **personal screening assistant** — a tool *you* run, on *your* own calls,
  using *your* own resume, to help handle or rehearse recruiter screening
  conversations.
- A **reference implementation** — an open-source example of building a
  production-style voice agent with LiveKit, SIP telephony, STT, an LLM, and TTS.

## Principles

1. **Consent and disclosure.** Many jurisdictions regulate recording and
   automated/AI participation in calls (e.g. two-party consent laws, and rules
   requiring disclosure that the caller is interacting with AI). You are
   responsible for complying with the laws that apply to you and the other party.
   When in doubt, disclose that an AI assistant is being used.

2. **Honesty.** The agent should represent real information. Do not use PROXIMUS
   to fabricate qualifications, misstate experience, or deceive the other party
   about material facts. The default system prompt instructs the agent to be
   truthful and to defer rather than invent.

3. **Your data, your responsibility.** Resumes and transcripts contain personal
   information. Store them securely, limit access, and delete what you don't need.
   The API ships with no authentication — do not expose it publicly without
   adding your own.

4. **Other people's data.** Don't upload someone else's resume or place calls
   that impersonate another person without their explicit consent.

## Prohibited Uses

Do not use PROXIMUS to:

- Impersonate another person without their consent.
- Conduct fraud, scams, social engineering, or harassment.
- Place mass / automated unsolicited calls (robocalling), or violate
  telemarketing / TCPA-style regulations.
- Evade disclosure where AI-interaction disclosure is legally required.
- Process personal data unlawfully.

## Disclaimer

PROXIMUS is provided "as is" under the [MIT License](LICENSE), without warranty.
The authors are not liable for how you use it. Compliance with applicable laws —
including telephony, recording, consent, AI-disclosure, and data-protection laws
in your jurisdiction — is your responsibility.
