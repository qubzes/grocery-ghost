
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { AddStoreModal } from "@/components/AddStoreModal";
import { 
  Plus, 
  Store, 
  CheckCircle, 
  Clock, 
  XCircle, 
  MoreVertical,
  Zap,
  Ghost,
  Loader2,
  AlertTriangle,
  Eye
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useSessions, useDeleteSession, useStartScraping } from "@/hooks/useApi";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";

const ErrorDetailsDialog = ({ session }: { session: any }) => {
  if (!session.error) return null;

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 w-6 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded-lg"
          title="View error details"
        >
          <AlertTriangle className="h-3 w-3" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="text-red-400 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Error Details for {session.name}
          </DialogTitle>
        </DialogHeader>
        <div className="mt-4">
          <div className="bg-red-950/50 border border-red-500/20 rounded-lg p-4 max-h-96 overflow-y-auto">
            <pre className="text-sm text-red-200 whitespace-pre-wrap font-mono">
              {session.error}
            </pre>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            <p>This error occurred during the scraping process. You can try re-scraping the store to resolve temporary issues.</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'completed':
      return {
        icon: CheckCircle,
        text: 'Completed',
        className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
      };
    case 'in_progress':
      return {
        icon: Clock,
        text: 'In Progress',
        className: 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse'
      };
    case 'queued':
      return {
        icon: Clock,
        text: 'Queued',
        className: 'bg-blue-500/10 text-blue-400 border-blue-500/20'
      };
    case 'failed':
      return {
        icon: XCircle,
        text: 'Failed',
        className: 'bg-red-500/10 text-red-400 border-red-500/20'
      };
    case 'canceled':
      return {
        icon: XCircle,
        text: 'Canceled',
        className: 'bg-gray-500/10 text-gray-400 border-gray-500/20'
      };
    default:
      return {
        icon: Clock,
        text: 'Unknown',
        className: 'bg-muted/50 text-muted-foreground border-muted'
      };
  }
};

