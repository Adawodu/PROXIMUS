import { useEffect, useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/solid';
import type { Resume } from '../../types';
import { getResumeContext, getResumePhones, updateResumeVoice } from '../../services/api';

interface Props {
  resume: Resume;
  onClose: () => void;
}

export function ResumeDetailModal({ resume, onClose }: Props) {
  const [tab, setTab] = useState<'preview' | 'prompt'>('preview');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [phones, setPhones] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [voice, setVoice] = useState(resume.voice ?? '');
  const [savingVoice, setSavingVoice] = useState(false);
  const [voiceSaved, setVoiceSaved] = useState(false);

  const handleSaveVoice = async () => {
    setSavingVoice(true);
    setVoiceSaved(false);
    try {
      await updateResumeVoice(resume.id, voice.trim());
      setVoiceSaved(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save voice');
    } finally {
      setSavingVoice(false);
    }
  };

  useEffect(() => {
    setError(null);
    getResumeContext(resume.id)
      .then((d) => setSystemPrompt(d.system_prompt))
      .catch((e) =>
        setError(e instanceof Error ? e.message : 'Failed to load system prompt')
      );
    // Linked phones are supplementary — a failure here shouldn't block the modal.
    getResumePhones(resume.id)
      .then((d) => setPhones(d.phones))
      .catch(() => setPhones([]));
  }, [resume.id]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Resume: ${resume.candidate_name}`}
        className="w-full max-w-2xl rounded-lg bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">{resume.candidate_name}</h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>

        <div className="border-b">
          <nav className="flex gap-4 px-6">
            {(['preview', 'prompt'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`border-b-2 py-3 text-sm font-medium transition-colors ${
                  tab === t ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {t === 'preview' ? 'Resume Content' : 'System Prompt'}
              </button>
            ))}
          </nav>
        </div>

        <div className="max-h-96 overflow-y-auto p-6">
          {tab === 'preview' ? (
            <pre className="whitespace-pre-wrap text-sm text-gray-700">{resume.content_preview}</pre>
          ) : error ? (
            <p role="alert" className="text-sm text-red-600">{error}</p>
          ) : (
            <pre className="whitespace-pre-wrap text-sm text-gray-700">{systemPrompt || 'Loading...'}</pre>
          )}
        </div>

        <div className="border-t px-6 py-3 space-y-2">
          <label htmlFor="tts-voice" className="block text-xs font-medium text-gray-500 uppercase">
            TTS Voice (Cartesia voice id)
          </label>
          <div className="flex gap-2">
            <input
              id="tts-voice"
              type="text"
              value={voice}
              onChange={(e) => {
                setVoice(e.target.value);
                setVoiceSaved(false);
              }}
              placeholder="Leave blank for the default voice"
              className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
            <button
              onClick={handleSaveVoice}
              disabled={savingVoice}
              className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {savingVoice ? 'Saving...' : 'Save'}
            </button>
          </div>
          {voiceSaved && <p className="text-xs text-emerald-600">Voice saved.</p>}
          {phones.length > 0 && (
            <p className="text-xs text-gray-500">Linked phones: {phones.join(', ')}</p>
          )}
        </div>
      </div>
    </div>
  );
}
