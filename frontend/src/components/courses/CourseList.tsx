import React, { useState, useEffect } from 'react';
import { getCourses, deleteCourse, Course } from '@/services/courseService';
import { toast } from 'sonner';

interface CourseListProps {
  onEditCourse: (course: Course) => void;
  onEditHoles?: (course: Course) => void;
  onRefresh: () => void;
}

const CourseList: React.FC<CourseListProps> = ({ onEditCourse, onEditHoles, onRefresh }) => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const perPage = 10;

  const fetchCourses = async () => {
    try {
      setLoading(true);
      const response = await getCourses(page, perPage, search);
      setCourses(response.courses);
      setTotal(response.total);
    } catch (error: any) {
      toast.error('Failed to fetch courses', {
        description: error.response?.data?.detail || 'An unexpected error occurred.',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, [page, search]);

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this course?')) {
      return;
    }

    try {
      await deleteCourse(id);
      toast.success('Course deleted successfully');
      fetchCourses();
      onRefresh();
    } catch (error: any) {
      toast.error('Failed to delete course', {
        description: error.response?.data?.detail || 'An unexpected error occurred.',
      });
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const totalPages = Math.ceil(total / perPage);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="text-center text-gray-600 flex items-center justify-center gap-2">
          <svg className="animate-spin h-6 w-6" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Loading courses...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-900">Golf Courses</h2>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Search courses..."
              value={search}
              onChange={handleSearch}
              className="w-80 px-4 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>
      <div className="p-6">
        <div className="space-y-3">
          {courses.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <svg className="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
              <p className="text-lg font-medium">No courses found</p>
              <p className="text-sm mt-1">Create your first golf course to get started</p>
            </div>
          ) : (
            <>
              <div className="space-y-3">
                {courses.map((course) => (
                  <div
                    key={course.id}
                    className="flex items-center justify-between p-5 border-2 border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all"
                  >
                    <div className="flex-1">
                      <div className="font-bold text-lg text-gray-900">{course.name}</div>
                      <div className="text-sm text-gray-600 mt-1">{course.location || 'No location specified'}</div>
                      <div className="flex gap-2 mt-2">
                        <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                          {course.total_holes} holes
                        </span>
                        <span className="inline-block px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                          {course.holes?.length || 0} configured
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => onEditCourse(course)}
                        className="px-4 py-2 border-2 border-blue-500 text-blue-600 rounded-lg hover:bg-blue-50 font-medium transition-colors"
                      >
                        Edit
                      </button>
                      {onEditHoles && (
                        <button
                          onClick={() => onEditHoles(course)}
                          className="px-4 py-2 border-2 border-green-500 text-green-600 rounded-lg hover:bg-green-50 font-medium transition-colors"
                        >
                          Edit Holes
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(course.id)}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {totalPages > 1 && (
                <div className="flex justify-center gap-3 mt-6 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="px-4 py-2 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed font-medium"
                  >
                    Previous
                  </button>
                  <span className="flex items-center px-4 py-2 text-sm font-medium text-gray-700">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page === totalPages}
                    className="px-4 py-2 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed font-medium"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default CourseList;
