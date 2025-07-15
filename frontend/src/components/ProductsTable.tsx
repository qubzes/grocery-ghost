
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { Download, ExternalLink, Filter, Trash2, Package, Search, ArrowUpDown } from "lucide-react";
import { ExportModal } from "@/components/ExportModal";
import { Input } from "@/components/ui/input";

interface Product {
  id: string;
  name: string;
  currentPrice: number;
  originalPrice?: number;
  unitSize: string;
  imageUrl: string;
  department: string;
  tags: string[];
}

const mockProducts: Product[] = [
  {
    id: '1',
    name: 'Organic Baby Spinach',
    currentPrice: 4.99,
    originalPrice: 5.99,
    unitSize: '5 oz',
    imageUrl: 'https://example.com/spinach.jpg',
    department: 'Produce',
    tags: ['Organic']
  },
  {
    id: '2',
    name: 'Grass-Fed Ground Beef',
    currentPrice: 8.99,
    unitSize: '1 lb',
    imageUrl: 'https://example.com/beef.jpg',
    department: 'Meat',
    tags: ['Protein']
  },
  {
    id: '3',
    name: 'Whole Grain Bread',
    currentPrice: 3.49,
    originalPrice: 3.99,
    unitSize: '24 oz',
    imageUrl: 'https://example.com/bread.jpg',
    department: 'Bakery',
    tags: ['Whole Grain', 'Organic']
  },
  {
    id: '4',
    name: 'Low Fat Greek Yogurt',
    currentPrice: 5.99,
    unitSize: '32 oz',
    imageUrl: 'https://example.com/yogurt.jpg',
    department: 'Dairy',
    tags: ['Low Fat', 'Protein']
  },
  {
    id: '5',
    name: 'Organic Almond Milk',
    currentPrice: 4.29,
    unitSize: '64 fl oz',
    imageUrl: 'https://example.com/almond-milk.jpg',
    department: 'Dairy',
    tags: ['Organic']
  }
];

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
    default:
      return 'bg-muted/50 text-muted-foreground border-muted hover:bg-muted/70';
  }
};

const getDepartmentColor = (department: string) => {
  switch (department.toLowerCase()) {
    case 'produce':
      return 'bg-green-500/20 text-green-400 border-green-500/30';
    case 'meat':
      return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'dairy':
      return 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30';
    case 'bakery':
      return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    default:
      return 'bg-muted/50 text-muted-foreground border-muted';
  }
};

export const ProductsTable = () => {
  const [products] = useState(mockProducts);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const handleClearTable = () => {
    console.log('Clear table');
  };

  const filteredProducts = products.filter(product =>
    product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    product.department.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
                {filteredProducts.length} products extracted • Real-time pricing data
              </p>
            </div>
            
            <div className="flex flex-wrap gap-3 w-full lg:w-auto">
              <Button 
                onClick={() => setIsExportModalOpen(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-300 rounded-xl"
              >
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
              <Button variant="outline" className="border-border/50 hover:bg-accent/50 rounded-xl">
                <Filter className="h-4 w-4 mr-2" />
                <span className="hidden sm:inline">Filter Results</span>
                <span className="sm:hidden">Filter</span>
              </Button>
              <Button variant="outline" className="border-red-500/50 text-red-400 hover:bg-red-500/10 rounded-xl">
                <Trash2 className="h-4 w-4 mr-2" />
                <span className="hidden sm:inline">Clear Table</span>
                <span className="sm:hidden">Clear</span>
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
                      {product.name}
                    </div>
                  </TableCell>
                  
                  <TableCell className="text-center py-4 px-4">
                    <div className="text-emerald-400 font-bold text-lg lg:text-xl">
                      ${product.currentPrice.toFixed(2)}
                    </div>
                  </TableCell>
                  
                  <TableCell className="text-center py-4 px-4 hidden sm:table-cell">
                    {product.originalPrice ? (
                      <span className="text-muted-foreground line-through text-sm">
                        ${product.originalPrice.toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  
                  <TableCell className="text-center py-4 px-4 text-muted-foreground hidden md:table-cell">
                    {product.unitSize}
                  </TableCell>
                  
                  <TableCell className="text-center py-4 px-4 hidden lg:table-cell">
                    <a 
                      href={product.imageUrl} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 inline-flex items-center font-medium transition-colors duration-200 hover:underline"
                    >
                      View
                      <ExternalLink className="h-3 w-3 ml-1" />
                    </a>
                  </TableCell>
                  
                  <TableCell className="text-center py-4 px-4">
                    <Badge className={`${getDepartmentColor(product.department)} border text-xs font-medium px-2 py-1 rounded-lg`}>
                      {product.department}
                    </Badge>
                  </TableCell>
                  
                  <TableCell className="py-4 px-4 hidden md:table-cell">
                    <div className="flex flex-wrap gap-1">
                      {product.tags.map((tag) => (
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
        </div>
        
        {filteredProducts.length === 0 && searchTerm && (
          <div className="text-center py-12 text-muted-foreground">
            <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
            <p className="text-lg">No products found for "{searchTerm}"</p>
            <p className="text-sm">Try adjusting your search terms</p>
          </div>
        )}
        
        {products.length === 0 && (
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
