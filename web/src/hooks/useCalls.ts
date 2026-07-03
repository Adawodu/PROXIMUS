import { useQuery } from '@tanstack/react-query';
import { listCalls, getCall } from '../services/api';

export function useCalls() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['calls'],
    queryFn: listCalls,
  });

  return {
    calls: data?.calls ?? [],
    loading: isLoading,
    error: error ? (error as Error).message : null,
    refresh: refetch,
  };
}

export function useCallDetail(callId: string | null) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['call', callId],
    queryFn: () => getCall(callId as string),
    enabled: !!callId,
  });

  return {
    call: data ?? null,
    loading: isLoading,
    error: error ? (error as Error).message : null,
  };
}
