
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Store, Rocket } from "lucide-react";

interface AddStoreModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AddStoreModal = ({ isOpen, onClose }: AddStoreModalProps) => {
  const [storeName, setStoreName] = useState("");
  const [storeUrl, setStoreUrl] = useState("");
  const [storeTag, setStoreTag] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle form submission
    console.log('Adding store:', { storeName, storeUrl, storeTag });
    onClose();
    // Reset form
    setStoreName("");
    setStoreUrl("");
    setStoreTag("");
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md rounded-xl shadow-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-gray-900 flex items-center">
            <Store className="h-6 w-6 mr-2 text-emerald-600" />
            Add New Store
          </DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-6 mt-4">
          <div className="space-y-2">
            <Label htmlFor="storeName" className="text-sm font-semibold text-gray-700">
              Store Name
            </Label>
            <Input
              id="storeName"
              type="text"
              value={storeName}
              onChange={(e) => setStoreName(e.target.value)}
              placeholder="e.g., Fresh Grocer - Cedar Grove"
              className="h-12 text-base border-2 focus:border-emerald-500"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="storeUrl" className="text-sm font-semibold text-gray-700">
              Store URL
            </Label>
            <Input
              id="storeUrl"
              type="url"
              value={storeUrl}
              onChange={(e) => setStoreUrl(e.target.value)}
              placeholder="https://www.examplegrocerystore.com/store/xyz"
              className="h-12 text-base border-2 focus:border-emerald-500"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="storeTag" className="text-sm font-semibold text-gray-700">
              Optional Tag or Nickname
            </Label>
            <Input
              id="storeTag"
              type="text"
              value={storeTag}
              onChange={(e) => setStoreTag(e.target.value)}
              placeholder="e.g., Downtown Location"
              className="h-12 text-base border-2 focus:border-emerald-500"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              className="flex-1 h-12 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
            >
              <Rocket className="h-4 w-4 mr-2" />
              Add & Start Scraping
            </Button>
            <Button
              type="button"
              onClick={onClose}
              variant="outline"
              className="px-8 h-12 border-gray-300 text-gray-700"
            >
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
