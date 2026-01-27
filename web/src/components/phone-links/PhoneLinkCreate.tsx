import { useState } from 'react';
import type { Resume } from '../../types';
import { createPhoneLink } from '../../services/api';

interface Props {
  resumes: Resume[];
  onCreated: () => void;
}

export function PhoneLinkCreate({ resumes, onCreated }: Props) {
  const [phone, setPhone] = useState('');
  const [resumeId, setResumeId] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone || !resumeId) return;
    setError(null);
    setSaving(true);
    try {
      await createPhoneLink({ phone, resume_id: resumeId });
      setPhone('');
      setResumeId('');
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to link');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <h3 className="mb-4 text-sm font-medium text-gray-900">Link Phone Number</h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="tel"
          placeholder="Phone number (e.g. +12481234567)"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          required
        />
        <select
          value={resumeId}
          onChange={(e) => setResumeId(e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          required
        >
          <option value="">Select a resume...</option>
          {resumes.map((r) => (
            <option key={r.id} value={r.id}>{r.candidate_name}</option>
          ))}
        </select>
        <button
          type="submit"
          disabled={saving}
          className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {saving ? 'Linking...' : 'Link Phone'}
        </button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </form>
    </div>
  );
}
