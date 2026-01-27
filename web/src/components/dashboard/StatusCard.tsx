import type { ComponentType } from 'react';

interface Props {
  title: string;
  value: string | number;
  icon: ComponentType<{ className?: string }>;
  color: string;
}

export function StatusCard({ title, value, icon: Icon, color }: Props) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="flex items-center gap-4">
        <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}
