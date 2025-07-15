
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Rocket, Zap, Globe } from "lucide-react";

export const ScrapeInputForm = () => {
  const [url, setUrl] = useState("");
  const [isScrapingActive, setIsScrapingActive] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleStartScraping = () => {
    if (!url.trim()) return;
    
    setIsScrapingActive(true);
    setProgress(0);
    
    // Simulate scraping progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsScrapingActive(false);
          return 100;
        }
        return prev + Math.random() * 15;
      });
    }, 500);
  };

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
              disabled={isScrapingActive}
            />
          </div>
          
          <Button 
            onClick={handleStartScraping}
            disabled={!url.trim() || isScrapingActive}
            className="h-14 lg:h-16 px-6 lg:px-8 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold text-base lg:text-lg rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
          >
            {isScrapingActive ? (
              <>
                <Zap className="h-5 w-5 lg:h-6 lg:w-6 mr-3 animate-pulse" />
                Scraping...
              </>
            ) : (
              <>
                <Rocket className="h-5 w-5 lg:h-6 lg:w-6 mr-3" />
                Start Scraping
              </>
            )}
          </Button>
        </div>
        
        {isScrapingActive && (
          <div className="space-y-4">
            <div className="flex justify-between items-center text-sm lg:text-base font-medium text-foreground">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-primary rounded-full animate-pulse"></div>
                <span>Extracting product data...</span>
              </div>
              <span className="text-primary font-bold">{Math.round(progress)}%</span>
            </div>
            <Progress 
              value={progress} 
              className="h-3 bg-muted/30 backdrop-blur-sm rounded-full overflow-hidden"
            />
          </div>
        )}
      </div>
    </div>
  );
};
