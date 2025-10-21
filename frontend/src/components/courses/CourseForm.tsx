import React, { useState } from 'react';
import { Course, CourseCreate, CourseUpdate, createCourse, updateCourse } from '@/services/courseService';
import { toast } from 'sonner';

interface CourseFormProps {
  course?: Course;
  onSuccess: () => void;
  onCancel: () => void;
}

const CourseForm: React.FC<CourseFormProps> = ({ course, onSuccess, onCancel }) => {
  const isEditing = !!course;
  const [name, setName] = useState(course?.name || '');
  const [location, setLocation] = useState(course?.location || '');
  const [totalHoles, setTotalHoles] = useState(course?.total_holes || 18);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      if (isEditing) {
        const updateData: CourseUpdate = {
          name,
          location,
          total_holes: totalHoles,
        };

        await updateCourse(course!.id, updateData);
        toast.success('Course updated successfully');
      } else {
        const createData: CourseCreate = {
          name,
          location,
          total_holes: totalHoles,
        };

        await createCourse(createData);
        toast.success('Course created successfully');
      }

      onSuccess();
    } catch (error: any) {
      toast.error(isEditing ? 'Failed to update course' : 'Failed to create course', {
        description: error.response?.data?.detail || 'An unexpected error occurred.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-6">{isEditing ? 'Edit Course' : 'Create Course'}</h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div style={{ marginBottom: '24px' }}>
            <label htmlFor="name" style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#000', marginBottom: '8px' }}>
              Course Name *
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Pebble Beach Golf Course"
              required
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '16px',
                border: '2px solid #3b82f6',
                borderRadius: '8px',
                backgroundColor: '#fff',
                color: '#000',
                minHeight: '48px',
                display: 'block'
              }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label htmlFor="location" style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#000', marginBottom: '8px' }}>
              Location
            </label>
            <input
              id="location"
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Pebble Beach, CA"
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '16px',
                border: '2px solid #3b82f6',
                borderRadius: '8px',
                backgroundColor: '#fff',
                color: '#000',
                minHeight: '48px',
                display: 'block'
              }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label htmlFor="totalHoles" style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#000', marginBottom: '8px' }}>
              Total Holes *
            </label>
            <input
              id="totalHoles"
              type="number"
              min="1"
              max="36"
              value={totalHoles}
              onChange={(e) => setTotalHoles(parseInt(e.target.value) || 18)}
              required
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '16px',
                border: '2px solid #3b82f6',
                borderRadius: '8px',
                backgroundColor: '#fff',
                color: '#000',
                minHeight: '48px',
                display: 'block'
              }}
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {isSubmitting ? 'Saving...' : (isEditing ? 'Update Course' : 'Create Course')}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="px-6 py-2 border border-gray-400 rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200 hover:border-gray-500 font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CourseForm;
