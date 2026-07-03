import { useQuery } from '@tanstack/react-query';
import { listPhoneLinks } from '../services/api';

export function usePhoneLinks() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['phoneLinks'],
    queryFn: listPhoneLinks,
  });

  return {
    links: data?.links ?? [],
    loading: isLoading,
    error: error ? (error as Error).message : null,
    refetch,
  };
}
