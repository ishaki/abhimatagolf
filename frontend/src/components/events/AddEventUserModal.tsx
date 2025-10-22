/**
 * Add Event User Modal Component
 * 
 * Modal for creating event-specific users with auto-generated credentials.
 * Shows credentials one-time only with copy functionality.
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
import { Copy, RefreshCw, UserPlus, AlertTriangle, Users, Eye, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';
import { usePermissions } from '@/hooks/usePermissions';
import { getEventUsers, createEventUser, removeEventUser, EventUser, EventUsersListResponse } from '@/services/userService';

interface AddEventUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  eventId: number;
  eventName: string;
  onUserCreated: () => void;
}

interface EventUserCreateData {
  full_name: string;
  email?: string;
  password?: string;
}

interface EventUserCreateResponse {
  user: {
    id: number;
    full_name: string;
    email: string;
    role: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  };
  email: string;
  password: string;
  message: string;
}

const AddEventUserModal: React.FC<AddEventUserModalProps> = ({
  isOpen,
  onClose,
  eventId,
  eventName,
  onUserCreated,
}) => {
  const { canCreateEventUsers } = usePermissions();
  const [formData, setFormData] = useState<EventUserCreateData>({
    full_name: '',
    email: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isGeneratingPassword, setIsGeneratingPassword] = useState(false);
  const [createdUser, setCreatedUser] = useState<EventUserCreateResponse | null>(null);
  const [showCredentials, setShowCredentials] = useState(false);
  const [existingUsers, setExistingUsers] = useState<EventUser[]>([]);
  const [hasExistingUsers, setHasExistingUsers] = useState(false);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [recreatingUserId, setRecreatingUserId] = useState<number | null>(null);
  const [showRecreateConfirm, setShowRecreateConfirm] = useState(false);
  const [userToRecreate, setUserToRecreate] = useState<EventUser | null>(null);

  // Check permissions
  if (!canCreateEventUsers()) {
    return null;
  }

  // Check for existing users when modal opens
  useEffect(() => {
    if (isOpen) {
      checkExistingUsers();
    }
  }, [isOpen, eventId]);

  const checkExistingUsers = async () => {
    setIsLoadingUsers(true);
    try {
      const response = await getEventUsers(eventId);
      setExistingUsers(response.users);
      setHasExistingUsers(response.users.length > 0);
    } catch (error) {
      console.error('Error fetching existing users:', error);
      // If there's an error, assume no users exist and show creation form
      setHasExistingUsers(false);
    } finally {
      setIsLoadingUsers(false);
    }
  };

  const handleInputChange = (field: keyof EventUserCreateData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const generatePassword = async () => {
    setIsGeneratingPassword(true);
    try {
      // Generate a secure password on the frontend
      const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
      let password = '';
      for (let i = 0; i < 12; i++) {
        password += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      
      setFormData(prev => ({
        ...prev,
        password,
      }));
      
      toast.success('New password generated');
    } catch (error) {
      toast.error('Failed to generate password');
    } finally {
      setIsGeneratingPassword(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.full_name.trim()) {
      toast.error('Full name is required');
      return;
    }

    setIsLoading(true);
    
    try {
      const result = await createEventUser(eventId, {
        full_name: formData.full_name.trim(),
        email: formData.email?.trim() || undefined,
        password: formData.password || undefined,
      });
      setCreatedUser(result);
      setShowCredentials(true);
      
      toast.success('Event user created successfully');
      
      // Reset form
      setFormData({
        full_name: '',
        email: '',
        password: '',
      });
      
      // Refresh the users list
      await checkExistingUsers();
      
      // Notify parent component
      onUserCreated();
      
    } catch (error: any) {
      console.error('Error creating event user:', error);
      toast.error(error.message || 'Failed to create event user');
    } finally {
      setIsLoading(false);
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

  const handleRecreateUser = (eventUser: EventUser) => {
    setUserToRecreate(eventUser);
    setShowRecreateConfirm(true);
  };

  const confirmRecreateUser = async () => {
    if (!userToRecreate) return;

    setRecreatingUserId(userToRecreate.user.id);
    setShowRecreateConfirm(false);
    
    try {
      // Remove the existing user from the event
      await removeEventUser(eventId, userToRecreate.user.id);
      
      // Create a new user with the same name
      const result = await createEventUser(eventId, {
        full_name: userToRecreate.user.full_name,
        email: userToRecreate.user.email,
        password: undefined, // Let the backend generate a new password
      });
      
      setCreatedUser(result);
      setShowCredentials(true);
      
      toast.success('User recreated successfully with new credentials');
      
      // Refresh the users list
      await checkExistingUsers();
      
      // Notify parent component
      onUserCreated();
      
    } catch (error: any) {
      console.error('Error recreating user:', error);
      toast.error(error.message || 'Failed to recreate user');
    } finally {
      setRecreatingUserId(null);
      setUserToRecreate(null);
    }
  };

  const cancelRecreateUser = () => {
    setShowRecreateConfirm(false);
    setUserToRecreate(null);
  };

  const handleClose = () => {
    setCreatedUser(null);
    setShowCredentials(false);
    setFormData({
      full_name: '',
      email: '',
      password: '',
    });
    setExistingUsers([]);
    setHasExistingUsers(false);
    setRecreatingUserId(null);
    setShowRecreateConfirm(false);
    setUserToRecreate(null);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {hasExistingUsers ? (
              <>
                <Users className="h-5 w-5" />
                Event Users
              </>
            ) : (
              <>
                <UserPlus className="h-5 w-5" />
                Add Event User
              </>
            )}
          </DialogTitle>
          <DialogDescription>
            {hasExistingUsers 
              ? `Manage users for the event "${eventName}". These users have access to this event.`
              : `Create a new user specifically for the event "${eventName}". This user will only have access to this event.`
            }
          </DialogDescription>
        </DialogHeader>

        {isLoadingUsers ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">Loading event users...</p>
            </div>
          </div>
        ) : showCredentials ? (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="h-5 w-5 text-green-600" />
                <h3 className="font-semibold text-green-800">User Created Successfully!</h3>
              </div>
              <p className="text-sm text-green-700 mb-4">
                Save these credentials - they won't be shown again. The user can now log in with these details.
              </p>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">User Credentials</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-sm font-medium text-gray-600">Full Name</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Input
                      value={createdUser?.user.full_name || ''}
                      readOnly
                      className="bg-gray-50"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(createdUser?.user.full_name || '', 'Name')}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium text-gray-600">Email</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Input
                      value={createdUser?.email || ''}
                      readOnly
                      className="bg-gray-50"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(createdUser?.email || '', 'Email')}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium text-gray-600">Password</Label>
                  <div className="flex items-center gap-2 mt-1">
                    <Input
                      value={createdUser?.password || ''}
                      readOnly
                      className="bg-gray-50 font-mono"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(createdUser?.password || '', 'Password')}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <DialogFooter>
              <Button onClick={handleClose} className="w-full">
                Close
              </Button>
            </DialogFooter>
          </div>
        ) : hasExistingUsers ? (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Eye className="h-5 w-5 text-blue-600" />
                <h3 className="font-semibold text-blue-800">Existing Event Users</h3>
              </div>
              <p className="text-sm text-blue-700">
                These users already have access to this event. You can share their credentials with others.
              </p>
            </div>

            <div className="space-y-4">
              {existingUsers.map((eventUser, index) => (
                <Card key={eventUser.user.id}>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center justify-between">
                      <span>{eventUser.user.full_name}</span>
                      <span className="text-sm font-normal text-gray-500">
                        {eventUser.access_level.replace('_', ' ').toUpperCase()}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
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
                    
                    <div className="pt-2 border-t border-gray-200">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => handleRecreateUser(eventUser)}
                        disabled={recreatingUserId === eventUser.user.id}
                        className="w-full border-orange-300 text-orange-600 hover:bg-orange-50"
                      >
                        {recreatingUserId === eventUser.user.id ? (
                          <>
                            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                            Recreating...
                          </>
                        ) : (
                          <>
                            <RotateCcw className="h-4 w-4 mr-2" />
                            Re-create User
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <DialogFooter>
              <Button onClick={handleClose} className="w-full">
                Close
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="full_name">Full Name *</Label>
                <Input
                  id="full_name"
                  value={formData.full_name}
                  onChange={(e) => handleInputChange('full_name', e.target.value)}
                  placeholder="Enter user's full name"
                  required
                />
              </div>

              <div>
                <Label htmlFor="email">Email (Optional)</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  placeholder="Leave empty for auto-generated email"
                />
                <p className="text-sm text-gray-500 mt-1">
                  If empty, an email will be auto-generated based on the event
                </p>
              </div>

              <div>
                <Label htmlFor="password">Password (Optional)</Label>
                <div className="flex gap-2">
                  <Input
                    id="password"
                    type="text"
                    value={formData.password}
                    onChange={(e) => handleInputChange('password', e.target.value)}
                    placeholder="Leave empty for auto-generated password"
                    readOnly
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={generatePassword}
                    disabled={isGeneratingPassword}
                    className="px-3"
                  >
                    <RefreshCw className={`h-4 w-4 ${isGeneratingPassword ? 'animate-spin' : ''}`} />
                  </Button>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  If empty, a secure password will be auto-generated
                </p>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? 'Creating...' : 'Create User'}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
      
      {/* Re-create Confirmation Dialog */}
      <Dialog open={showRecreateConfirm} onOpenChange={cancelRecreateUser}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <RotateCcw className="h-5 w-5 text-orange-600" />
              Re-create User
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to recreate "{userToRecreate?.user.full_name}"?
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
                <h3 className="font-semibold text-orange-800">Warning</h3>
              </div>
              <p className="text-sm text-orange-700">
                This will delete the current user and create a new one with fresh credentials. 
                The old credentials will no longer work.
              </p>
            </div>
            
            <div className="text-sm text-gray-600">
              <p><strong>Current user:</strong> {userToRecreate?.user.full_name}</p>
              <p><strong>Email:</strong> {userToRecreate?.user.email}</p>
              <p><strong>Access level:</strong> {userToRecreate?.access_level.replace('_', ' ').toUpperCase()}</p>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={cancelRecreateUser}>
              Cancel
            </Button>
            <Button 
              onClick={confirmRecreateUser}
              className="bg-orange-600 hover:bg-orange-700 text-white"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Re-create User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Dialog>
  );
};

export default AddEventUserModal;
