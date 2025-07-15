
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
  Ghost
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface StoreData {
  id: string;
  name: string;
  url: string;
  status: 'completed' | 'running' | 'failed';
  lastScrape: string;
  productCount: number;
}

const mockStores: StoreData[] = [
  {
    id: '1',
    name: 'Fresh Grocer - Cedar Grove',
    url: 'https://freshgrocer.com/cedar-grove',
    status: 'completed',
    lastScrape: '2 hours ago',
    productCount: 1247
  },
  {
    id: '2',
    name: 'Whole Foods Market',
    url: 'https://wholefoodsmarket.com/store-123',
    status: 'running',
    lastScrape: '5 minutes ago',
    productCount: 892
  },
  {
    id: '3',
    name: 'SuperMart Downtown',
    url: 'https://supermart.com/downtown',
    status: 'failed',
    lastScrape: '1 day ago',
    productCount: 0
  }
];

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'completed':
      return {
        icon: CheckCircle,
        text: 'Completed',
        className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
      };
    case 'running':
      return {
        icon: Clock,
        text: 'Running',
        className: 'bg-amber-500/10 text-amber-400 border-amber-500/20 animate-pulse'
      };
    case 'failed':
      return {
        icon: XCircle,
        text: 'Failed',
        className: 'bg-red-500/10 text-red-400 border-red-500/20'
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
  const [stores] = useState(mockStores);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

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
          {stores.map((store) => {
            const statusConfig = getStatusConfig(store.status);
            const StatusIcon = statusConfig.icon;
            
            return (
              <Card 
                key={store.id} 
                className="p-4 bg-sidebar-accent border-sidebar-border hover:bg-sidebar-accent/80 transition-all duration-300 hover:shadow-lg rounded-xl group"
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-white text-sm lg:text-base truncate group-hover:text-sidebar-primary transition-colors duration-200">
                      {store.name}
                    </h3>
                    <p className="text-xs text-sidebar-foreground truncate mt-1">
                      {store.url}
                    </p>
                  </div>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-8 w-8 p-0 text-sidebar-foreground hover:text-white hover:bg-sidebar-accent/50 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200"
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent 
                      align="end" 
                      className="w-48 bg-sidebar-accent border-sidebar-border rounded-xl"
                    >
                      <DropdownMenuItem className="text-white hover:bg-sidebar-primary/20 hover:text-sidebar-primary rounded-lg">
                        <Zap className="h-4 w-4 mr-2" />
                        Re-scrape Store
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-white hover:bg-sidebar-primary/20 hover:text-sidebar-primary rounded-lg">
                        <Store className="h-4 w-4 mr-2" />
                        Edit Store Info
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-red-400 hover:bg-red-500/20 hover:text-red-300 rounded-lg">
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
                  
                  <span className="text-xs text-sidebar-foreground">
                    {store.lastScrape}
                  </span>
                </div>
                
                <div className="text-xs text-white bg-sidebar-accent/30 rounded-lg px-3 py-2">
                  <span className="font-medium text-sidebar-primary">
                    {store.productCount.toLocaleString()}
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
