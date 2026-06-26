import { useQuery } from '@tanstack/react-query';
import { getInteraction } from '../lib/api.js';

// the single interaction query, enabled once an id is selected.
// while the record is pending it is polled so the fields appear once ready.
export function useInteraction(id) {
  return useQuery({
    queryKey: ['interactions', id],
    queryFn: () => getInteraction(id),
    enabled: id != null,
    refetchInterval: (query) =>
      query.state.data?.record?.status === 'pending' ? 2000 : false,
  });
}
