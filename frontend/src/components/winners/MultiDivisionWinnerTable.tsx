/**
 * MultiDivisionWinnerTable Component
 *
 * Displays winner results grouped by division with separate sections for each division.
 * Only shows actual winners (top N per division based on configuration).
 *
 * Features:
 * - Separate card/section for each division
 * - Winners ordered by rank (1st, 2nd, 3rd) within each division
 * - Columns: Rank, Player Name, Declared HCP, Course HCP, Gross, Net, OCB/Tied
 * - Trophy/medal icons for top 3 positions
 * - Color-coded rows based on rank
 * - Responsive design
 */

import React, { useMemo } from 'react';
import { Trophy, Medal } from 'lucide-react';
import { WinnerResult, formatTieInformation } from '@/services/winnerService';

interface MultiDivisionWinnerTableProps {
  winners: WinnerResult[];
  eventName: string;
  scoringType: string;  // Event scoring type for conditional column display
}

const MultiDivisionWinnerTable: React.FC<MultiDivisionWinnerTableProps> = ({
  winners,
  eventName,
  scoringType
}) => {
  // Separate special awards from division winners
  const { specialAwards, divisionWinners } = useMemo(() => {
    const special = winners.filter(w => w.award_category !== null && w.award_category !== undefined);
    const divisions = winners.filter(w => w.award_category === null || w.award_category === undefined);
    return { specialAwards: special, divisionWinners: divisions };
  }, [winners]);

  // Group division winners by division and keep them sorted by division_rank
  const groupedWinners = useMemo(() => {
    const groups: { [key: string]: WinnerResult[] } = {};

    divisionWinners.forEach(winner => {
      const division = winner.division || 'No Division';
      if (!groups[division]) {
        groups[division] = [];
      }
      groups[division].push(winner);
    });

    // Sort each division by division_rank (should already be sorted from backend)
    Object.keys(groups).forEach(division => {
      groups[division].sort((a, b) => {
        const rankA = a.division_rank || 999;
        const rankB = b.division_rank || 999;
        return rankA - rankB;
      });
    });

    return groups;
  }, [divisionWinners]);

  // Get sorted division names for consistent display order
  const sortedDivisionNames = useMemo(() => {
    return Object.keys(groupedWinners).sort();
  }, [groupedWinners]);

  // Render rank badge with trophy/medal icons
  const renderRankBadge = (rank: number) => {
    if (rank === 1) {
      return (
        <div className="flex items-center justify-center gap-2">
          <Trophy className="h-6 w-6 text-yellow-500" fill="currentColor" />
          <span className="text-lg font-bold text-yellow-600">1st</span>
        </div>
      );
    } else if (rank === 2) {
      return (
        <div className="flex items-center justify-center gap-2">
          <Medal className="h-6 w-6 text-gray-400" fill="currentColor" />
          <span className="text-lg font-bold text-gray-500">2nd</span>
        </div>
      );
    } else if (rank === 3) {
      return (
        <div className="flex items-center justify-center gap-2">
          <Medal className="h-6 w-6 text-amber-600" fill="currentColor" />
          <span className="text-lg font-bold text-amber-700">3rd</span>
        </div>
      );
    } else {
      return (
        <span className="text-base font-semibold text-gray-700">{rank}th</span>
      );
    }
  };

  // Get row background color based on rank
  const getRowBgColor = (rank: number, index: number) => {
    if (rank === 1) return 'bg-yellow-50';
    if (rank === 2) return 'bg-gray-100';
    if (rank === 3) return 'bg-amber-50';
    return index % 2 === 0 ? 'bg-blue-50' : 'bg-white';
  };

  if (winners.length === 0) {
    return (
      <div className="w-full bg-white rounded-xl shadow-lg p-8 text-center">
        <p className="text-gray-500 text-lg">No winner results available</p>
        <p className="text-gray-400 text-sm mt-2">
          Winners need to be calculated before they can be displayed
        </p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      {/* Special Awards Section - Rendered FIRST */}
      {specialAwards.length > 0 && (
        <div className="bg-gradient-to-br from-yellow-50 via-amber-50 to-yellow-100 rounded-xl shadow-2xl overflow-hidden border-2 border-yellow-400">
          {/* Special Awards Header */}
          <div className="bg-gradient-to-r from-yellow-500 to-amber-600 px-6 py-4">
            <h3 className="text-2xl font-bold text-white flex items-center gap-3">
              <Trophy className="h-7 w-7" fill="currentColor" />
              🏆 Special Awards
            </h3>
            <p className="text-yellow-100 text-sm mt-1">
              {specialAwards.length} Special Award{specialAwards.length !== 1 ? 's' : ''}
            </p>
          </div>

          {/* Special Awards Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-yellow-200/80">
                <tr>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-yellow-900 uppercase tracking-wider">
                    Award
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-yellow-900 uppercase tracking-wider">
                    Player Name
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-yellow-900 uppercase tracking-wider">
                    Division
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-yellow-900 uppercase tracking-wider">
                    Declared HCP
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-yellow-900 uppercase tracking-wider">
                    Gross
                  </th>
                  {scoringType === 'net_stroke' && (
                    <th className="px-4 py-3 text-center text-xs font-semibold text-yellow-900 uppercase tracking-wider">
                      Course HCP
                    </th>
                  )}
                  {scoringType === 'system_36' && (
                    <th className="px-4 py-3 text-center text-xs font-semibold text-yellow-900 uppercase tracking-wider">
                      System 36 HCP
                    </th>
                  )}
                  {(scoringType === 'net_stroke' || scoringType === 'system_36') && (
                    <th className="px-4 py-3 text-center text-xs font-semibold text-yellow-900 uppercase tracking-wider">
                      Net
                    </th>
                  )}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-yellow-200">
                {specialAwards.map((winner, index) => (
                  <tr
                    key={winner.id}
                    className={`hover:bg-yellow-50 transition-colors ${
                      index % 2 === 0 ? 'bg-yellow-50/50' : 'bg-white'
                    }`}
                  >
                    {/* Award Category */}
                    <td className="px-4 py-4 whitespace-nowrap text-center">
                      <div className="flex items-center justify-center gap-2">
                        <Trophy className="h-6 w-6 text-yellow-600" fill="currentColor" />
                        <span className="text-base font-bold text-yellow-700">
                          {winner.award_category}
                        </span>
                      </div>
                    </td>
                    {/* Player Name */}
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-base font-bold text-gray-900">
                        {winner.participant_name}
                      </span>
                    </td>
                    {/* Division */}
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className="text-sm font-medium text-gray-700">
                        {winner.division || '-'}
                      </span>
                    </td>
                    {/* Declared HCP */}
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className="text-sm font-semibold text-gray-900">
                        {winner.declared_handicap}
                      </span>
                    </td>
                    {/* Gross Score */}
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className="text-base font-bold text-gray-900">
                        {winner.gross_score}
                      </span>
                    </td>
                    {/* Course HCP (if net_stroke) */}
                    {scoringType === 'net_stroke' && (
                      <td className="px-4 py-3 whitespace-nowrap text-center">
                        <span className="text-sm font-semibold text-gray-900">
                          {winner.course_handicap}
                        </span>
                      </td>
                    )}
                    {/* System 36 HCP (if system_36) */}
                    {scoringType === 'system_36' && (
                      <td className="px-4 py-3 whitespace-nowrap text-center">
                        <span className="text-sm font-semibold text-purple-700">
                          {winner.system36_handicap !== null && winner.system36_handicap !== undefined
                            ? winner.system36_handicap
                            : '-'}
                        </span>
                      </td>
                    )}
                    {/* Net Score (if applicable) */}
                    {(scoringType === 'net_stroke' || scoringType === 'system_36') && (
                      <td className="px-4 py-3 whitespace-nowrap text-center">
                        <span className="text-base font-bold text-blue-600">
                          {winner.net_score !== null && winner.net_score !== undefined
                            ? winner.net_score
                            : '-'}
                        </span>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Division Winners - One section per division */}
      {sortedDivisionNames.map((divisionName) => {
        const divisionWinners = groupedWinners[divisionName];

        return (
          <div key={divisionName} className="bg-white rounded-xl shadow-lg overflow-hidden">
            {/* Division Header */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-3">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <Trophy className="h-5 w-5" />
                {divisionName}
              </h3>
              <p className="text-blue-100 text-sm mt-1">
                {divisionWinners.length} Winner{divisionWinners.length !== 1 ? 's' : ''}
              </p>
            </div>

            {/* Division Winners Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-blue-50">
                  <tr>
                    {/* Always show: Rank, Player Name, Declared HCP */}
                    <th className="px-4 py-3 text-center text-xs font-semibold text-blue-800 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-blue-800 uppercase tracking-wider">
                      Player Name
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-blue-800 uppercase tracking-wider">
                      Declared HCP
                    </th>
                    {/* Conditional columns based on scoring type */}
                    <th className="px-4 py-3 text-center text-xs font-semibold text-blue-800 uppercase tracking-wider">
                      Gross
                    </th>
                    {scoringType === 'net_stroke' && (
                      <th className="px-4 py-3 text-center text-xs font-semibold text-blue-800 uppercase tracking-wider">
                        Course HCP
                      </th>
                    )}
                    {scoringType === 'system_36' && (
                      <th className="px-4 py-3 text-center text-xs font-semibold text-blue-800 uppercase tracking-wider">
                        System 36 HCP
                      </th>
                    )}
                    {(scoringType === 'net_stroke' || scoringType === 'system_36') && (
                      <th className="px-4 py-3 text-center text-xs font-semibold text-blue-800 uppercase tracking-wider">
                        Net
                      </th>
                    )}
                    {/* Always show: OCB/Tied */}
                    <th className="px-4 py-3 text-center text-xs font-semibold text-blue-800 uppercase tracking-wider">
                      OCB/Tied
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {divisionWinners.map((winner, index) => {
                    const rank = winner.division_rank || 1;
                    return (
                      <tr
                        key={winner.id}
                        className={`hover:bg-gray-50 transition-colors ${getRowBgColor(rank, index)}`}
                      >
                        {/* Always show: Rank, Player Name, Declared HCP */}
                        <td className="px-4 py-4 whitespace-nowrap text-center">
                          {renderRankBadge(rank)}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="text-base font-semibold text-gray-900">
                            {winner.participant_name}
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-center">
                          <span className="text-sm font-semibold text-gray-900">
                            {winner.declared_handicap}
                          </span>
                        </td>
                        {/* Conditional columns based on scoring type */}
                        <td className="px-4 py-3 whitespace-nowrap text-center">
                          <span className="text-sm font-bold text-gray-900">
                            {winner.gross_score}
                          </span>
                        </td>
                        {scoringType === 'net_stroke' && (
                          <td className="px-4 py-3 whitespace-nowrap text-center">
                            <span className="text-sm font-semibold text-gray-900">
                              {winner.course_handicap}
                            </span>
                          </td>
                        )}
                        {scoringType === 'system_36' && (
                          <td className="px-4 py-3 whitespace-nowrap text-center">
                            <span className="text-sm font-semibold text-purple-700">
                              {winner.system36_handicap !== null && winner.system36_handicap !== undefined
                                ? winner.system36_handicap
                                : '-'}
                            </span>
                          </td>
                        )}
                        {(scoringType === 'net_stroke' || scoringType === 'system_36') && (
                          <td className="px-4 py-3 whitespace-nowrap text-center">
                            <span className="text-base font-bold text-blue-600">
                              {winner.net_score !== null && winner.net_score !== undefined
                                ? winner.net_score
                                : '-'}
                            </span>
                          </td>
                        )}
                        {/* Always show: OCB/Tied */}
                        <td className="px-4 py-3 whitespace-nowrap text-center">
                          {winner.is_tied ? (
                            <span className="text-sm text-orange-600 font-medium">
                              {formatTieInformation(winner) || 'Yes'}
                            </span>
                          ) : (
                            <span className="text-sm text-gray-500">No</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default MultiDivisionWinnerTable;