export const StoreSidebar = () => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const { data: sessionsData, isLoading, error } = useSessions();
  const deleteSessionMutation = useDeleteSession();
  const startScrapingMutation = useStartScraping();

  const sessions = sessionsData?.sessions || [];

  const handleDeleteSession = async (sessionId: string, sessionName: string) => {
    if (window.confirm(`Are you sure you want to delete "${sessionName}"? This action cannot be undone.`)) {
      try {
        await deleteSessionMutation.mutateAsync(sessionId);
      } catch (error) {
        // Error is handled in the mutation
      }
    }
  };

  const handleReScrapeStore = async (url: string) => {
    try {
      await startScrapingMutation.mutateAsync({ url });
      toast.success("Re-scraping started!");
    } catch (error) {
      // Error is handled in the mutation
    }
  };

  const formatLastScrape = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return 'Unknown';
    }
  };

  return (
    <>
      <div className="w-80 lg:w-96 bg-sidebar border-r border-sidebar-border flex flex-col shadow-lg">
        {/* Header */}
        <div className="p-6 border-b border-sidebar-border bg-sidebar">
          <div className="flex items-center gap-3 mb-4">
            <Ghost className="h-6 w-6 text-sidebar-primary float-animation" />
            <h2 className="text-xl font-bold text-white">
              Store Tracker
            </h2>
          </div>
          
          <Button 
            onClick={() => setIsAddModalOpen(true)}
            className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold shadow-lg hover:shadow-xl transition-all duration-300 rounded-xl"
          >
            <Plus className="h-5 w-5 mr-2" />
            Add New Store
          </Button>
        </div>

        {/* Stores List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-sidebar-primary" />
              <span className="ml-2 text-sidebar-foreground">Loading sessions...</span>
            </div>
          )}

          {error && (
            <div className="text-center py-8 text-red-400">
              <p>Failed to load sessions</p>
              <p className="text-sm text-sidebar-foreground mt-1">
                Make sure the backend is running
              </p>
            </div>
          )}

          {!isLoading && !error && sessions.length === 0 && (
            <div className="text-center py-8 text-sidebar-foreground">
              <Store className="h-12 w-12 mx-auto mb-4 text-sidebar-primary/50" />
              <p className="text-sm">No stores added yet</p>
              <p className="text-xs mt-1">Click "Add New Store" to get started</p>
            </div>
          )}

          {sessions.map((session) => {
            const statusConfig = getStatusConfig(session.status);
            const StatusIcon = statusConfig.icon;
            
            return (
              <Card 
                key={session.id} 
                className="p-4 bg-sidebar-accent border-sidebar-border hover:bg-sidebar-accent/80 transition-all duration-300 hover:shadow-lg rounded-xl group"
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-white text-sm lg:text-base truncate group-hover:text-sidebar-primary transition-colors duration-200">
                      {session.name}
                    </h3>
                    <p className="text-xs text-sidebar-foreground truncate mt-1">
                      {session.url}
                    </p>
                  </div>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-8 w-8 p-0 text-sidebar-foreground hover:text-white hover:bg-sidebar-accent/50 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200"
                        disabled={deleteSessionMutation.isPending}
                      >
                        {deleteSessionMutation.isPending ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <MoreVertical className="h-4 w-4" />
                        )}
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent 
                      align="end" 
                      className="w-48 bg-sidebar-accent border-sidebar-border rounded-xl"
                    >
                      <DropdownMenuItem 
                        className="text-white hover:bg-sidebar-primary/20 hover:text-sidebar-primary rounded-lg"
                        onClick={() => handleReScrapeStore(session.url)}
                        disabled={startScrapingMutation.isPending}
                      >
                        <Zap className="h-4 w-4 mr-2" />
                        Re-scrape Store
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        className="text-red-400 hover:bg-red-500/20 hover:text-red-300 rounded-lg"
                        onClick={() => handleDeleteSession(session.id, session.name)}
                        disabled={deleteSessionMutation.isPending}
                      >
                        <XCircle className="h-4 w-4 mr-2" />
                        Delete Store
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                
                <div className="flex items-center justify-between mb-3">
                  <Badge className={`${statusConfig.className} border text-xs px-2 py-1 rounded-lg font-medium`}>
                    <StatusIcon className="h-3 w-3 mr-1" />
                    {statusConfig.text}
                  </Badge>
                  
                  <div className="flex items-center gap-2">
                    {session.error && session.status === 'failed' && (
                      <ErrorDetailsDialog session={session} />
                    )}
                    <span className="text-xs text-sidebar-foreground">
                      {formatLastScrape(session.started_at)}
                    </span>
                  </div>
                </div>
                
                {session.status === 'in_progress' && session.total_pages > 0 && (
                  <div className="mb-3">
                    <div className="flex justify-between text-xs text-sidebar-foreground mb-1">
                      <span>Progress</span>
                      <span>{Math.round((session.scraped_pages / session.total_pages) * 100)}%</span>
                    </div>
                    <div className="w-full bg-sidebar-accent/30 rounded-full h-1.5">
                      <div 
                        className="bg-sidebar-primary h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${(session.scraped_pages / session.total_pages) * 100}%` }}
                      />
                    </div>
                  </div>
                )}
                
                <div className="text-xs text-white bg-sidebar-accent/30 rounded-lg px-3 py-2">
                  <span className="font-medium text-sidebar-primary">
                    {session.product_count.toLocaleString()}
                  </span> products extracted
                </div>
              </Card>
            );
          })}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-sidebar-border bg-sidebar">
          <div className="text-center text-xs text-sidebar-foreground">
            <div className="flex items-center justify-center gap-2 mb-1">
              <Ghost className="h-4 w-4 text-sidebar-primary" />
              <span className="font-medium text-white">GroceryGhost</span>
            </div>
            <div>Real-time grocery intelligence</div>
          </div>
        </div>
      </div>

      <AddStoreModal 
        isOpen={isAddModalOpen} 
        onClose={() => setIsAddModalOpen(false)} 
      />
    </>
  );
};
