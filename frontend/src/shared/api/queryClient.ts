import { QueryClient } from '@tanstack/react-query';
import { statusOf } from './errorMessage';

/**
 * Server state for every feature (frontend DEC-005). A 4xx is an answer, not a
 * hiccup: retrying it only delays the message the screen has to show.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: (failures, error) => {
        const status = statusOf(error);
        return (status === null || status >= 500) && failures < 2;
      },
    },
  },
});
