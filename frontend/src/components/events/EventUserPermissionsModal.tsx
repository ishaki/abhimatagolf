/**
 * Event User Permissions Modal Component
 * 
 * Modal for managing user permissions for an event.
 * Allows super admins to assign event admin permissions to other users.
 */

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Copy, RefreshCw, Users, Shield, AlertTriangle, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { usePermissions } from '@/hooks/usePermissions';
import { getEventUsers, updateEventUserAccess, EventUser } from '@/services/userService';

interface EventUserPermissionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  eventId: number;
  eventName: string;
  eventCreatedBy: number;
  onPermissionsUpdated: () => void;
}

const EventUserPermissionsModal: React.FC<EventUserPermissionsModalProps> = ({
  isOpen,
  onClose,
  eventId,
  eventName,
  eventCreatedBy,
  onPermissionsUpdated,
}) => {
  const { isSuperAdmin } = usePermissions();
  const [eventUsers, setEventUsers] = useState<EventUser[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [updatingUserId, setUpdatingUserId] = useState<number | null>(null);

  // Check permissions - only super admins can manage permissions
  if (!isSuperAdmin()) {
    return null;
  }

  // Load event users when modal opens
  useEffect(() => {
    if (isOpen) {
      loadEventUsers();
    }
  }, [isOpen, eventId]);

  const loadEventUsers = async () => {
    setIsLoading(true);
    try {
      const response = await getEventUsers(eventId);
      setEventUsers(response.users);
    } catch (error) {
      console.error('Error fetching event users:', error);
      toast.error('Failed to load event users');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAccessLevelChange = async (userId: number, newAccessLevel: string) => {
    setUpdatingUserId(userId);
    try {
      await updateEventUserAccess(eventId, userId, newAccessLevel);
      toast.success('User permissions updated successfully');
      
      // Refresh the users list
      await loadEventUsers();
      
      // Notify parent component
      onPermissionsUpdated();
      
    } catch (error: any) {
      console.error('Error updating user permissions:', error);
      toast.error(error.message || 'Failed to update user permissions');
    } finally {
      setUpdatingUserId(null);
    }
  };

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${label} copied to clipboard`);
    } catch (error) {
      toast.error('Failed to copy to clipboard');
    }
  };

  const handleClose = () => {
    setEventUsers([]);
    setUpdatingUserId(null);
    onClose();
  };

  const getAccessLevelColor = (accessLevel: string) => {
    switch (accessLevel) {
      case 'admin':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'read_write':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'read_only':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getAccessLevelDescription = (accessLevel: string) => {
    switch (accessLevel) {
      case 'admin':
        return 'Full access to manage event, participants, and scores';
      case 'read_write':
        return 'Can view and edit participants and scores';
      case 'read_only':
        return 'Can only view event data';
      default:
        return 'Unknown access level';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Event User Permissions
          </DialogTitle>
          <DialogDescription>
            Manage user permissions for the event "{eventName}". Only super admins can modify permissions.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">Loading event users...</p>
            </div>
          </div>
        ) : eventUsers.length === 0 ? (
          <div className="text-center py-8">
            <Users className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Event Users Found</h3>
            <p className="text-gray-600 mb-4">
              There are no users assigned to this event yet. Create event users first to manage their permissions.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="h-5 w-5 text-blue-600" />
                <h3 className="font-semibold text-blue-800">Permission Management</h3>
              </div>
              <p className="text-sm text-blue-700">
                You can change user access levels for this event. Changes take effect immediately.
              </p>
            </div>

            <div className="space-y-4">
              {eventUsers.map((eventUser) => (
                <Card key={eventUser.user.id} className="border border-gray-200">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <span>{eventUser.user.full_name}</span>
                        {eventUser.user.id === eventCreatedBy && (
                          <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                            Event Creator
                          </span>
                        )}
                      </CardTitle>
                      <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getAccessLevelColor(eventUser.access_level)}`}>
                        {eventUser.access_level.replace('_', ' ').toUpperCase()}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label className="text-sm font-medium text-gray-600">Email</Label>
                        <div className="flex items-center gap-2 mt-1">
                          <Input
                            value={eventUser.user.email}
                            readOnly
                            className="bg-gray-50"
                          />
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => copyToClipboard(eventUser.user.email, 'Email')}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <div>
                        <Label className="text-sm font-medium text-gray-600">Assigned Date</Label>
                        <Input
                          value={new Date(eventUser.assigned_at).toLocaleDateString()}
                          readOnly
                          className="bg-gray-50"
                        />
                      </div>
                    </div>

                    <div>
                      <Label className="text-sm font-medium text-gray-600">Current Access Level</Label>
                      <p className="text-sm text-gray-700 mt-1">
                        {getAccessLevelDescription(eventUser.access_level)}
                      </p>
                    </div>

                    {eventUser.user.id !== eventCreatedBy && (
                      <div>
                        <Label className="text-sm font-medium text-gray-600">Change Access Level</Label>
                        <div className="flex items-center gap-2 mt-1">
                          <Select
                            value={eventUser.access_level}
                            onValueChange={(value) => handleAccessLevelChange(eventUser.user.id, value)}
                            disabled={updatingUserId === eventUser.user.id}
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="read_only">
                                <div className="flex flex-col">
                                  <span>Read Only</span>
                                  <span className="text-xs text-gray-500">View only</span>
                                </div>
                              </SelectItem>
                              <SelectItem value="read_write">
                                <div className="flex flex-col">
                                  <span>Read Write</span>
                                  <span className="text-xs text-gray-500">View and edit</span>
                                </div>
                              </SelectItem>
                              <SelectItem value="admin">
                                <div className="flex flex-col">
                                  <span>Admin</span>
                                  <span className="text-xs text-gray-500">Full access</span>
                                </div>
                              </SelectItem>
                            </SelectContent>
                          </Select>
                          {updatingUserId === eventUser.user.id && (
                            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                          )}
                        </div>
                      </div>
                    )}

                    {eventUser.user.id === eventCreatedBy && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                        <div className="flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-green-600" />
                          <span className="text-sm font-medium text-green-800">
                            Event Creator - Cannot modify permissions
                          </span>
                        </div>
                        <p className="text-xs text-green-700 mt-1">
                          The event creator always has full admin access to their event.
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        <DialogFooter>
          <Button onClick={handleClose} className="w-full">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default EventUserPermissionsModal;
