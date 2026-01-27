import { useState, useEffect, useCallback } from 'react';
import type { CallSummary, CallDetail } from '../types';
import { listCalls, getCall } from '../services/api';

export function useCalls() {
  const [calls, setCalls] = useState<CallSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listCalls();
      setCalls(data.calls);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load calls');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { calls, loading, error, refresh };
}

export function useCallDetail(callId: string | null) {
  const [call, setCall] = useState<CallDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!callId) {
      setCall(null);
      return;
    }
    setLoading(true);
    setError(null);
    getCall(callId)
      .then(setCall)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load call'))
      .finally(() => setLoading(false));
  }, [callId]);

  return { call, loading, error };
}
