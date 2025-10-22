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
  canAccessWinners: () => boolean;
  canViewWinners: () => boolean;
  canCreateEventUsers: () => boolean;
  canManageParticipants: (eventId?: number) => boolean;
  canManageScores: (eventId?: number) => boolean;
  
  // Event-specific checks
  canAccessEvent: (eventId: number) => boolean;
  canEditEvent: (eventId: number) => boolean;
  
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
  
  const canAccessWinners = (): boolean => {
    return isSuperAdmin() || isEventAdmin();
  };
  
  const canViewWinners = (): boolean => {
    return isSuperAdmin() || isEventAdmin();
  };
  
  const canCreateEventUsers = (): boolean => {
    return isSuperAdmin() || isEventAdmin();
  };
  
  const canCreateEvents = (): boolean => {
    return isSuperAdmin() || isEventAdmin();
  };
  
  const canManageParticipants = (eventId?: number): boolean => {
    if (!user) return false;
    
    // Super admins can manage participants for all events
    if (isSuperAdmin()) return true;
    
    // Event admins can manage participants for events they created
    if (isEventAdmin()) {
      // For now, assume event admins can manage participants for events they're viewing
      return true;
    }
    
    // Event users can only manage participants for events they're assigned to
    if (isEventUser()) {
      // This would need to be checked against UserEvent relationships
      // For now, assume they can manage participants for events they're viewing
      return true;
    }
    
    return false;
  };
  
  const canManageScores = (eventId?: number): boolean => {
    if (!user) return false;
    
    // Super admins can manage scores for all events
    if (isSuperAdmin()) return true;
    
    // Event admins can manage scores for events they created
    if (isEventAdmin()) {
      // For now, assume event admins can manage scores for events they're viewing
      return true;
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
  const canAccessEvent = (eventId: number): boolean => {
    if (!user) return false;
    
    // Super admins can access all events
    if (isSuperAdmin()) return true;
    
    // Event admins can access events they created
    if (isEventAdmin()) {
      // This would need to be checked against the event's creator_id
      // For now, we'll assume event admins can access events they're viewing
      return true;
    }
    
    // Event users can only access events they're assigned to
    if (isEventUser()) {
      // This would need to be checked against UserEvent relationships
      // For now, we'll assume they can access events they're viewing
      return true;
    }
    
    return false;
  };
  
  const canEditEvent = (eventId: number): boolean => {
    if (!user) return false;
    
    // Super admins can edit all events
    if (isSuperAdmin()) return true;
    
    // Event admins can edit events they created
    if (isEventAdmin()) {
      // This would need to be checked against the event's creator_id
      return true;
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
