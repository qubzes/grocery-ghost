import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiService, type ScrapeRequest } from '@/lib/api';
import { toast } from 'sonner';

// Query keys
export const queryKeys = {
  sessions: ['sessions'] as const,
  session: (id: string) => ['session', id] as const,
};

// Hook to get all sessions
export function useSessions() {
  return useQuery({
    queryKey: queryKeys.sessions,
    queryFn: () => apiService.getSessions(),
    refetchInterval: 2000, // Refetch every 2 seconds for real-time updates
  });
}

// Hook to get a specific session
export function useSession(sessionId: string | null) {
  return useQuery({
    queryKey: queryKeys.session(sessionId || ''),
    queryFn: () => apiService.getSession(sessionId!),
    enabled: !!sessionId,
    refetchInterval: (data) => {
      // Stop refetching if session is completed or failed
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 1000; // Refetch every second for active sessions
    },
  });
}

// Hook to start scraping
export function useStartScraping() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (request: ScrapeRequest) => apiService.startScraping(request),
    onSuccess: (data) => {
      toast.success(`Scraping started for ${data.session_id}`);
      // Invalidate sessions to show the new session immediately
      queryClient.invalidateQueries({ queryKey: queryKeys.sessions });
    },
    onError: (error: Error) => {
      toast.error(`Failed to start scraping: ${error.message}`);
    },
  });
}

// Hook to delete a session
export function useDeleteSession() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (sessionId: string) => apiService.deleteSession(sessionId),
    onSuccess: () => {
      toast.success('Session deleted successfully');
      // Invalidate sessions to update the list
      queryClient.invalidateQueries({ queryKey: queryKeys.sessions });
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete session: ${error.message}`);
    },
  });
}

// Hook to export session data
export function useExportSession() {
  return useMutation({
    mutationFn: async ({ sessionId, filename }: { sessionId: string; filename: string }) => {
      const blob = await apiService.exportSession(sessionId);
      apiService.downloadExport(blob, filename);
      return blob;
    },
    onSuccess: () => {
      toast.success('Export downloaded successfully');
    },
    onError: (error: Error) => {
      toast.error(`Failed to export: ${error.message}`);
    },
  });
}
