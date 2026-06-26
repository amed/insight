import { useQuery } from '@tanstack/react-query';
import { getInteractions } from '../lib/api.js';

// the interactions list query
export function useInteractions() {
  return useQuery({ queryKey: ['interactions'], queryFn: getInteractions });
}
