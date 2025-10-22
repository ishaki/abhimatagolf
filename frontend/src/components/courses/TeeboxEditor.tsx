import React, { useState, useEffect } from 'react';
import { Teebox, TeeboxCreate, TeeboxUpdate, getCourseTeeboxes, createTeebox, updateTeebox, deleteTeebox } from '@/services/courseService';
import { toast } from 'sonner';
import { useConfirm } from '@/hooks/useConfirm';

interface TeeboxEditorProps {
  courseId: number;
  onSave: () => void;
  onCancel: () => void;
}

const TeeboxEditor: React.FC<TeeboxEditorProps> = ({ courseId, onSave, onCancel }) => {
  const { confirm } = useConfirm();
  const [teeboxes, setTeeboxes] = useState<Teebox[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingTeebox, setEditingTeebox] = useState<Teebox | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    course_rating: 0,
    slope_rating: 0
  });

  useEffect(() => {
    fetchTeeboxes();
  }, [courseId]);

  const fetchTeeboxes = async () => {
    try {
      setLoading(true);
      const data = await getCourseTeeboxes(courseId);
      setTeeboxes(data);
    } catch (error: any) {
      toast.error('Failed to fetch teeboxes', {
        description: error.response?.data?.detail || 'An unexpected error occurred.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAddTeebox = () => {
    setEditingTeebox(null);
    setFormData({ name: '', course_rating: 0, slope_rating: 0 });
    setShowForm(true);
  };

  const handleEditTeebox = (teebox: Teebox) => {
    setEditingTeebox(teebox);
    setFormData({
      name: teebox.name,
      course_rating: teebox.course_rating,
      slope_rating: teebox.slope_rating
    });
    setShowForm(true);
  };

  const handleDeleteTeebox = async (teeboxId: number) => {
    const confirmed = await confirm({
      title: 'Delete Teebox?',
      description: 'Are you sure you want to delete this teebox? This action cannot be undone.',
      variant: 'danger',
      confirmText: 'Delete',
      cancelText: 'Cancel',
    });

    if (!confirmed) {
      return;
    }

    try {
      await deleteTeebox(courseId, teeboxId);
      toast.success('Teebox deleted successfully');
      fetchTeeboxes();
    } catch (error: any) {
      toast.error('Failed to delete teebox', {
        description: error.response?.data?.detail || 'An unexpected error occurred.',
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error('Teebox name is required');
      return;
    }

    if (formData.course_rating <= 0) {
      toast.error('Course rating must be greater than 0');
      return;
    }

    if (formData.slope_rating <= 0) {
      toast.error('Slope rating must be greater than 0');
      return;
    }

    try {
      if (editingTeebox) {
        await updateTeebox(courseId, editingTeebox.id, formData);
        toast.success('Teebox updated successfully');
      } else {
        await createTeebox(courseId, formData);
        toast.success('Teebox created successfully');
      }
      
      setShowForm(false);
      setEditingTeebox(null);
      fetchTeeboxes();
    } catch (error: any) {
      toast.error(editingTeebox ? 'Failed to update teebox' : 'Failed to create teebox', {
        description: error.response?.data?.detail || 'An unexpected error occurred.',
      });
    }
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingTeebox(null);
    setFormData({ name: '', course_rating: 0, slope_rating: 0 });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading teeboxes...</div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Manage Teeboxes</h2>
          <div className="flex gap-3">
            <button
              onClick={handleAddTeebox}
              className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 font-medium"
            >
              Add Teebox
            </button>
            <button
              onClick={onCancel}
              className="px-6 py-2 border border-gray-400 rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200 hover:border-gray-500 font-medium"
            >
              Done
            </button>
          </div>
        </div>

        {showForm && (
          <div className="mb-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
            <h3 className="text-lg font-semibold mb-4">
              {editingTeebox ? 'Edit Teebox' : 'Add New Teebox'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                    Teebox Name *
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Blue, White, Red"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="course_rating" className="block text-sm font-medium text-gray-700 mb-1">
                    Course Rating *
                  </label>
                  <input
                    id="course_rating"
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.course_rating}
                    onChange={(e) => setFormData({ ...formData, course_rating: parseFloat(e.target.value) || 0 })}
                    placeholder="72.8"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="slope_rating" className="block text-sm font-medium text-gray-700 mb-1">
                    Slope Rating *
                  </label>
                  <input
                    id="slope_rating"
                    type="number"
                    min="0"
                    value={formData.slope_rating}
                    onChange={(e) => setFormData({ ...formData, slope_rating: parseInt(e.target.value) || 0 })}
                    placeholder="136"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 font-medium"
                >
                  {editingTeebox ? 'Update Teebox' : 'Create Teebox'}
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  className="px-6 py-2 border border-gray-400 rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200 hover:border-gray-500 font-medium"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="space-y-4">
          {teeboxes.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No teeboxes found. Click "Add Teebox" to create the first one.
            </div>
          ) : (
            teeboxes.map((teebox) => (
              <div key={teebox.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-4">
                    <h4 className="font-semibold text-lg">{teebox.name}</h4>
                    <div className="flex gap-6 text-sm text-gray-600">
                      <span>Course Rating: <strong>{teebox.course_rating}</strong></span>
                      <span>Slope Rating: <strong>{teebox.slope_rating}</strong></span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEditTeebox(teebox)}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDeleteTeebox(teebox.id)}
                    className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default TeeboxEditor;
