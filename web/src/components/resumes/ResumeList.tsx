import { useState } from 'react';
import { TrashIcon, EyeIcon } from '@heroicons/react/24/outline';
import type { Resume } from '../../types';
import { deleteResume } from '../../services/api';
import { ResumeDetailModal } from './ResumeDetailModal';

interface Props {
  resumes: Resume[];
  loading: boolean;
  onChanged: () => void;
}

export function ResumeList({ resumes, loading, onChanged }: Props) {
  const [selected, setSelected] = useState<Resume | null>(null);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this resume?')) return;
    await deleteResume(id);
    onChanged();
  };

  if (loading) return <p className="text-sm text-gray-500">Loading...</p>;

  if (resumes.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-500">No resumes uploaded yet.</p>
      </div>
    );
  }

  return (
    <>
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Candidate</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Created</th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {resumes.map((r) => (
              <tr key={r.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{r.candidate_name}</td>
                <td className="px-6 py-4 text-sm text-gray-500 font-mono">{r.id.slice(0, 8)}</td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {new Date(r.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 text-right">
                  <button onClick={() => setSelected(r)} className="mr-2 text-indigo-600 hover:text-indigo-800">
                    <EyeIcon className="h-4 w-4 inline" />
                  </button>
                  <button onClick={() => handleDelete(r.id)} className="text-red-600 hover:text-red-800">
                    <TrashIcon className="h-4 w-4 inline" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <ResumeDetailModal resume={selected} onClose={() => setSelected(null)} />
      )}
    </>
  );
}
