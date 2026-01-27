import { useState, useEffect, useCallback } from 'react';
import type { PhoneLink } from '../types';
import { listPhoneLinks } from '../services/api';

export function usePhoneLinks() {
  const [links, setLinks] = useState<PhoneLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      setLoading(true);
      const data = await listPhoneLinks();
      setLinks(data.links);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load phone links');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  return { links, loading, error, refetch: fetch };
}
