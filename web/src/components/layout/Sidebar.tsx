import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  DocumentTextIcon,
  PhoneIcon,
  BookOpenIcon,
  CogIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

const navItems = [
  { to: '/', icon: HomeIcon, label: 'Dashboard' },
  { to: '/resumes', icon: DocumentTextIcon, label: 'Resumes' },
  { to: '/phone-links', icon: PhoneIcon, label: 'Phone Links' },
  { to: '/calls', icon: ClockIcon, label: 'Call History' },
  { to: '/guide', icon: BookOpenIcon, label: 'How-To Guide' },
  { to: '/config', icon: CogIcon, label: 'Configuration' },
];

export function Sidebar() {
  return (
    <nav className="w-56 shrink-0 border-r border-gray-200 bg-gray-50 p-4">
      <ul className="space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <li key={to}>
            <NavLink
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`
              }
            >
              <Icon className="h-5 w-5" />
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
