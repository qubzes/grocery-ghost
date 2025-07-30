
import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { Download, ExternalLink, Filter, Trash2, Package, Search, ArrowUpDown, Loader2 } from "lucide-react";
import { ExportModal } from "@/components/ExportModal";
import { Input } from "@/components/ui/input";
import { useSessions, useSession, useExportSession } from "@/hooks/useApi";
import type { Product } from "@/lib/api";

const getTagColor = (tag: string) => {
  switch (tag.toLowerCase()) {
    case 'organic':
      return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/30';
    case 'protein':
      return 'bg-blue-500/20 text-blue-400 border-blue-500/30 hover:bg-blue-500/30';
    case 'whole grain':
      return 'bg-amber-500/20 text-amber-400 border-amber-500/30 hover:bg-amber-500/30';
    case 'low fat':
      return 'bg-purple-500/20 text-purple-400 border-purple-500/30 hover:bg-purple-500/30';
    case 'gluten-free':
      return 'bg-pink-500/20 text-pink-400 border-pink-500/30 hover:bg-pink-500/30';
    case 'vegan':
      return 'bg-green-500/20 text-green-400 border-green-500/30 hover:bg-green-500/30';
    default:
      return 'bg-muted/50 text-muted-foreground border-muted hover:bg-muted/70';
  }
};

const getDepartmentColor = (department: string) => {
  switch (department?.toLowerCase()) {
    case 'produce':
      return 'bg-green-500/20 text-green-400 border-green-500/30';
    case 'meat':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'dairy':
      return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30';
    case 'bakery':
      return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'frozen':
      return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
    case 'pantry':
      return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    default:
      return 'bg-muted/50 text-muted-foreground border-muted';
  }
};

const parsePrice = (priceString: string | null): number | null => {
  if (!priceString) return null;
  const matches = priceString.match(/[\d,.]+/);
  if (!matches) return null;
  return parseFloat(matches[0].replace(',', ''));
};

