import { useState, useEffect, useCallback } from 'react';
import type { Resume } from '../types';
import { listResumes } from '../services/api';

export function useResumes() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const data = await listResumes();
      setResumes(data.resumes);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load resumes');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  return { resumes, loading, error, refetch: fetch };
}
