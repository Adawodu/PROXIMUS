import { useEffect, useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/solid';
import type { Resume } from '../../types';
import { getResumeContext, getResumePhones } from '../../services/api';

interface Props {
  resume: Resume;
  onClose: () => void;
}

export function ResumeDetailModal({ resume, onClose }: Props) {
  const [tab, setTab] = useState<'preview' | 'prompt'>('preview');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [phones, setPhones] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

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

        {phones.length > 0 && (
          <div className="border-t px-6 py-3">
            <p className="text-xs text-gray-500">
              Linked phones: {phones.join(', ')}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
