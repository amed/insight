import { useQuery } from '@tanstack/react-query';
import { getSteps } from '../lib/api.js';

// the steps query; polled while the record is still processing
export function useSteps(id, poll) {
  return useQuery({
    queryKey: ['steps', id],
    queryFn: () => getSteps(id),
    enabled: id != null,
    refetchInterval: poll ? 2000 : false,
  });
}
