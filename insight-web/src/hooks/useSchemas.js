import { useQuery } from '@tanstack/react-query';
import { getSchemas } from '../lib/api.js';

// the schema list; it only changes with a core restart, so it is fetched once
export function useSchemas() {
  return useQuery({ queryKey: ['schemas'], queryFn: getSchemas, staleTime: Infinity });
}
