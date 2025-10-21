import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import UserList from '@/components/users/UserList';
import UserForm from '@/components/users/UserForm';
import { User } from '@/services/userService';

const UsersPage: React.FC = () => {
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | undefined>(undefined);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleCreateUser = () => {
    setEditingUser(undefined);
    setShowForm(true);
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setShowForm(true);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingUser(undefined);
    setRefreshKey(prev => prev + 1);
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setEditingUser(undefined);
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-lg border-b border-gray-200 px-8 py-3 flex-shrink-0">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-lg font-bold text-gray-900">User Management</h1>
            <p className="text-xs text-gray-600">Manage user accounts and permissions</p>
          </div>
          <Button onClick={handleCreateUser} className="bg-blue-500 hover:bg-blue-600 text-white">
            Create User
          </Button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden p-8">
        {showForm ? (
          <UserForm
            user={editingUser}
            onSuccess={handleFormSuccess}
            onCancel={handleFormCancel}
          />
        ) : (
          <UserList
            key={refreshKey}
            onEditUser={handleEditUser}
            onRefresh={handleRefresh}
          />
        )}
      </div>
    </div>
  );
};

export default UsersPage;