export function Guide() {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">How-To Guide</h2>

      <div className="space-y-4">
        <Step
          number={1}
          title="Set Up External Services"
          content={
            <ol className="list-decimal space-y-2 pl-5 text-sm text-gray-700">
              <li>Create accounts at <strong>Telnyx</strong>, <strong>LiveKit Cloud</strong>, <strong>Deepgram</strong>, <strong>Cartesia</strong>, and your AI provider (Anthropic or OpenAI)</li>
              <li>In the Telnyx portal, create an <strong>FQDN SIP Connection</strong> with digest auth credentials</li>
              <li>Purchase or assign a phone number and link it to the SIP connection</li>
              <li>In LiveKit, create an <strong>inbound SIP trunk</strong> and a <strong>dispatch rule</strong> routing to <code className="rounded bg-gray-100 px-1">proximus-agent</code></li>
              <li>
                Run the setup helper for generated commands:
                <pre className="mt-1 rounded bg-gray-900 p-2 text-xs text-green-400">python -m proximus sip setup</pre>
              </li>
            </ol>
          }
        />

        <Step
          number={2}
          title="Configure Environment"
          content={
            <div className="text-sm text-gray-700 space-y-2">
              <p>Copy <code className="rounded bg-gray-100 px-1">.env.example</code> to <code className="rounded bg-gray-100 px-1">.env</code> and fill in all API keys and credentials.</p>
              <p>See the <a href="/config" className="text-indigo-600 hover:underline">Configuration</a> page for all required variables.</p>
            </div>
          }
        />

        <Step
          number={3}
          title="Start the Services"
          content={
            <div className="space-y-2">
              <pre className="rounded bg-gray-900 p-3 text-xs text-green-400 space-y-1">
{`# Terminal 1: REST API
python -m proximus api

# Terminal 2: Voice Agent
python -m proximus agent dev

# Terminal 3: Web Dashboard
cd web && npm run dev`}
              </pre>
            </div>
          }
        />

        <Step
          number={4}
          title="Upload Your Resume"
          content={
            <div className="text-sm text-gray-700 space-y-2">
              <p>Go to the <a href="/resumes" className="text-indigo-600 hover:underline">Resumes</a> page and upload your resume file (PDF, DOCX, or TXT).</p>
              <p>Optionally enter a candidate name. If left blank, the system will try to extract it from the file.</p>
            </div>
          }
        />

        <Step
          number={5}
          title="Link Your Phone Number"
          content={
            <div className="text-sm text-gray-700 space-y-2">
              <p>Go to the <a href="/phone-links" className="text-indigo-600 hover:underline">Phone Links</a> page.</p>
              <p>Enter your Telnyx phone number in E.164 format (e.g. <code className="rounded bg-gray-100 px-1">+12481234567</code>) and select the resume you uploaded.</p>
              <p>This tells PROXIMUS which resume to use when a call comes in from that number.</p>
            </div>
          }
        />

        <Step
          number={6}
          title="Test a Call"
          content={
            <div className="text-sm text-gray-700 space-y-2">
              <p>Have a recruiter bot (or any phone) call your Telnyx number. PROXIMUS will:</p>
              <ol className="list-decimal pl-5 space-y-1">
                <li>Receive the call via Telnyx SIP</li>
                <li>Route it through LiveKit to the voice agent</li>
                <li>Look up the caller's phone number to find the linked resume</li>
                <li>Answer as the candidate using the resume context</li>
              </ol>
            </div>
          }
        />

        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
          <h3 className="text-sm font-medium text-amber-800">Troubleshooting</h3>
          <ul className="mt-2 list-disc pl-5 text-sm text-amber-700 space-y-1">
            <li><strong>Agent not connecting</strong> — Check <code className="rounded bg-amber-100 px-1">LIVEKIT_URL</code>, <code className="rounded bg-amber-100 px-1">LIVEKIT_API_KEY</code>, and <code className="rounded bg-amber-100 px-1">LIVEKIT_API_SECRET</code> in your .env</li>
            <li><strong>Calls not routing</strong> — Verify your inbound trunk number matches your Telnyx number (E.164 format) and the dispatch rule is active</li>
            <li><strong>Upload fails</strong> — Ensure the API is running on port 8000 and <code className="rounded bg-amber-100 px-1">python-multipart</code> is installed</li>
            <li><strong>Dashboard shows "Offline"</strong> — The API server isn't running. Start it with <code className="rounded bg-amber-100 px-1">python -m proximus api</code></li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function Step({ number, title, content }: { number: number; title: string; content: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="flex items-start gap-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-sm font-bold text-white">
          {number}
        </div>
        <div className="flex-1">
          <h3 className="mb-3 text-lg font-medium text-gray-900">{title}</h3>
          {content}
        </div>
      </div>
    </div>
  );
}
