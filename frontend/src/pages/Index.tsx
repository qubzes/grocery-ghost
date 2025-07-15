
import { StoreSidebar } from "@/components/StoreSidebar";
import { DashboardHeader } from "@/components/DashboardHeader";
import { ScrapeInputForm } from "@/components/ScrapeInputForm";
import { ProductsTable } from "@/components/ProductsTable";

const Index = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background/95 to-accent/20 flex">
      <StoreSidebar />
      
      <div className="flex-1 lg:p-8 p-4 bg-gradient-to-b from-card/50 to-background">
        <DashboardHeader />
        <ScrapeInputForm />
        <ProductsTable />
      </div>
    </div>
  );
};

export default Index;
