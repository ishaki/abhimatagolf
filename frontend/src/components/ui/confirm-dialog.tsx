import React, { createContext, useContext, useState, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Trash2, Info } from 'lucide-react';

export type ConfirmVariant = 'danger' | 'warning' | 'info';

export interface ConfirmOptions {
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: ConfirmVariant;
  icon?: React.ReactNode;
}

interface ConfirmDialogContextType {
  confirm: (options: ConfirmOptions) => Promise<boolean>;
}

const ConfirmDialogContext = createContext<ConfirmDialogContextType | null>(null);

interface ConfirmDialogProviderProps {
  children: React.ReactNode;
}

export const ConfirmDialogProvider: React.FC<ConfirmDialogProviderProps> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [options, setOptions] = useState<ConfirmOptions | null>(null);
  const [resolve, setResolve] = useState<((value: boolean) => void) | null>(null);

  const confirm = useCallback((confirmOptions: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolvePromise) => {
      setOptions(confirmOptions);
      setResolve(() => resolvePromise);
      setIsOpen(true);
    });
  }, []);

  const handleConfirm = useCallback(() => {
    setIsOpen(false);
    if (resolve) {
      resolve(true);
      setResolve(null);
    }
  }, [resolve]);

  const handleCancel = useCallback(() => {
    setIsOpen(false);
    if (resolve) {
      resolve(false);
      setResolve(null);
    }
  }, [resolve]);

  const getVariantStyles = (variant: ConfirmVariant = 'info') => {
    switch (variant) {
      case 'danger':
        return {
          icon: <Trash2 className="h-6 w-6 text-red-600" />,
          confirmButtonClass: 'bg-red-600 hover:bg-red-700 text-white',
          accentColor: 'text-red-600',
        };
      case 'warning':
        return {
          icon: <AlertTriangle className="h-6 w-6 text-orange-600" />,
          confirmButtonClass: 'bg-orange-600 hover:bg-orange-700 text-white',
          accentColor: 'text-orange-600',
        };
      case 'info':
      default:
        return {
          icon: <Info className="h-6 w-6 text-blue-600" />,
          confirmButtonClass: 'bg-blue-600 hover:bg-blue-700 text-white',
          accentColor: 'text-blue-600',
        };
    }
  };

  return (
    <ConfirmDialogContext.Provider value={{ confirm }}>
      {children}
      <Dialog open={isOpen} onOpenChange={handleCancel}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              {options?.icon || getVariantStyles(options?.variant).icon}
              <span className={getVariantStyles(options?.variant).accentColor}>
                {options?.title}
              </span>
            </DialogTitle>
            {options?.description && (
              <DialogDescription className="text-gray-600 mt-2">
                {options.description}
              </DialogDescription>
            )}
          </DialogHeader>
          
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              className="border-gray-300 text-gray-700 hover:bg-gray-50"
            >
              {options?.cancelText || 'Cancel'}
            </Button>
            <Button
              type="button"
              onClick={handleConfirm}
              className={getVariantStyles(options?.variant).confirmButtonClass}
            >
              {options?.confirmText || 'Confirm'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </ConfirmDialogContext.Provider>
  );
};

export const useConfirm = (): ConfirmDialogContextType => {
  const context = useContext(ConfirmDialogContext);
  if (!context) {
    throw new Error('useConfirm must be used within a ConfirmDialogProvider');
  }
  return context;
};

// Helper functions for common confirmation patterns
export const useConfirmHelpers = () => {
  const { confirm } = useConfirm();

  const confirmDelete = useCallback(
    (itemName: string, additionalWarning?: string) => {
      return confirm({
        title: `Delete ${itemName}?`,
        description: additionalWarning || `Are you sure you want to delete ${itemName}? This action cannot be undone.`,
        variant: 'danger',
        confirmText: 'Delete',
        cancelText: 'Cancel',
      });
    },
    [confirm]
  );

  const confirmAction = useCallback(
    (actionName: string, description?: string) => {
      return confirm({
        title: `${actionName}?`,
        description: description || `Are you sure you want to ${actionName.toLowerCase()}?`,
        variant: 'warning',
        confirmText: 'Continue',
        cancelText: 'Cancel',
      });
    },
    [confirm]
  );

  return {
    confirm,
    confirmDelete,
    confirmAction,
  };
};