export const ProductsTable = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  const { data: sessionsData } = useSessions();
  const { data: sessionData, isLoading: isLoadingSession } = useSession(selectedSessionId);
  const exportMutation = useExportSession();

  // Get the most recent session with products if none is selected
  const defaultSessionId = useMemo(() => {
    if (selectedSessionId) return selectedSessionId;
    
    const sessionsWithProducts = sessionsData?.sessions.filter(s => s.product_count > 0) || [];
    if (sessionsWithProducts.length === 0) return null;
    
    return sessionsWithProducts[0].id;
  }, [sessionsData, selectedSessionId]);

  // Use the default session if no specific session is selected
  const { data: defaultSessionData, isLoading: isLoadingDefault } = useSession(defaultSessionId);
  
  const currentSessionData = sessionData || defaultSessionData;
  const isLoading = isLoadingSession || isLoadingDefault;
  const products = currentSessionData?.products || [];

  const filteredProducts = useMemo(() => {
    return products.filter(product =>
      product.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.category?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [products, searchTerm]);

  const handleExport = async () => {
    if (!currentSessionData) return;
    
    try {
      await exportMutation.mutateAsync({
        sessionId: currentSessionData.session_id,
        filename: `${currentSessionData.name}_products.csv`
      });
    } catch (error) {
      // Error is handled in the mutation
    }
  };

  const allSessions = sessionsData?.sessions || [];
  const sessionsWithProducts = allSessions.filter(s => s.product_count > 0);

  return (
    <>
      <Card className="backdrop-blur-sm bg-card/60 border-border/50 shadow-2xl rounded-2xl overflow-hidden">
        <div className="p-6 lg:p-8 border-b border-border/50 bg-gradient-to-r from-card/80 to-accent/10">
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-6">
            <div>
              <h2 className="text-2xl lg:text-3xl font-bold text-foreground mb-2">
                Product Intelligence View
              </h2>
              <p className="text-muted-foreground text-sm lg:text-base">
                {isLoading ? (
                  "Loading products..."
                ) : (
                  <>
                    {filteredProducts.length} products extracted
                    {currentSessionData && (
                      <> • {currentSessionData.name}</>
                    )}
                    {currentSessionData?.status === 'in_progress' && (
                      <> • Scraping in progress ({Math.round(currentSessionData.progress)}% complete)</>
                    )}
                  </>
                )}
              </p>
            </div>
            
            <div className="flex flex-wrap gap-3 w-full lg:w-auto">
              {sessionsWithProducts.length > 1 && (
                <select 
                  className="px-3 py-2 bg-background border border-border rounded-xl text-sm"
                  value={defaultSessionId || ""}
                  onChange={(e) => setSelectedSessionId(e.target.value || null)}
                >
                  {sessionsWithProducts.map(session => (
                    <option key={session.id} value={session.id}>
                      {session.name} ({session.product_count} products)
                    </option>
                  ))}
                </select>
              )}
              
              <Button 
                onClick={handleExport}
                disabled={!currentSessionData || products.length === 0 || exportMutation.isPending}
                className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-300 rounded-xl"
              >
                {exportMutation.isPending ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Export CSV
              </Button>
              <Button variant="outline" className="border-border/50 hover:bg-accent/50 rounded-xl">
                <Filter className="h-4 w-4 mr-2" />
                <span className="hidden sm:inline">Filter Results</span>
                <span className="sm:hidden">Filter</span>
              </Button>
            </div>
          </div>
          
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search products or departments..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-background/50 border-border/50 rounded-xl"
            />
          </div>
        </div>
        
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <span className="ml-3 text-muted-foreground">Loading products...</span>
            </div>
          ) : (
            <Table>
              <TableHeader className="bg-accent/30 backdrop-blur-sm">
                <TableRow className="border-border/50 hover:bg-transparent">
                  <TableHead className="font-bold text-foreground text-left py-4 px-6">
                    <div className="flex items-center gap-2">
                      Item
                      <ArrowUpDown className="h-4 w-4" />
                    </div>
                  </TableHead>
                  <TableHead className="font-bold text-foreground text-center py-4 px-4">
                    Current Price
                  </TableHead>
                  <TableHead className="font-bold text-foreground text-center py-4 px-4 hidden sm:table-cell">
                    Original Price
                  </TableHead>
                  <TableHead className="font-bold text-foreground text-center py-4 px-4 hidden md:table-cell">
                    Size
                  </TableHead>
                  <TableHead className="font-bold text-foreground text-center py-4 px-4 hidden lg:table-cell">
                    Image
                  </TableHead>
                  <TableHead className="font-bold text-foreground text-center py-4 px-4">
                    Department
                  </TableHead>
                  <TableHead className="font-bold text-foreground text-left py-4 px-4 hidden md:table-cell">
                    Tags
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredProducts.map((product, index) => (
                  <TableRow 
                    key={product.id} 
                    className={`border-border/30 hover:bg-accent/20 transition-all duration-200 ${
                      index % 2 === 0 ? 'bg-card/20' : 'bg-accent/5'
                    }`}
                  >
                    <TableCell className="font-semibold text-foreground py-4 px-6 max-w-[200px] lg:max-w-none">
                      <div className="truncate lg:whitespace-normal">
                        {product.name || 'Unknown Product'}
                      </div>
                    </TableCell>
                    
                    <TableCell className="text-center py-4 px-4">
                      <div className="text-emerald-400 font-bold text-lg lg:text-xl">
                        {product.current_price || 'N/A'}
                      </div>
                    </TableCell>
                    
                    <TableCell className="text-center py-4 px-4 hidden sm:table-cell">
                      {product.original_price ? (
                        <span className="text-muted-foreground line-through text-sm">
                          {product.original_price}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    
                    <TableCell className="text-center py-4 px-4 text-muted-foreground hidden md:table-cell">
                      {product.unit_size || '-'}
                    </TableCell>
                    
                    <TableCell className="text-center py-4 px-4 hidden lg:table-cell">
                      {product.image_url ? (
                        <a 
                          href={product.image_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:text-blue-300 inline-flex items-center font-medium transition-colors duration-200 hover:underline"
                        >
                          View
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    
                    <TableCell className="text-center py-4 px-4">
                      <Badge className={`${getDepartmentColor(product.category)} border text-xs font-medium px-2 py-1 rounded-lg`}>
                        {product.category || 'Unknown'}
                      </Badge>
                    </TableCell>
                    
                    <TableCell className="py-4 px-4 hidden md:table-cell">
                      <div className="flex flex-wrap gap-1">
                        {product.dietary_tags.map((tag) => (
                          <Badge 
                            key={tag} 
                            className={`${getTagColor(tag)} border text-xs px-2 py-1 rounded-lg font-medium transition-colors duration-200`}
                          >
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
        
        {!isLoading && filteredProducts.length === 0 && searchTerm && (
          <div className="text-center py-12 text-muted-foreground">
            <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
            <p className="text-lg">No products found for "{searchTerm}"</p>
            <p className="text-sm">Try adjusting your search terms</p>
          </div>
        )}
        
        {!isLoading && products.length === 0 && !searchTerm && (
          <div className="text-center py-16 text-muted-foreground">
            <Package className="h-16 w-16 mx-auto mb-6 text-muted-foreground/30 float-animation" />
            <p className="text-xl lg:text-2xl font-semibold mb-2">No products extracted yet</p>
            <p className="text-sm lg:text-base">Start by entering a grocery store URL above</p>
          </div>
        )}
      </Card>

      <ExportModal 
        isOpen={isExportModalOpen} 
        onClose={() => setIsExportModalOpen(false)} 
      />
    </>
  );
};
