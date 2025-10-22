import React, { useState, useEffect } from 'react';
import { HoleCreate, Hole, updateCourseHoles } from '@/services/courseService';
import { toast } from 'sonner';

interface HoleEditorProps {
  courseId: number;
  holes: Hole[];
  onSave: (holes: Hole[]) => void;
  onCancel: () => void;
}

const HoleEditor: React.FC<HoleEditorProps> = ({ courseId, holes, onSave, onCancel }) => {
  const [holeData, setHoleData] = useState<HoleCreate[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Initialize hole data from existing holes or create default 18 holes
    if (holes && holes.length > 0) {
      setHoleData(holes.map(hole => ({
        number: hole.number,
        par: hole.par,
        stroke_index: hole.stroke_index,
        distance_meters: hole.distance_meters,
      })));
    } else {
      // Create default 18 holes
      const defaultHoles: HoleCreate[] = [];
      for (let i = 1; i <= 18; i++) {
        defaultHoles.push({
          number: i,
          par: i <= 4 ? 4 : i <= 10 ? 3 : 5, // Mix of par 3, 4, 5
          stroke_index: i,
          distance_meters: undefined,
        });
      }
      setHoleData(defaultHoles);
    }
  }, [holes]);

  const handleHoleChange = (index: number, field: keyof HoleCreate, value: string | number) => {
    const newHoleData = [...holeData];
    newHoleData[index] = {
      ...newHoleData[index],
      [field]: value,
    };
    setHoleData(newHoleData);
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      const updatedHoles = await updateCourseHoles(courseId, holeData);
      toast.success('Holes updated successfully');
      onSave(updatedHoles);
    } catch (error: any) {
      toast.error('Failed to update holes', {
        description: error.response?.data?.detail || 'An unexpected error occurred.',
      });
    } finally {
      setLoading(false);
    }
  };

  const totalPar = holeData.reduce((sum, hole) => sum + hole.par, 0);

  return (
    <div className="w-full h-full flex flex-col">
      {/* Sticky Header with Actions */}
      <div className="bg-white border-b-2 border-gray-200 px-6 py-4 sticky top-0 z-10 shadow-md">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Configure Course Holes</h2>
              <p className="text-sm text-gray-600 mt-1">
                {holeData.length} holes • Total Par: {totalPar}
              </p>
            </div>
            
            {/* Action Buttons - Right aligned */}
            <div className="flex gap-3">
              <button
                onClick={handleSave}
                disabled={loading}
                className="bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold text-lg shadow-md"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Saving...
                  </span>
                ) : (
                  '💾 Save All Holes'
                )}
              </button>
              <button
                onClick={onCancel}
                className="px-8 py-3 border-2 border-gray-400 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 hover:border-gray-500 font-semibold text-lg"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto bg-gray-50 px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {holeData.map((hole, index) => (
              <div
                key={index}
                className="bg-white border-2 border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow"
              >
                {/* Hole Header */}
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-10 h-10 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-lg">
                    {hole.number}
                  </div>
                  <div>
                    <div className="font-bold text-gray-900">Hole {hole.number}</div>
                    <div className="text-xs text-gray-500">Par {hole.par}</div>
                  </div>
                </div>

                {/* Hole Fields */}
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">Par</label>
                    <select
                      value={hole.par}
                      onChange={(e) => handleHoleChange(index, 'par', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-medium"
                    >
                      <option value={3}>Par 3</option>
                      <option value={4}>Par 4</option>
                      <option value={5}>Par 5</option>
                      <option value={6}>Par 6</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">Stroke Index</label>
                    <input
                      type="number"
                      value={hole.stroke_index}
                      onChange={(e) => handleHoleChange(index, 'stroke_index', parseInt(e.target.value) || 1)}
                      min="1"
                      max="18"
                      className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-1">Distance (meters)</label>
                    <input
                      type="number"
                      value={hole.distance_meters || ''}
                      onChange={(e) => handleHoleChange(index, 'distance_meters', e.target.value ? parseFloat(e.target.value) : 0)}
                      placeholder="Optional"
                      className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Bottom padding for better scrolling */}
          <div className="h-8"></div>
        </div>
      </div>
    </div>
  );
};

export default HoleEditor;
