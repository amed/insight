import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createInteraction } from '../lib/api.js';

// an interaction is created from a file (plus optional fields); the list is refreshed on success
export function useCreateInteraction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, fields }) => createInteraction(file, fields),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['interactions'] }),
  });
}
