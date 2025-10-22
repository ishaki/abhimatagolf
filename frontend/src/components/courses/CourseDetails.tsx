import React, { useEffect } from 'react';
import { Course } from '@/services/courseService';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface CourseDetailsProps {
  course: Course;
  onClose: () => void;
}

const CourseDetails: React.FC<CourseDetailsProps> = ({ course, onClose }) => {
  // Handle escape key press
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4 animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-hidden bg-white shadow-2xl animate-in zoom-in-95 duration-200">
        <CardHeader className="bg-gradient-to-r from-orange-400 to-orange-500 text-white">
          <div className="flex justify-between items-center">
            <CardTitle className="text-2xl font-bold">{course.name}</CardTitle>
            <Button
              onClick={onClose}
              variant="secondary"
              className="bg-white/20 hover:bg-white/30 text-white border-white/30 hover:text-white"
            >
              ✕ Close
            </Button>
          </div>
        </CardHeader>
        
        <CardContent className="p-6 overflow-y-auto max-h-[calc(90vh-120px)] bg-white">
          <div className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Course Information</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center py-2 border-b border-gray-200">
                      <span className="text-gray-700 font-medium">Name:</span>
                      <span className="font-semibold text-gray-900">{course.name}</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-gray-200">
                      <span className="text-gray-700 font-medium">Location:</span>
                      <span className="font-semibold text-gray-900">{course.location || 'Not specified'}</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-gray-200">
                      <span className="text-gray-700 font-medium">Total Holes:</span>
                      <span className="font-semibold text-gray-900">{course.total_holes}</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-gray-200">
                      <span className="text-gray-700 font-medium">Configured Holes:</span>
                      <span className="font-semibold text-gray-900">{course.holes?.length || 0}</span>
                    </div>
                    <div className="flex justify-between items-center py-2">
                      <span className="text-gray-700 font-medium">Teeboxes:</span>
                      <span className="font-semibold text-gray-900">{course.teeboxes?.length || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Course Statistics</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center py-2 border-b border-gray-200">
                      <span className="text-gray-700 font-medium">Total Par:</span>
                      <span className="font-semibold text-gray-900">
                        {course.holes?.reduce((sum, hole) => sum + hole.par, 0) || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-gray-200">
                      <span className="text-gray-700 font-medium">Average Par:</span>
                      <span className="font-semibold text-gray-900">
                        {course.holes?.length 
                          ? (course.holes.reduce((sum, hole) => sum + hole.par, 0) / course.holes.length).toFixed(1)
                          : 'N/A'
                        }
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-gray-200">
                      <span className="text-gray-700 font-medium">Total Distance:</span>
                      <span className="font-semibold text-gray-900">
                        {course.holes?.reduce((sum, hole) => sum + (hole.distance_meters || 0), 0) || 'N/A'} meters
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-2">
                      <span className="text-gray-700 font-medium">Created:</span>
                      <span className="font-semibold text-gray-900">
                        {new Date(course.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Holes Details */}
            {course.holes && course.holes.length > 0 ? (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Hole Details</h3>
                <div className="overflow-x-auto bg-white rounded-lg shadow-sm">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="px-4 py-3 text-left font-semibold text-gray-900 border-b border-gray-200">Hole</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-900 border-b border-gray-200">Par</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-900 border-b border-gray-200">Stroke Index</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-900 border-b border-gray-200">Distance (m)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {course.holes.map((hole) => (
                        <tr key={hole.id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3 font-medium text-gray-900 border-b border-gray-100">{hole.number}</td>
                          <td className="px-4 py-3 text-gray-700 border-b border-gray-100">{hole.par}</td>
                          <td className="px-4 py-3 text-gray-700 border-b border-gray-100">{hole.stroke_index}</td>
                          <td className="px-4 py-3 text-gray-700 border-b border-gray-100">
                            {hole.distance_meters ? `${hole.distance_meters}m` : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div className="text-gray-500">
                  <svg className="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                  </svg>
                  <p className="text-xl font-semibold text-gray-900 mb-2">No holes configured</p>
                  <p className="text-gray-600">This course doesn't have any holes configured yet</p>
                </div>
              </div>
            )}

            {/* Teeboxes Details */}
            {course.teeboxes && course.teeboxes.length > 0 ? (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Teebox Details</h3>
                <div className="overflow-x-auto bg-white rounded-lg shadow-sm">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="px-4 py-3 text-left font-semibold text-gray-900 border-b border-gray-200">Teebox</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-900 border-b border-gray-200">Course Rating</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-900 border-b border-gray-200">Slope Rating</th>
                      </tr>
                    </thead>
                    <tbody>
                      {course.teeboxes.map((teebox) => (
                        <tr key={teebox.id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-4 py-3 font-medium text-gray-900 border-b border-gray-100">{teebox.name}</td>
                          <td className="px-4 py-3 text-gray-700 border-b border-gray-100">{teebox.course_rating}</td>
                          <td className="px-4 py-3 text-gray-700 border-b border-gray-100">{teebox.slope_rating}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                <div className="text-gray-500">
                  <svg className="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-xl font-semibold text-gray-900 mb-2">No teeboxes configured</p>
                  <p className="text-gray-600">This course doesn't have any teeboxes configured yet</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CourseDetails;
