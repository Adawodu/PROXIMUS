import { useState, useEffect, useRef, useCallback } from 'react';
import { Room, RoomEvent, Track, RemoteTrackPublication, ConnectionState } from 'livekit-client';
import type { Resume } from '../../types';
import { listResumes, makeOutboundCall, getListenToken } from '../../services/api';

type CallPhase = 'setup' | 'dialing' | 'connected' | 'ended' | 'error';

// Decorative "audio visualizer" bars. Computed once at module load so renders
// stay pure (no Math.random() during render).
const VISUALIZER_BARS = [...Array(12)].map((_, i) => ({
  height: 20 + Math.random() * 80,
  animationDelay: i * 0.1,
  animationDuration: 0.6 + Math.random() * 0.6,
}));

interface Props {
  open: boolean;
  onClose: () => void;
}

export function OutboundCallModal({ open, onClose }: Props) {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [phone, setPhone] = useState('');
  const [callerId, setCallerId] = useState('');
  const [jobDetail, setJobDetail] = useState('');
  const [phase, setPhase] = useState<CallPhase>('setup');
  const [errorMsg, setErrorMsg] = useState('');
  const [roomName, setRoomName] = useState('');
  const [participants, setParticipants] = useState<string[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const [muted, setMuted] = useState(false);

  const roomRef = useRef<Room | null>(null);
  const audioRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  // Load resumes on open
  useEffect(() => {
    if (open) {
      listResumes().then((data) => {
        setResumes(data.resumes);
        if (data.resumes.length > 0) setSelectedResumeId(data.resumes[0].id);
      });
      setPhase('setup');
      setErrorMsg('');
      setPhone('');
      setCallerId('');
      setJobDetail('');
      setRoomName('');
      setParticipants([]);
      setElapsed(0);
      setMuted(false);
    }
  }, [open]);

  // Cleanup on unmount or close
  const cleanup = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (roomRef.current) {
      roomRef.current.disconnect();
      roomRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.innerHTML = '';
    }
  }, []);

  useEffect(() => {
    if (!open) cleanup();
    return cleanup;
  }, [open, cleanup]);

  // Timer
  useEffect(() => {
    if (phase === 'connected') {
      startTimeRef.current = Date.now();
      timerRef.current = setInterval(() => {
        setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000));
      }, 1000);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, [phase]);

  const formatElapsed = (secs: number) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const attachAudioTrack = useCallback((publication: RemoteTrackPublication) => {
    if (!audioRef.current) return;
    const track = publication.track;
    if (!track || track.kind !== Track.Kind.Audio) return;
    const el = track.attach();
    el.id = `audio-${publication.trackSid}`;
    audioRef.current.appendChild(el);
  }, []);

  const handleDial = async () => {
    if (!phone || !selectedResumeId) return;
    setPhase('dialing');
    setErrorMsg('');

    try {
      // 1. Initiate the outbound call
      const result = await makeOutboundCall({
        phone,
        resume_id: selectedResumeId,
        ...(callerId.trim() ? { caller_id: callerId.trim() } : {}),
        ...(jobDetail.trim() ? { job_detail: jobDetail.trim() } : {}),
      });
      setRoomName(result.call_id);

      // 2. Get a listen token
      const tokenData = await getListenToken(result.call_id);

      // 3. Connect to the room as a listener
      const room = new Room();
      roomRef.current = room;

      room.on(RoomEvent.TrackSubscribed, (_track, publication) => {
        attachAudioTrack(publication);
      });

      room.on(RoomEvent.ParticipantConnected, (participant) => {
        setParticipants((prev) =>
          prev.includes(participant.identity) ? prev : [...prev, participant.identity]
        );
        // setPhase is idempotent; call it directly instead of guarding on the
        // stale `phase` captured by this closure at dial time.
        setPhase('connected');
      });

      room.on(RoomEvent.ParticipantDisconnected, (participant) => {
        setParticipants((prev) => prev.filter((p) => p !== participant.identity));
      });

      room.on(RoomEvent.ConnectionStateChanged, (state: ConnectionState) => {
        if (state === ConnectionState.Disconnected) {
          setPhase('ended');
        }
      });

      room.on(RoomEvent.Disconnected, () => {
        setPhase('ended');
      });

      await room.connect(tokenData.url, tokenData.token);
      setPhase('connected');

      // Attach any existing tracks
      room.remoteParticipants.forEach((p) => {
        setParticipants((prev) =>
          prev.includes(p.identity) ? prev : [...prev, p.identity]
        );
        p.trackPublications.forEach((pub) => {
          if (pub.isSubscribed) attachAudioTrack(pub);
        });
      });
    } catch (err) {
      setPhase('error');
      setErrorMsg(err instanceof Error ? err.message : 'Failed to initiate call');
    }
  };

  const handleHangup = () => {
    cleanup();
    setPhase('ended');
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    const audios = audioRef.current.querySelectorAll('audio');
    audios.forEach((el) => {
      el.muted = !muted;
    });
    setMuted(!muted);
  };

  const handleClose = () => {
    cleanup();
    onClose();
  };

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
    // handleClose is stable enough for this listener; re-subscribing per render is fine.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Call recruiter"
        className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden"
      >
        {/* Header */}
        <div
          className={`px-6 py-4 ${
            phase === 'connected'
              ? 'bg-emerald-600'
              : phase === 'dialing'
              ? 'bg-amber-500'
              : phase === 'ended'
              ? 'bg-gray-600'
              : phase === 'error'
              ? 'bg-red-600'
              : 'bg-indigo-600'
          } text-white transition-colors`}
        >
          <h2 className="text-lg font-bold">
            {phase === 'setup' && 'Call Recruiter'}
            {phase === 'dialing' && 'Dialing...'}
            {phase === 'connected' && 'Call In Progress'}
            {phase === 'ended' && 'Call Ended'}
            {phase === 'error' && 'Call Failed'}
          </h2>
          {phase === 'connected' && (
            <p className="text-sm opacity-90 mt-0.5">{formatElapsed(elapsed)}</p>
          )}
          {roomName && phase !== 'setup' && (
            <p className="text-xs opacity-60 mt-1 font-mono truncate">{roomName}</p>
          )}
        </div>

        <div className="p-6">
          {/* Setup phase */}
          {phase === 'setup' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Resume</label>
                <select
                  value={selectedResumeId}
                  onChange={(e) => setSelectedResumeId(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                >
                  {resumes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.candidate_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Recruiter Phone Number
                </label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+12125551234"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Caller ID (shown to recruiter)
                </label>
                <input
                  type="tel"
                  value={callerId}
                  onChange={(e) => setCallerId(e.target.value)}
                  placeholder="+12125550123"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Leave blank to use the default Telnyx number
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Details (optional)
                </label>
                <textarea
                  value={jobDetail}
                  onChange={(e) => setJobDetail(e.target.value)}
                  placeholder="e.g. Program Manager role at Google, Mountain View CA. Requires 5+ years PM experience..."
                  rows={3}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm resize-none"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Give the agent context about the role being discussed
                </p>
              </div>
            </div>
          )}

          {/* Dialing phase */}
          {phase === 'dialing' && (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber-100 mb-4">
                <svg className="w-8 h-8 text-amber-600 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </div>
              <p className="text-gray-600">Connecting to {phone}...</p>
            </div>
          )}

          {/* Connected phase */}
          {phase === 'connected' && (
            <div className="space-y-4">
              {/* Audio visualizer placeholder */}
              <div className="flex items-center justify-center py-6">
                <div className="flex items-end gap-1 h-12">
                  {VISUALIZER_BARS.map((bar, i) => (
                    <div
                      key={i}
                      className="w-1.5 bg-emerald-500 rounded-full animate-pulse"
                      style={{
                        height: `${bar.height}%`,
                        animationDelay: `${bar.animationDelay}s`,
                        animationDuration: `${bar.animationDuration}s`,
                      }}
                    />
                  ))}
                </div>
              </div>

              {/* Participants */}
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs font-medium text-gray-500 uppercase mb-2">In Call</p>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    <span className="text-gray-700">PROXIMUS Agent</span>
                  </div>
                  {participants.map((p) => (
                    <div key={p} className="flex items-center gap-2 text-sm">
                      <span className="w-2 h-2 rounded-full bg-blue-500" />
                      <span className="text-gray-700">{p}</span>
                    </div>
                  ))}
                  <div className="flex items-center gap-2 text-sm">
                    <span className="w-2 h-2 rounded-full bg-gray-400" />
                    <span className="text-gray-500 italic">You (listening)</span>
                  </div>
                </div>
              </div>

              {/* Controls */}
              <div className="flex items-center justify-center gap-4 pt-2">
                <button
                  onClick={toggleMute}
                  className={`flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition-colors ${
                    muted
                      ? 'bg-gray-200 text-gray-700'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {muted ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    </svg>
                  )}
                  {muted ? 'Unmute' : 'Mute'}
                </button>
                <button
                  onClick={handleHangup}
                  className="flex items-center gap-2 rounded-full bg-red-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-red-700 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.13a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z" />
                  </svg>
                  Leave Call
                </button>
              </div>
            </div>
          )}

          {/* Ended phase */}
          {phase === 'ended' && (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
                <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-gray-700 font-medium">Call ended</p>
              {elapsed > 0 && (
                <p className="text-sm text-gray-500 mt-1">Duration: {formatElapsed(elapsed)}</p>
              )}
              <p className="text-xs text-gray-400 mt-2">Check Call History for the transcript.</p>
            </div>
          )}

          {/* Error phase */}
          {phase === 'error' && (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
                <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p className="text-red-700 font-medium">Failed to connect</p>
              <p className="text-sm text-red-500 mt-1">{errorMsg}</p>
            </div>
          )}

          {/* Hidden audio container */}
          <div ref={audioRef} className="hidden" />
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3">
          {phase === 'setup' && (
            <>
              <button
                onClick={handleClose}
                className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDial}
                disabled={!phone || !selectedResumeId}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                Dial
              </button>
            </>
          )}
          {(phase === 'ended' || phase === 'error') && (
            <button
              onClick={handleClose}
              className="rounded-lg bg-gray-600 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
