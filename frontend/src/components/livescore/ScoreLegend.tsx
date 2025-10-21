/**
 * Score Legend Component - Phase 3.2
 *
 * Displays color-coded legend for score types (Eagle, Birdie, Par, Bogey, Double+)
 */

import React from 'react';

const ScoreLegend: React.FC = () => {
  const legendItems = [
    { label: 'Eagle (-2 or better)', color: 'bg-blue-100 text-blue-800 border-blue-200' },
    { label: 'Birdie (-1)', color: 'bg-green-100 text-green-800 border-green-200' },
    { label: 'Par (E)', color: 'bg-white text-gray-800 border-gray-300' },
    { label: 'Bogey (+1)', color: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
    { label: 'Double+ (+2 or worse)', color: 'bg-red-100 text-red-800 border-red-200' },
  ];

  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Score Legend</h3>
      <div className="flex flex-wrap gap-3">
        {legendItems.map((item, index) => (
          <div key={index} className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded border-2 ${item.color} flex items-center justify-center text-xs font-bold`}
            >
              5
            </div>
            <span className="text-xs text-gray-600">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ScoreLegend;
