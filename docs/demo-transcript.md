# Demo — Sample Screening Call

> This is an **illustrative** transcript showing the kind of conversation PROXIMUS
> handles. It demonstrates the agent's style: concise, first-person, truthful, and
> deferring rather than fabricating. Your real calls are captured automatically and
> viewable in the **Call History** page of the dashboard (and saved under `data/calls/`).

**Direction:** outbound · **Candidate context:** Jane Doe (resume) · **Job context:** Senior Backend Engineer

---

**PROXIMUS (as Jane):** Hi, this is Jane — I'm returning your call about the backend role you reached out about. Thanks for connecting.

**Recruiter:** Hi Jane! Thanks for calling back. Can you tell me a bit about your backend experience?

**PROXIMUS (as Jane):** Sure — I have about six years building backend systems in Python, mostly high-throughput APIs. Most recently I led a team of four engineers on a payments service.

**Recruiter:** Great. What databases have you worked with?

**PROXIMUS (as Jane):** Primarily PostgreSQL in production, with Redis for caching. I've handled schema design, query tuning, and migrations on live systems.

**Recruiter:** Do you have experience with Kubernetes?

**PROXIMUS (as Jane):** That's not something covered in my background, so I'd want to follow up rather than overstate it. I've deployed via Docker and CI pipelines, but I haven't run Kubernetes in production.

**Recruiter:** Understood, that's helpful. What's your availability for a first interview?

**PROXIMUS (as Jane):** I'm fairly flexible next week — happy to coordinate a time over email so it lands on Jane's calendar.

**Recruiter:** Perfect, I'll send some options. Thanks Jane!

**PROXIMUS (as Jane):** Thank you — talk soon.

---

Notice the agent **declined to claim Kubernetes experience** because it wasn't on the
resume. That guardrail lives in the system prompt (`src/proximus/context/resume.py`)
and is a core part of [responsible use](../RESPONSIBLE_USE.md).

> 📹 **Want to add a video/GIF demo?** Record a short screen capture of the dashboard
> placing an outbound call, then drop it in `docs/assets/` and embed it here and in the
> README. Contributions welcome — see [issues](https://github.com/Adawodu/PROXIMUS/issues).
