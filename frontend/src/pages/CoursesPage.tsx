import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import CourseList from '@/components/courses/CourseList';
import CourseForm from '@/components/courses/CourseForm';
import HoleEditor from '@/components/courses/HoleEditor';
import TeeboxEditor from '@/components/courses/TeeboxEditor';
import CourseDetails from '@/components/courses/CourseDetails';
import { Course } from '@/services/courseService';
import { usePermissions } from '@/hooks/usePermissions';

const CoursesPage: React.FC = () => {
  const location = useLocation();
  const { canManageCourses } = usePermissions();
  const [showForm, setShowForm] = useState(false);
  const [showHoleEditor, setShowHoleEditor] = useState(false);
  const [showTeeboxEditor, setShowTeeboxEditor] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [editingCourse, setEditingCourse] = useState<Course | undefined>(undefined);
  const [viewingCourse, setViewingCourse] = useState<Course | undefined>(undefined);
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

  const handleEditTeeboxes = (course: Course) => {
    setEditingCourse(course);
    setShowTeeboxEditor(true);
  };

  const handleViewDetails = (course: Course) => {
    setViewingCourse(course);
    setShowDetails(true);
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

  const handleTeeboxEditorSuccess = () => {
    setShowTeeboxEditor(false);
    setEditingCourse(undefined);
    setRefreshKey(prev => prev + 1);
  };

  const handleTeeboxEditorCancel = () => {
    setShowTeeboxEditor(false);
    setEditingCourse(undefined);
  };

  const handleDetailsCancel = () => {
    setShowDetails(false);
    setViewingCourse(undefined);
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
            {canManageCourses() && (
              <Button onClick={handleCreateCourse} className="bg-blue-500 hover:bg-blue-600 text-white">
                Create Course
              </Button>
            )}
          </div>
      </div>

      {/* Main content */}
      <div className={`flex-1 ${(showHoleEditor || showTeeboxEditor) ? 'overflow-hidden' : 'overflow-y-auto p-8'}`}>
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
        ) : showTeeboxEditor && editingCourse ? (
          <TeeboxEditor
            courseId={editingCourse.id}
            onSave={handleTeeboxEditorSuccess}
            onCancel={handleTeeboxEditorCancel}
          />
        ) : (
          <CourseList
            key={refreshKey}
            onEditCourse={handleEditCourse}
            onEditHoles={handleEditHoles}
            onEditTeeboxes={handleEditTeeboxes}
            onViewDetails={handleViewDetails}
            onRefresh={handleRefresh}
            canManageCourses={canManageCourses()}
          />
        )}
      </div>
      
      {/* Course Details Modal - Rendered outside main content */}
      {showDetails && viewingCourse && (
        <CourseDetails
          course={viewingCourse}
          onClose={handleDetailsCancel}
        />
      )}
    </div>
  );
};

export default CoursesPage;