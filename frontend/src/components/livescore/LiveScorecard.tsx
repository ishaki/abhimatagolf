/**
 * Live Scorecard Component - Phase 3.2
 *
 * Read-only scorecard display for Live Score page.
 * Shows hole-by-hole scores with color coding (no editing).
 */

import React from 'react';
import { ScorecardResponse } from '@/services/scorecardService';
import { getScoreColor } from '@/services/scorecardService';

interface LiveScorecardProps {
  scorecard: ScorecardResponse;
  compact?: boolean; // Compact mode for fitting more cards per page
}

const LiveScorecard: React.FC<LiveScorecardProps> = ({ scorecard, compact = false }) => {
  const formatToPar = (score: number) => {
    if (score === 0) return 'E';
    if (score > 0) return `+${score}`;
    return score.toString();
  };

  // Compact mode for smaller displays
  if (compact) {
    return (
      <div className="bg-white border rounded-lg p-3 shadow-sm">
        {/* Header */}
        <div className="mb-2">
          <h3 className="text-lg font-bold text-gray-900 truncate">{scorecard.participant_name}</h3>
          <div className="text-xs text-gray-600">
            HCP: {scorecard.handicap} | Holes: {scorecard.holes_completed}/18
          </div>
        </div>

        {/* Scores Grid - Compact */}
        <div className="grid grid-cols-9 gap-1 mb-2">
          {scorecard.front_nine.map((hole) => (
            <div
              key={hole.hole_number}
              className={`text-center p-1 rounded border ${
                hole.strokes > 0 ? getScoreColor(hole.color_code) : 'bg-gray-50 text-gray-400'
              }`}
            >
              <div className="text-xs font-bold">{hole.strokes || '-'}</div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-9 gap-1">
          {scorecard.back_nine.map((hole) => (
            <div
              key={hole.hole_number}
              className={`text-center p-1 rounded border ${
                hole.strokes > 0 ? getScoreColor(hole.color_code) : 'bg-gray-50 text-gray-400'
              }`}
            >
              <div className="text-xs font-bold">{hole.strokes || '-'}</div>
            </div>
          ))}
        </div>

        {/* Totals */}
        <div className="mt-2 flex justify-between text-sm">
          <div>
            <span className="text-gray-600">Total: </span>
            <span className="font-bold text-blue-600">{scorecard.gross_score || '-'}</span>
          </div>
          <div>
            <span className="text-gray-600">To Par: </span>
            <span
              className={`font-bold ${
                scorecard.gross_score > 0
                  ? scorecard.score_to_par >= 0
                    ? 'text-red-600'
                    : 'text-green-600'
                  : 'text-gray-400'
              }`}
            >
              {scorecard.gross_score > 0 ? formatToPar(scorecard.score_to_par) : '-'}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Full mode for larger displays
  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm">
      {/* Header */}
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-gray-900">{scorecard.participant_name}</h2>
        <p className="text-sm text-gray-600">
          {scorecard.event_name} • Handicap: {scorecard.handicap} • Par: {scorecard.course_par}
        </p>
      </div>

      {/* Scorecard Table */}
      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Hole
                </th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                  Par
                </th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                  Score
                </th>
                <th className="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                  To Par
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {/* Front Nine */}
              {scorecard.front_nine.map((hole) => (
                <tr key={hole.hole_number} className="hover:bg-gray-50">
                  <td className="px-3 py-2 whitespace-nowrap">
                    <span className="font-semibold text-gray-900">{hole.hole_number}</span>
                  </td>
                  <td className="px-3 py-2 text-center text-sm text-gray-600">{hole.hole_par}</td>
                  <td className="px-3 py-2 text-center">
                    <span
                      className={`inline-block px-3 py-1 rounded border-2 font-bold ${
                        hole.strokes > 0 ? getScoreColor(hole.color_code) : 'bg-gray-50 text-gray-400'
                      }`}
                    >
                      {hole.strokes || '-'}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center">
                    {hole.strokes > 0 && (
                      <span
                        className={`text-sm font-medium ${
                          hole.score_to_par < 0
                            ? 'text-green-600'
                            : hole.score_to_par > 0
                            ? 'text-red-600'
                            : 'text-gray-600'
                        }`}
                      >
                        {formatToPar(hole.score_to_par)}
                      </span>
                    )}
                  </td>
                </tr>
              ))}

              {/* OUT Subtotal */}
              <tr className="bg-blue-50 font-semibold">
                <td className="px-3 py-2">OUT</td>
                <td className="px-3 py-2 text-center">
                  {scorecard.front_nine.reduce((sum, h) => sum + h.hole_par, 0)}
                </td>
                <td className="px-3 py-2 text-center text-blue-700">{scorecard.out_total || '-'}</td>
                <td className="px-3 py-2 text-center">
                  {scorecard.out_total > 0 && (
                    <span
                      className={
                        scorecard.out_to_par >= 0 ? 'text-red-600' : 'text-green-600'
                      }
                    >
                      {formatToPar(scorecard.out_to_par)}
                    </span>
                  )}
                </td>
              </tr>

              {/* Back Nine */}
              {scorecard.back_nine.map((hole) => (
                <tr key={hole.hole_number} className="hover:bg-gray-50">
                  <td className="px-3 py-2 whitespace-nowrap">
                    <span className="font-semibold text-gray-900">{hole.hole_number}</span>
                  </td>
                  <td className="px-3 py-2 text-center text-sm text-gray-600">{hole.hole_par}</td>
                  <td className="px-3 py-2 text-center">
                    <span
                      className={`inline-block px-3 py-1 rounded border-2 font-bold ${
                        hole.strokes > 0 ? getScoreColor(hole.color_code) : 'bg-gray-50 text-gray-400'
                      }`}
                    >
                      {hole.strokes || '-'}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-center">
                    {hole.strokes > 0 && (
                      <span
                        className={`text-sm font-medium ${
                          hole.score_to_par < 0
                            ? 'text-green-600'
                            : hole.score_to_par > 0
                            ? 'text-red-600'
                            : 'text-gray-600'
                        }`}
                      >
                        {formatToPar(hole.score_to_par)}
                      </span>
                    )}
                  </td>
                </tr>
              ))}

              {/* IN Subtotal */}
              <tr className="bg-indigo-50 font-semibold">
                <td className="px-3 py-2">IN</td>
                <td className="px-3 py-2 text-center">
                  {scorecard.back_nine.reduce((sum, h) => sum + h.hole_par, 0)}
                </td>
                <td className="px-3 py-2 text-center text-indigo-700">
                  {scorecard.in_total || '-'}
                </td>
                <td className="px-3 py-2 text-center">
                  {scorecard.in_total > 0 && (
                    <span
                      className={
                        scorecard.in_to_par >= 0 ? 'text-red-600' : 'text-green-600'
                      }
                    >
                      {formatToPar(scorecard.in_to_par)}
                    </span>
                  )}
                </td>
              </tr>

              {/* Total */}
              <tr className="bg-gray-100 font-bold text-lg">
                <td className="px-3 py-3">TOTAL</td>
                <td className="px-3 py-3 text-center">{scorecard.course_par}</td>
                <td className="px-3 py-3 text-center text-blue-700">
                  {scorecard.gross_score || '-'}
                </td>
                <td className="px-3 py-3 text-center">
                  {scorecard.gross_score > 0 && (
                    <span
                      className={
                        scorecard.score_to_par >= 0 ? 'text-red-600' : 'text-green-600'
                      }
                    >
                      {formatToPar(scorecard.score_to_par)}
                    </span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-3">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-600">Holes Completed</div>
          <div className="text-xl font-bold text-gray-900">{scorecard.holes_completed}/18</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-600">Gross Score</div>
          <div className="text-xl font-bold text-blue-600">{scorecard.gross_score || '-'}</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-600">To Par</div>
          <div
            className={`text-xl font-bold ${
              scorecard.gross_score > 0
                ? scorecard.score_to_par >= 0
                  ? 'text-red-600'
                  : 'text-green-600'
                : 'text-gray-400'
            }`}
          >
            {scorecard.gross_score > 0 ? formatToPar(scorecard.score_to_par) : '-'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveScorecard;
