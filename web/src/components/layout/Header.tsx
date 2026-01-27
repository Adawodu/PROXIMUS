import { SignalIcon, SignalSlashIcon } from '@heroicons/react/24/solid';
import { useHealth } from '../../hooks/useHealth';

export function Header() {
  const { health, error } = useHealth();

  return (
    <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white font-bold text-sm">
          P
        </div>
        <h1 className="text-xl font-semibold text-gray-900">PROXIMUS</h1>
      </div>
      <div className="flex items-center gap-2 text-sm">
        {health ? (
          <>
            <SignalIcon className="h-4 w-4 text-green-500" />
            <span className="text-green-700">Healthy</span>
            <span className="text-gray-400">v{health.version}</span>
          </>
        ) : (
          <>
            <SignalSlashIcon className="h-4 w-4 text-red-500" />
            <span className="text-red-700">{error || 'Offline'}</span>
          </>
        )}
      </div>
    </header>
  );
}
