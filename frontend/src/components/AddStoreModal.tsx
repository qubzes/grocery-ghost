import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Store, Rocket, Loader2 } from "lucide-react";
import { useStartScraping } from "@/hooks/useApi";
import { toast } from "sonner";

interface AddStoreModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AddStoreModal = ({ isOpen, onClose }: AddStoreModalProps) => {
  const [storeUrl, setStoreUrl] = useState("");
  const startScrapingMutation = useStartScraping();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!storeUrl.trim()) {
      toast.error("Please enter a valid store URL");
      return;
    }

    try {
      await startScrapingMutation.mutateAsync({ url: storeUrl.trim() });
      toast.success("Store added and scraping started!");

      // Reset form and close modal
      setStoreUrl("");
      onClose();
    } catch (error) {
      // Error is already handled in the mutation
    }
  };

  const handleClose = () => {
    if (!startScrapingMutation.isPending) {
      setStoreUrl("");
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md rounded-xl shadow-2xl">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-gray-900 flex items-center">
            <Store className="h-6 w-6 mr-2 text-emerald-600" />
            Add New Store
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6 mt-4">
          <div className="space-y-2">
            <Label
              htmlFor="storeUrl"
              className="text-sm font-semibold text-gray-700"
            >
              Store URL
            </Label>
            <Input
              id="storeUrl"
              type="url"
              value={storeUrl}
              onChange={(e) => setStoreUrl(e.target.value)}
              placeholder="https://www.examplegrocerystore.com"
              className="h-12 text-base border-2 focus:border-emerald-500"
              required
              disabled={startScrapingMutation.isPending}
            />
            <p className="text-xs text-gray-500">
              Enter the main URL of the grocery store. The system will
              automatically extract the store name and start scraping.
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              className="flex-1 h-12 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
              disabled={!storeUrl.trim() || startScrapingMutation.isPending}
            >
              {startScrapingMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Rocket className="h-4 w-4 mr-2" />
                  Add & Start Scraping
                </>
              )}
            </Button>
            <Button
              type="button"
              onClick={handleClose}
              variant="outline"
              className="px-8 h-12 border-gray-300 text-gray-700"
              disabled={startScrapingMutation.isPending}
            >
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
