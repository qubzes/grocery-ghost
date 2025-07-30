
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Rocket, Zap, Globe } from "lucide-react";
import { useStartScraping } from "@/hooks/useApi";
import { toast } from "sonner";

export const ScrapeInputForm = () => {
  const [url, setUrl] = useState("");
  const startScrapingMutation = useStartScraping();

  const handleStartScraping = async () => {
    if (!url.trim()) {
      toast.error("Please enter a valid URL");
      return;
    }
    
    try {
      await startScrapingMutation.mutateAsync({ url: url.trim() });
      setUrl(""); // Clear the input after successful submission
    } catch (error) {
      // Error is already handled in the mutation
    }
  };

  const isLoading = startScrapingMutation.isPending;

  return (
    <div className="mb-8 lg:mb-12">
      <div className="bg-card/60 backdrop-blur-sm p-6 lg:p-8 rounded-2xl border border-border/50 shadow-2xl">
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Globe className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Paste a store URL here... (e.g., https://grocery-store.com)"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="h-14 lg:h-16 pl-12 text-base lg:text-lg border-2 border-border/50 focus:border-primary bg-background/50 backdrop-blur-sm rounded-xl transition-all duration-300 hover:shadow-lg focus:shadow-xl"
              disabled={isLoading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !isLoading) {
                  handleStartScraping();
                }
              }}
            />
          </div>
          
          <Button 
            onClick={handleStartScraping}
            disabled={!url.trim() || isLoading}
            className="h-14 lg:h-16 px-6 lg:px-8 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-base lg:text-lg rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
          >
            {isLoading ? (
              <>
                <Zap className="h-5 w-5 lg:h-6 lg:w-6 mr-3 animate-pulse" />
                Starting...
              </>
            ) : (
              <>
                <Rocket className="h-5 w-5 lg:h-6 lg:w-6 mr-3" />
                Start Scraping
              </>
            )}
          </Button>
        </div>
        
        {isLoading && (
          <div className="space-y-4">
            <div className="flex justify-between items-center text-sm lg:text-base font-medium text-foreground">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-primary rounded-full animate-pulse"></div>
                <span>Validating URL and starting scraper...</span>
              </div>
            </div>
            <Progress 
              value={undefined} 
              className="h-3 bg-muted/30 backdrop-blur-sm rounded-full overflow-hidden"
            />
          </div>
        )}
      </div>
    </div>
  );
};
