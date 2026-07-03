import { useQuery } from '@tanstack/react-query';
import { getHealth } from '../services/api';

export function useHealth(pollInterval = 30000) {
  const { data, error, refetch } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: pollInterval,
    staleTime: 0,
    retry: false,
  });

  return {
    health: error ? null : (data ?? null),
    error: error ? 'API unreachable' : null,
    refetch,
  };
}
