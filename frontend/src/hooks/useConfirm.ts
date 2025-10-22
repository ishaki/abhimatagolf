import { useConfirm as useConfirmContext } from '@/components/ui/confirm-dialog';

// Re-export the main hook for convenience
export const useConfirm = useConfirmContext;

// Export types for TypeScript users
export type { ConfirmOptions, ConfirmVariant } from '@/components/ui/confirm-dialog';
