import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import CourseList from '@/components/courses/CourseList';
import CourseForm from '@/components/courses/CourseForm';
import HoleEditor from '@/components/courses/HoleEditor';
import { Course } from '@/services/courseService';

const CoursesPage: React.FC = () => {
  const location = useLocation();
  const [showForm, setShowForm] = useState(false);
  const [showHoleEditor, setShowHoleEditor] = useState(false);
  const [editingCourse, setEditingCourse] = useState<Course | undefined>(undefined);
  const [refreshKey, setRefreshKey] = useState(0);

  // Check if we should open the form automatically (from Dashboard quick action)
  useEffect(() => {
    if (location.state?.openForm) {
      setShowForm(true);
    }
  }, [location.state?.openForm]);

  const handleCreateCourse = () => {
    setEditingCourse(undefined);
    setShowForm(true);
  };

  const handleEditCourse = (course: Course) => {
    setEditingCourse(course);
    setShowForm(true);
  };

  const handleEditHoles = (course: Course) => {
    setEditingCourse(course);
    setShowHoleEditor(true);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingCourse(undefined);
    setRefreshKey(prev => prev + 1);
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setEditingCourse(undefined);
  };

  const handleHoleEditorSuccess = () => {
    setShowHoleEditor(false);
    setEditingCourse(undefined);
    setRefreshKey(prev => prev + 1);
  };

  const handleHoleEditorCancel = () => {
    setShowHoleEditor(false);
    setEditingCourse(undefined);
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
            <h1 className="text-lg font-bold text-gray-900">Course Management</h1>
            <p className="text-xs text-gray-600">Manage golf courses and hole configurations</p>
          </div>
          <Button onClick={handleCreateCourse} className="bg-blue-500 hover:bg-blue-600 text-white">
            Create Course
          </Button>
        </div>
      </div>

      {/* Main content */}
      <div className={`flex-1 ${showHoleEditor ? 'overflow-hidden' : 'overflow-y-auto p-8'}`}>
        {showForm ? (
          <div className="p-8">
            <CourseForm
              course={editingCourse}
              onSuccess={handleFormSuccess}
              onCancel={handleFormCancel}
            />
          </div>
        ) : showHoleEditor && editingCourse ? (
          <HoleEditor
            courseId={editingCourse.id}
            holes={editingCourse.holes || []}
            onSave={handleHoleEditorSuccess}
            onCancel={handleHoleEditorCancel}
          />
        ) : (
          <CourseList
            key={refreshKey}
            onEditCourse={handleEditCourse}
            onEditHoles={handleEditHoles}
            onRefresh={handleRefresh}
          />
        )}
      </div>
    </div>
  );
};

export default CoursesPage;