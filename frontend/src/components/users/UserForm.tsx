import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { FormControl, FormField, FormItem, FormLabel, FormMessage, FormDescription } from '@/components/ui/form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { User, UserCreate, UserUpdate, createUser, updateUser } from '@/services/userService';
import { toast } from 'sonner';
import { CheckCircle2, XCircle, Loader2, AlertCircle } from 'lucide-react';

const userSchema = z.object({
  full_name: z.string()
    .min(2, { message: 'Full name must be at least 2 characters.' })
    .max(100, { message: 'Full name must not exceed 100 characters.' }),
  email: z.string()
    .email({ message: 'Please enter a valid email address.' })
    .max(254, { message: 'Email must not exceed 254 characters.' }),
  password: z.string()
    .min(8, { message: 'Password must be at least 8 characters.' })
    .max(128, { message: 'Password must not exceed 128 characters.' })
    .optional()
    .or(z.literal('')),
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
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      full_name: user?.full_name || '',
      email: user?.email || '',
      password: '',
      role: user?.role as 'super_admin' | 'event_admin' | 'event_user' || 'event_user',
      is_active: user?.is_active ?? true,
    },
  });

  const onSubmit = async (values: UserFormData) => {
    try {
      setIsSubmitting(true);
      setError(null);

      console.log('=== User Form Submit ===');
      console.log('Form values:', values);
      console.log('Is editing:', isEditing);

      if (isEditing) {
        const updateData: UserUpdate = {
          full_name: values.full_name,
          email: values.email,
          role: values.role,
          is_active: values.is_active,
        };

        // Only include password if it's provided
        if (values.password && values.password.length > 0) {
          (updateData as any).password = values.password;
        }

        await updateUser(user!.id, updateData);
        toast.success('User Updated', {
          description: `${values.full_name} has been updated successfully.`,
          icon: <CheckCircle2 className="h-4 w-4" />,
        });
      } else {
        // Ensure password is provided for new users
        if (!values.password || values.password.length === 0) {
          setError('Password is required when creating a new user.');
          return;
        }

        const createData: UserCreate = {
          full_name: values.full_name,
          email: values.email,
          password: values.password,
          role: values.role,
          is_active: values.is_active,
        };

        const result = await createUser(createData);
        console.log('User created successfully:', result);
        toast.success('User Created', {
          description: `${values.full_name} has been created successfully.`,
          icon: <CheckCircle2 className="h-4 w-4" />,
        });
      }

      console.log('Calling onSuccess callback...');
      onSuccess();
      form.reset();
    } catch (error: any) {
      console.error('=== User form error ===');
      console.error('Error object:', error);
      console.error('Error response:', error.response);
      console.error('Error response data:', error.response?.data);

      let errorMessage = 'An unexpected error occurred.';

      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((e: any) => e.msg || e.message).join(', ');
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      console.error('Parsed error message:', errorMessage);
      setError(errorMessage);

      toast.error(isEditing ? 'Failed to Update User' : 'Failed to Create User', {
        description: errorMessage,
        icon: <XCircle className="h-4 w-4" />,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto shadow-lg">
      <CardHeader className="space-y-1 bg-gradient-to-r from-blue-50 to-indigo-50 border-b">
        <CardTitle className="text-2xl font-bold">
          {isEditing ? 'Edit User' : 'Create New User'}
        </CardTitle>
        <CardDescription>
          {isEditing
            ? 'Update user information and permissions'
            : 'Add a new user to the system with appropriate access level'}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-6">
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FormField
                control={form.control}
                name="full_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-sm font-semibold">Full Name *</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="e.g., John Doe"
                        className="h-10"
                        {...field}
                        disabled={isSubmitting}
                      />
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
                    <FormLabel className="text-sm font-semibold">Email Address *</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder="e.g., john.doe@example.com"
                        className="h-10"
                        {...field}
                        disabled={isSubmitting}
                      />
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
                    <FormLabel className="text-sm font-semibold">
                      Password {isEditing ? '(optional)' : '*'}
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="password"
                        placeholder={isEditing ? 'Leave blank to keep current' : 'Min 8 characters'}
                        className="h-10"
                        {...field}
                        disabled={isSubmitting}
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
                    <FormLabel className="text-sm font-semibold">Role *</FormLabel>
                    <FormControl>
                      <select
                        {...field}
                        disabled={isSubmitting}
                        className="w-full h-10 px-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
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
            </div>

            <FormField
              control={form.control}
              name="is_active"
              render={({ field }) => (
                <FormItem className="flex flex-row items-center space-x-3 space-y-0 rounded-md border p-3 bg-gray-50">
                  <FormControl>
                    <input
                      type="checkbox"
                      checked={field.value}
                      onChange={field.onChange}
                      disabled={isSubmitting}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:cursor-not-allowed"
                    />
                  </FormControl>
                  <div className="space-y-0 leading-none">
                    <FormLabel className="text-sm font-medium cursor-pointer">
                      Active Account
                    </FormLabel>
                  </div>
                </FormItem>
              )}
            />

            <div className="flex gap-3 pt-4 border-t">
              <Button
                type="submit"
                className="flex-1"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {isEditing ? 'Updating...' : 'Creating...'}
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    {isEditing ? 'Update User' : 'Create User'}
                  </>
                )}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
                className="flex-1"
                disabled={isSubmitting}
              >
                Cancel
              </Button>
            </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default UserForm;
