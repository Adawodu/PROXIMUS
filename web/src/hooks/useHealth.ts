import { useState, useEffect, useCallback } from 'react';
import type { HealthResponse } from '../types';
import { getHealth } from '../services/api';

export function useHealth(pollInterval = 30000) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      const data = await getHealth();
      setHealth(data);
      setError(null);
    } catch {
      setHealth(null);
      setError('API unreachable');
    }
  }, []);

  useEffect(() => {
    fetch();
    const id = setInterval(fetch, pollInterval);
    return () => clearInterval(id);
  }, [fetch, pollInterval]);

  return { health, error, refetch: fetch };
}
