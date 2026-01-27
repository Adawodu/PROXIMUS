import { TrashIcon } from '@heroicons/react/24/outline';
import type { PhoneLink } from '../../types';
import { deletePhoneLink } from '../../services/api';

interface Props {
  links: PhoneLink[];
  loading: boolean;
  onChanged: () => void;
}

export function PhoneLinkList({ links, loading, onChanged }: Props) {
  const handleDelete = async (phone: string) => {
    if (!confirm(`Unlink ${phone}?`)) return;
    await deletePhoneLink(phone);
    onChanged();
  };

  if (loading) return <p className="text-sm text-gray-500">Loading...</p>;

  if (links.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-500">No phone numbers linked yet.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Phone</th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Candidate</th>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase text-gray-500">Resume ID</th>
            <th className="px-6 py-3 text-right text-xs font-medium uppercase text-gray-500">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {links.map((l) => (
            <tr key={l.phone} className="hover:bg-gray-50">
              <td className="px-6 py-4 text-sm font-mono text-gray-900">{l.phone}</td>
              <td className="px-6 py-4 text-sm text-gray-700">{l.candidate_name}</td>
              <td className="px-6 py-4 text-sm text-gray-500 font-mono">{l.resume_id.slice(0, 8)}</td>
              <td className="px-6 py-4 text-right">
                <button onClick={() => handleDelete(l.phone)} className="text-red-600 hover:text-red-800">
                  <TrashIcon className="h-4 w-4 inline" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
