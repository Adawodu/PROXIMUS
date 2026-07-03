import { useState } from 'react';
import { useCalls, useCallDetail } from '../hooks/useCalls';

function formatDuration(start: string, end: string | null): string {
  if (!end) return 'In progress';
  const ms = new Date(end).getTime() - new Date(start).getTime();
  const secs = Math.floor(ms / 1000);
  const mins = Math.floor(secs / 60);
  const remSecs = secs % 60;
  return `${mins}m ${remSecs}s`;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString();
}

function TranscriptView({ callId }: { callId: string }) {
  const { call, loading, error } = useCallDetail(callId);

  if (loading) return <p className="text-sm text-gray-500 p-4">Loading transcript...</p>;
  if (error) return <p className="text-sm text-red-500 p-4">{error}</p>;
  if (!call || call.transcript.length === 0)
    return <p className="text-sm text-gray-400 p-4">No transcript available.</p>;

  return (
    <div className="space-y-3 p-4 bg-gray-50 border-t border-gray-200">
      {call.transcript.map((entry, i) => (
        <div
          key={i}
          className={`flex ${entry.role === 'agent' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[75%] rounded-lg px-3 py-2 text-sm ${
              entry.role === 'agent'
                ? 'bg-indigo-100 text-indigo-900'
                : 'bg-white border border-gray-200 text-gray-800'
            }`}
          >
            <div className="font-medium text-xs mb-1 opacity-60">
              {entry.role === 'agent' ? 'Agent' : 'Caller'}
            </div>
            {entry.text}
          </div>
        </div>
      ))}
    </div>
  );
}

export function CallHistory() {
  const { calls, loading, error, refresh } = useCalls();
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Call History</h1>
          <p className="text-sm text-gray-500 mt-1">View transcripts from past calls</p>
        </div>
        <button
          onClick={() => refresh()}
          className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 hover:bg-gray-50"
        >
          Refresh
        </button>
      </div>

      {loading && <p className="text-gray-500">Loading calls...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && calls.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-500">No calls recorded yet.</p>
          <p className="text-sm text-gray-400 mt-1">Calls will appear here after your first conversation.</p>
        </div>
      )}

      {calls.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          {/* Column labels (visual only; each row below is an accessible disclosure button). */}
          <div
            aria-hidden="true"
            className="hidden sm:flex bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase"
          >
            <div className="px-4 py-3 w-[20%]">Date</div>
            <div className="px-4 py-3 w-[20%]">Candidate</div>
            <div className="px-4 py-3 w-[12%]">Direction</div>
            <div className="px-4 py-3 w-[18%]">Phone</div>
            <div className="px-4 py-3 w-[15%]">Duration</div>
            <div className="px-4 py-3 w-[15%]">Turns</div>
          </div>
          <ul className="divide-y divide-gray-200">
            {calls.map((call) => {
              const expanded = expandedId === call.id;
              return (
                <li key={call.id}>
                  <button
                    onClick={() => setExpandedId(expanded ? null : call.id)}
                    aria-expanded={expanded}
                    className="w-full text-left hover:bg-gray-50 transition-colors sm:flex"
                  >
                    <div className="px-4 py-3 text-sm text-gray-700 sm:w-[20%]">{formatTime(call.started_at)}</div>
                    <div className="px-4 py-3 text-sm font-medium text-gray-900 sm:w-[20%]">{call.candidate_name}</div>
                    <div className="px-4 py-3 sm:w-[12%]">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                          call.direction === 'inbound'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-blue-100 text-blue-700'
                        }`}
                      >
                        {call.direction}
                      </span>
                    </div>
                    <div className="px-4 py-3 text-sm text-gray-600 sm:w-[18%]">{call.caller_phone || '—'}</div>
                    <div className="px-4 py-3 text-sm text-gray-600 sm:w-[15%]">{formatDuration(call.started_at, call.ended_at)}</div>
                    <div className="px-4 py-3 text-sm text-gray-600 sm:w-[15%]">{call.turn_count} turns</div>
                  </button>
                  {expanded && (
                    <>
                      {call.summary && (
                        <div className="px-4 py-3 bg-indigo-50 border-t border-indigo-100">
                          <p className="text-xs font-medium text-indigo-500 uppercase mb-1">Summary</p>
                          <p className="text-sm text-indigo-900">{call.summary}</p>
                        </div>
                      )}
                      <TranscriptView callId={call.id} />
                    </>
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
