import { useState } from 'react';
import { DocumentTextIcon, PhoneIcon, SignalIcon } from '@heroicons/react/24/solid';
import { Link } from 'react-router-dom';
import { StatusCard } from '../components/dashboard/StatusCard';
import { useResumes } from '../hooks/useResumes';
import { usePhoneLinks } from '../hooks/usePhoneLinks';
import { useHealth } from '../hooks/useHealth';
import { useCalls } from '../hooks/useCalls';
import { OutboundCallModal } from '../components/calls/OutboundCallModal';

export function Dashboard() {
  const { resumes, loading: resumesLoading, error: resumesError } = useResumes();
  const { links, loading: linksLoading, error: linksError } = usePhoneLinks();
  const { health, error: healthError } = useHealth();
  const { calls, loading: callsLoading, error: callsError } = useCalls();
  const [showCallModal, setShowCallModal] = useState(false);

  const errors = [resumesError, linksError, callsError].filter(Boolean) as string[];

  // Show a dash while a count is still loading rather than a misleading 0.
  const count = (isLoading: boolean, n: number) => (isLoading ? '—' : n);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <button
          onClick={() => setShowCallModal(true)}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Call Recruiter
        </button>
      </div>

      {errors.length > 0 && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          Failed to load dashboard data: {errors.join('; ')}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <StatusCard title="Resumes" value={count(resumesLoading, resumes.length)} icon={DocumentTextIcon} color="bg-indigo-600" />
        <StatusCard title="Phone Links" value={count(linksLoading, links.length)} icon={PhoneIcon} color="bg-emerald-600" />
        <StatusCard title="Total Calls" value={count(callsLoading, calls.length)} icon={PhoneIcon} color="bg-purple-600" />
        <StatusCard title="API Status" value={healthError ? 'Offline' : health ? 'Healthy' : '…'} icon={SignalIcon} color={health && !healthError ? 'bg-green-600' : 'bg-red-600'} />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Link
          to="/resumes"
          className="rounded-lg border border-gray-200 bg-white p-6 hover:border-indigo-300 hover:shadow-sm transition-all"
        >
          <h3 className="font-medium text-gray-900">Upload Resume</h3>
          <p className="mt-1 text-sm text-gray-500">Add a candidate resume for the voice agent to use.</p>
        </Link>
        <Link
          to="/phone-links"
          className="rounded-lg border border-gray-200 bg-white p-6 hover:border-indigo-300 hover:shadow-sm transition-all"
        >
          <h3 className="font-medium text-gray-900">Link Phone Number</h3>
          <p className="mt-1 text-sm text-gray-500">Map a phone number to a resume for call routing.</p>
        </Link>
        <Link
          to="/calls"
          className="rounded-lg border border-gray-200 bg-white p-6 hover:border-indigo-300 hover:shadow-sm transition-all"
        >
          <h3 className="font-medium text-gray-900">Call History</h3>
          <p className="mt-1 text-sm text-gray-500">View transcripts from past screening calls.</p>
        </Link>
      </div>

      <OutboundCallModal open={showCallModal} onClose={() => setShowCallModal(false)} />
    </div>
  );
}
