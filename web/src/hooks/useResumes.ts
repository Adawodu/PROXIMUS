import { useQuery } from '@tanstack/react-query';
import { listResumes } from '../services/api';

export function useResumes() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['resumes'],
    queryFn: listResumes,
  });

  return {
    resumes: data?.resumes ?? [],
    loading: isLoading,
    error: error ? (error as Error).message : null,
    refetch,
  };
}
