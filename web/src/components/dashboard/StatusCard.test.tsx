import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DocumentTextIcon } from '@heroicons/react/24/solid';
import { StatusCard } from './StatusCard';

describe('StatusCard', () => {
  it('renders the title and value', () => {
    render(<StatusCard title="Resumes" value={7} icon={DocumentTextIcon} color="bg-indigo-600" />);
    expect(screen.getByText('Resumes')).toBeInTheDocument();
    expect(screen.getByText('7')).toBeInTheDocument();
  });

  it('renders a string value (e.g. loading dash)', () => {
    render(<StatusCard title="Calls" value="—" icon={DocumentTextIcon} color="bg-purple-600" />);
    expect(screen.getByText('—')).toBeInTheDocument();
  });
});
