/**
 * Permissions Hook
 * 
 * Provides role-based access control (RBAC) functions for the frontend.
 * Uses AuthContext to determine user permissions.
 */

import { useAuth } from '@/contexts/AuthContext';

export enum UserRole {
  SUPER_ADMIN = 'super_admin',
  EVENT_ADMIN = 'event_admin',
  EVENT_USER = 'event_user',
}

export interface UsePermissionsReturn {
  // Role checks
  isSuperAdmin: () => boolean;
  isEventAdmin: () => boolean;
  isEventUser: () => boolean;
  
  // Permission checks
  canManageCourses: () => boolean;
  canManageUsers: () => boolean;
  canCreateEvents: () => boolean;
  canAccessWinners: (eventId?: number, event?: any) => boolean;
  canViewWinners: (eventId?: number, event?: any) => boolean;
  canConfigureWinners: (eventId?: number, event?: any) => boolean;
  canCreateEventUsers: () => boolean;
  canManageParticipants: (eventId?: number, event?: any) => boolean;
  canManageScores: (eventId?: number, event?: any) => boolean;
  
  // Event-specific checks
  canAccessEvent: (eventId: number, event?: any) => boolean;
  canEditEvent: (eventId: number, event?: any) => boolean;
  
  // Current user info
  currentUser: any;
  userRole: string | null;
}

export const usePermissions = (): UsePermissionsReturn => {
  const { user } = useAuth();
  
  // Role checks
  const isSuperAdmin = (): boolean => {
    return user?.role === UserRole.SUPER_ADMIN;
  };
  
  const isEventAdmin = (): boolean => {
    return user?.role === UserRole.EVENT_ADMIN;
  };
  
  const isEventUser = (): boolean => {
    return user?.role === UserRole.EVENT_USER;
  };
  
  // Permission checks
  const canManageCourses = (): boolean => {
    return isSuperAdmin();
  };
  
  const canManageUsers = (): boolean => {
    return isSuperAdmin();
  };
  
  const canAccessWinners = (eventId?: number, event?: any): boolean => {
    if (!user) return false;
    
    // Super admins can access winners for all events
    if (isSuperAdmin()) return true;
    
    // Event admins can only access winners for events they created
    if (isEventAdmin()) {
      if (event && event.created_by === user.id) {
        return true;
      }
      // If no event data provided, we can't determine ownership
      return false;
    }
    
    return false;
  };
  
  const canViewWinners = (eventId?: number, event?: any): boolean => {
    if (!user) return false;
    
    // Super admins can view winners for all events
    if (isSuperAdmin()) return true;
    
    // Event admins can only view winners for events they created
    if (isEventAdmin()) {
      if (event && event.created_by === user.id) {
        return true;
      }
      // If no event data provided, we can't determine ownership
      return false;
    }
    
    return false;
  };
  
  const canConfigureWinners = (eventId?: number, event?: any): boolean => {
    if (!user) return false;
    
    // Super admins can configure winners for all events
    if (isSuperAdmin()) return true;
    
    // Event admins can only configure winners for events they created
    if (isEventAdmin()) {
      if (event && event.created_by === user.id) {
        return true;
      }
      // If no event data provided, we can't determine ownership
      return false;
    }
    
    return false;
  };
  
  const canCreateEventUsers = (): boolean => {
    return isSuperAdmin() || isEventAdmin();
  };
  
  const canCreateEvents = (): boolean => {
    return isSuperAdmin() || isEventAdmin();
  };
  
  const canManageParticipants = (eventId?: number, event?: any): boolean => {
    if (!user) return false;
    
    // Super admins can manage participants for all events
    if (isSuperAdmin()) return true;
    
    // Event admins can only manage participants for events they created
    if (isEventAdmin()) {
      if (event && event.created_by === user.id) {
        return true;
      }
      // If no event data provided, we can't determine ownership
      return false;
    }
    
    // Event users can only manage participants for events they're assigned to
    if (isEventUser()) {
      // This would need to be checked against UserEvent relationships
      // For now, assume they can manage participants for events they're viewing
      return true;
    }
    
    return false;
  };
  
  const canManageScores = (eventId?: number, event?: any): boolean => {
    if (!user) return false;
    
    // Super admins can manage scores for all events
    if (isSuperAdmin()) return true;
    
    // Event admins can only manage scores for events they created
    if (isEventAdmin()) {
      if (event && event.created_by === user.id) {
        return true;
      }
      // If no event data provided, we can't determine ownership
      return false;
    }
    
    // Event users can only manage scores for events they're assigned to
    if (isEventUser()) {
      // This would need to be checked against UserEvent relationships
      // For now, assume they can manage scores for events they're viewing
      return true;
    }
    
    return false;
  };
  
  // Event-specific checks
  const canAccessEvent = (eventId: number, event?: any): boolean => {
    if (!user) return false;
    
    // Super admins can access all events
    if (isSuperAdmin()) return true;
    
    // Event admins can access ALL events (read-only for events they didn't create)
    if (isEventAdmin()) return true;
    
    // Event users can only access events they're assigned to
    if (isEventUser()) {
      // This would need to be checked against UserEvent relationships
      // For now, assume they can access events they're viewing
      return true;
    }
    
    return false;
  };
  
  const canEditEvent = (eventId: number, event?: any): boolean => {
    if (!user) return false;
    
    // Super admins can edit all events
    if (isSuperAdmin()) return true;
    
    // Event admins can only edit events they created
    if (isEventAdmin()) {
      // Check if the event was created by the current user
      if (event && event.created_by === user.id) {
        return true;
      }
      // If no event data provided, we can't determine ownership
      return false;
    }
    
    // Event users cannot edit events
    return false;
  };
  
  return {
    // Role checks
    isSuperAdmin,
    isEventAdmin,
    isEventUser,
    
    // Permission checks
    canManageCourses,
    canManageUsers,
    canCreateEvents,
    canAccessWinners,
    canViewWinners,
    canConfigureWinners,
    canCreateEventUsers,
    canManageParticipants,
    canManageScores,
    
    // Event-specific checks
    canAccessEvent,
    canEditEvent,
    
    // Current user info
    currentUser: user,
    userRole: user?.role || null,
  };
};
