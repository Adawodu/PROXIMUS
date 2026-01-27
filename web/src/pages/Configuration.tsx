export function Configuration() {
  const envVars = [
    { name: 'LIVEKIT_URL', desc: 'LiveKit server WebSocket URL' },
    { name: 'LIVEKIT_API_KEY', desc: 'LiveKit API key' },
    { name: 'LIVEKIT_API_SECRET', desc: 'LiveKit API secret' },
    { name: 'TELNYX_API_KEY', desc: 'Telnyx API key' },
    { name: 'TELNYX_PHONE_NUMBER', desc: 'Telnyx phone number (E.164)' },
    { name: 'TELNYX_SIP_USERNAME', desc: 'SIP digest auth username' },
    { name: 'TELNYX_SIP_PASSWORD', desc: 'SIP digest auth password' },
    { name: 'ANTHROPIC_API_KEY', desc: 'Anthropic API key (if using Claude)' },
    { name: 'OPENAI_API_KEY', desc: 'OpenAI API key (if using GPT)' },
    { name: 'DEEPGRAM_API_KEY', desc: 'Deepgram STT API key' },
    { name: 'CARTESIA_API_KEY', desc: 'Cartesia TTS API key' },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Configuration</h2>

      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 font-medium text-gray-900">Required Environment Variables</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead>
              <tr>
                <th className="px-4 py-2 text-left font-medium text-gray-500">Variable</th>
                <th className="px-4 py-2 text-left font-medium text-gray-500">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {envVars.map((v) => (
                <tr key={v.name}>
                  <td className="px-4 py-2 font-mono text-indigo-700">{v.name}</td>
                  <td className="px-4 py-2 text-gray-600">{v.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 font-medium text-gray-900">Setup Steps</h3>
        <ol className="list-decimal space-y-2 pl-5 text-sm text-gray-700">
          <li>Create accounts: Telnyx, LiveKit Cloud, Deepgram, Cartesia, and your AI provider (Anthropic or OpenAI)</li>
          <li>Configure Telnyx: Create an FQDN SIP connection with digest auth credentials, purchase a phone number, and link it to the SIP connection</li>
          <li>Configure LiveKit SIP: Create an inbound trunk pointing to your Telnyx number, then create a dispatch rule routing to the <code className="rounded bg-gray-100 px-1">proximus-agent</code></li>
          <li>Copy <code className="rounded bg-gray-100 px-1">.env.example</code> to <code className="rounded bg-gray-100 px-1">.env</code> and fill in all values</li>
          <li>Start the API: <code className="rounded bg-gray-100 px-1">python -m proximus api</code></li>
          <li>Start the agent: <code className="rounded bg-gray-100 px-1">python -m proximus agent dev</code></li>
          <li>Start the web UI: <code className="rounded bg-gray-100 px-1">cd web && npm run dev</code></li>
          <li>Upload a resume and link your phone number via the dashboard</li>
        </ol>
      </div>
    </div>
  );
}
