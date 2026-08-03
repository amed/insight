import { useQuery } from '@tanstack/react-query';
import { getSchemaSummary } from '../lib/api.js';

// the value counts for one schema version, optionally one pipeline
export function useSummary(schema, pipeline) {
  return useQuery({
    queryKey: ['summary', schema && schema.id, pipeline],
    queryFn: () => getSchemaSummary(schema.name, schema.version, pipeline),
    enabled: schema != null,
  });
}
