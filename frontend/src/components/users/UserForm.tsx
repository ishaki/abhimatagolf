import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { User, UserCreate, UserUpdate, createUser, updateUser } from '@/services/userService';
import { toast } from 'sonner';

const userSchema = z.object({
  name: z.string().min(1, { message: 'Name is required.' }),
  email: z.string().email({ message: 'Invalid email address.' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters.' }).optional(),
  role: z.enum(['super_admin', 'event_admin', 'event_user'], {
    required_error: 'Please select a role.',
  }),
  is_active: z.boolean().default(true),
});

type UserFormData = z.infer<typeof userSchema>;

interface UserFormProps {
  user?: User;
  onSuccess: () => void;
  onCancel: () => void;
}

const UserForm: React.FC<UserFormProps> = ({ user, onSuccess, onCancel }) => {
  const isEditing = !!user;

  const form = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      name: user?.name || '',
      email: user?.email || '',
      password: '',
      role: user?.role as 'super_admin' | 'event_admin' | 'event_user' || 'event_user',
      is_active: user?.is_active ?? true,
    },
  });

  const onSubmit = async (values: UserFormData) => {
    try {
      if (isEditing) {
        const updateData: UserUpdate = {
          name: values.name,
          email: values.email,
          role: values.role,
          is_active: values.is_active,
        };
        
        // Only include password if it's provided
        if (values.password && values.password.length > 0) {
          (updateData as any).password = values.password;
        }
        
        await updateUser(user!.id, updateData);
        toast.success('User updated successfully');
      } else {
        const createData: UserCreate = {
          name: values.name,
          email: values.email,
          password: values.password!,
          role: values.role,
          is_active: values.is_active,
        };
        
        await createUser(createData);
        toast.success('User created successfully');
      }
      
      onSuccess();
    } catch (error: any) {
      toast.error(isEditing ? 'Failed to update user' : 'Failed to create user', {
        description: error.response?.data?.detail || 'An unexpected error occurred.',
      });
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>{isEditing ? 'Edit User' : 'Create User'}</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="John Doe" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input placeholder="john@example.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>
                    Password {isEditing && '(leave blank to keep current)'}
                  </FormLabel>
                  <FormControl>
                    <Input 
                      type="password" 
                      placeholder="********" 
                      {...field} 
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <FormControl>
                    <select 
                      {...field}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    >
                      <option value="event_user">Event User</option>
                      <option value="event_admin">Event Admin</option>
                      <option value="super_admin">Super Admin</option>
                    </select>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <FormField
              control={form.control}
              name="is_active"
              render={({ field }) => (
                <FormItem className="flex items-center space-x-2">
                  <FormControl>
                    <input
                      type="checkbox"
                      checked={field.value}
                      onChange={field.onChange}
                      className="rounded"
                    />
                  </FormControl>
                  <FormLabel>Active</FormLabel>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <div className="flex gap-2">
              <Button type="submit" className="flex-1" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? 'Saving...' : (isEditing ? 'Update' : 'Create')}
              </Button>
              <Button type="button" variant="outline" onClick={onCancel} className="border-gray-400 text-gray-700 bg-gray-100 hover:bg-gray-200 hover:border-gray-500">
                Cancel
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
};

export default UserForm;
