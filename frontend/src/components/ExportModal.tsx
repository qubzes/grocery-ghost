
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Download, FileText } from "lucide-react";

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const exportColumns = [
  { id: 'productName', label: 'Product Name', defaultChecked: true },
  { id: 'currentPrice', label: 'Current Price', defaultChecked: true },
  { id: 'originalPrice', label: 'Original Price', defaultChecked: true },
  { id: 'size', label: 'Size', defaultChecked: true },
  { id: 'department', label: 'Department', defaultChecked: true },
  { id: 'dietaryTags', label: 'Dietary Tags', defaultChecked: false },
];

export const ExportModal = ({ isOpen, onClose }: ExportModalProps) => {
  const [selectedColumns, setSelectedColumns] = useState<string[]>(
    exportColumns.filter(col => col.defaultChecked).map(col => col.id)
  );

  const handleColumnToggle = (columnId: string, checked: boolean) => {
    if (checked) {
      setSelectedColumns([...selectedColumns, columnId]);
    } else {
      setSelectedColumns(selectedColumns.filter(id => id !== columnId));
    }
  };

  const handleExport = () => {
    // Handle CSV export with selected columns
    console.log('Exporting columns:', selectedColumns);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md rounded-xl shadow-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-gray-900 flex items-center">
            <FileText className="h-6 w-6 mr-2 text-blue-600" />
            Export Product Data
          </DialogTitle>
        </DialogHeader>
        
        <div className="mt-4">
          <p className="text-gray-600 mb-6">
            Choose which columns to include in your CSV export
          </p>
          
          <div className="space-y-4">
            {exportColumns.map((column) => (
              <div key={column.id} className="flex items-center space-x-3">
                <Checkbox
                  id={column.id}
                  checked={selectedColumns.includes(column.id)}
                  onCheckedChange={(checked) => 
                    handleColumnToggle(column.id, checked as boolean)
                  }
                  className="data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                />
                <Label 
                  htmlFor={column.id} 
                  className="text-sm font-medium text-gray-700 cursor-pointer"
                >
                  {column.label}
                </Label>
              </div>
            ))}
          </div>

          <div className="flex gap-3 pt-6">
            <Button
              onClick={handleExport}
              className="flex-1 h-12 bg-blue-600 hover:bg-blue-700 text-white font-semibold"
              disabled={selectedColumns.length === 0}
            >
              <Download className="h-4 w-4 mr-2" />
              Download CSV
            </Button>
            <Button
              onClick={onClose}
              variant="outline"
              className="px-8 h-12 border-gray-300 text-gray-700"
            >
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
