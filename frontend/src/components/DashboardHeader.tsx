
import { Ghost } from "lucide-react";

export const DashboardHeader = () => {
  return (
    <div className="mb-8 lg:mb-12">
      <div className="flex items-center gap-3 mb-4">
        <div className="relative">
          <Ghost className="h-10 w-10 lg:h-12 lg:w-12 text-primary float-animation" />
          <div className="absolute inset-0 h-10 w-10 lg:h-12 lg:w-12 text-primary/20 animate-ping" />
        </div>
        <div>
          <h1 className="text-3xl lg:text-5xl font-bold bg-gradient-to-r from-primary via-accent-foreground to-primary bg-clip-text text-transparent">
            GroceryGhost
          </h1>
          <div className="text-xs lg:text-sm text-muted-foreground font-medium tracking-wider uppercase">
            Intelligence Console
          </div>
        </div>
      </div>
      
      <p className="text-muted-foreground text-base lg:text-lg leading-relaxed max-w-2xl">
        Track and extract real-time grocery data across store chains with AI-powered intelligence
      </p>
    </div>
  );
};
