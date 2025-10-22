/**
 * Winner Page - Phase 3.3
 *
 * Public-facing winner display for tournaments.
 * Features: Overall and division winners with tie information, professional styling.
 *
 * Route: /winners/:eventId (public, no auth required)
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Trophy, Medal, Award, RefreshCw, Maximize, Minimize } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  getEventWinners,
  WinnerResult,
  WinnersListResponse,
  getRankDisplay,
  getRankBadgeColor,
  formatTieInformation,
} from '@/services/winnerService';
import { toast } from 'sonner';

const WinnerPage: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const [winnersData, setWinnersData] = useState<WinnersListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [selectedDivision, setSelectedDivision] = useState<string | 'all'>('all');

  // Load winners data
  const loadWinners = useCallback(async () => {
    if (!eventId) return;

    try {
      setLoading(true);
      const data = await getEventWinners(parseInt(eventId!));
      setWinnersData(data);
      setLastUpdated(new Date());
    } catch (error: any) {
      console.error('Error loading winners:', error);
      toast.error('Failed to load winners');
    } finally {
      setLoading(false);
    }
  }, [eventId]);

  // Initial load
  useEffect(() => {
    if (eventId) {
      loadWinners();
    }
  }, [loadWinners, eventId]);

  // Full screen toggle
  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullScreen(true);
    } else {
      document.exitFullscreen();
      setIsFullScreen(false);
    }
  };

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullScreenChange = () => {
      setIsFullScreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullScreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullScreenChange);
    };
  }, []);

  // Get unique divisions
  const divisions = React.useMemo(() => {
    if (!winnersData) return [];
    const divisionSet = new Set<string>();
    winnersData.winners.forEach((winner) => {
      if (winner.division) {
        divisionSet.add(winner.division);
      }
    });
    return Array.from(divisionSet).sort();
  }, [winnersData]);

  // Filter winners by division
  const filteredWinners = React.useMemo(() => {
    if (!winnersData) return [];
    if (selectedDivision === 'all') {
      // For "Best Gross & Nett", show only the best gross and best net scores
      const winners = winnersData.winners;
      
      // Find lowest gross score
      const lowestGross = Math.min(...winners.map(w => w.gross_score).filter(score => score > 0));
      const bestGrossWinner = winners.find(w => w.gross_score === lowestGross);
      
      // Find lowest net score (excluding null/undefined)
      const validNetScores = winners.map(w => w.net_score).filter(score => score !== null && score !== undefined && score > 0);
      const lowestNet = validNetScores.length > 0 ? Math.min(...validNetScores) : null;
      const bestNetWinner = lowestNet ? winners.find(w => w.net_score === lowestNet) : null;
      
      // Return unique winners (in case the same person has both best gross and net)
      const uniqueWinners = [];
      if (bestGrossWinner) uniqueWinners.push(bestGrossWinner);
      if (bestNetWinner && bestNetWinner.id !== bestGrossWinner?.id) uniqueWinners.push(bestNetWinner);
      
      return uniqueWinners;
    }
    // For divisions, return all division winners (podiumWinners will handle the top 3 filtering)
    return winnersData.winners.filter((w) => w.division === selectedDivision);
  }, [winnersData, selectedDivision]);

  // Get podium winners (top 3)
  const podiumWinners = React.useMemo(() => {
    if (selectedDivision === 'all') {
      // For "Best Gross & Nett", use the filtered winners directly
      return filteredWinners;
    }
    // For divisions, get top 3 winners sorted by rank
    const divisionWinners = winnersData?.winners.filter(
      (w) => w.division === selectedDivision
    ) || [];
    
    // Sort by division rank (handle cases where division_rank might be missing)
    const sortedWinners = divisionWinners.sort((a, b) => {
      const rankA = a.division_rank || 999;
      const rankB = b.division_rank || 999;
      
      // If both have the same rank or both are missing rank, sort by gross score as tiebreaker
      if (rankA === rankB) {
        return a.gross_score - b.gross_score;
      }
      
      return rankA - rankB;
    });
    
    // Take only the first 3 winners
    return sortedWinners.slice(0, 3);
  }, [winnersData, selectedDivision, filteredWinners]);

  // Get remaining winners (4th place and beyond)
  const remainingWinners = React.useMemo(() => {
    if (selectedDivision === 'all') {
      // For "Best Gross & Nett", no remaining winners
      return [] as WinnerResult[];
    }
    // For divisions, no remaining winners since we only show top 3
    return [] as WinnerResult[];
  }, [selectedDivision]);

  if (loading) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-blue-50 via-white to-green-50 flex items-center justify-center">
        <div className="text-center w-full">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-xl text-gray-600">Loading winners...</p>
        </div>
      </div>
    );
  }

  if (!winnersData || winnersData.winners.length === 0) {
    return (
      <div className="min-h-screen w-full bg-gradient-to-br from-blue-50 via-white to-green-50 flex items-center justify-center p-4">
        <div className="text-center w-full">
          <Trophy className="h-24 w-24 text-gray-300 mx-auto mb-6" />
          <h2 className="text-3xl font-bold text-gray-700 mb-4">No Winners Yet</h2>
          <p className="text-gray-600 mb-8">
            Winners have not been calculated for this event yet. Please ask an administrator to calculate the winners.
          </p>
          <Button
            onClick={loadWinners}
            variant="outline"
            size="lg"
            className="border-blue-500 text-blue-600 hover:bg-blue-50"
          >
            <RefreshCw className="h-5 w-5 mr-2" />
            Refresh
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="w-full px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <Trophy className="h-8 w-8 text-yellow-500" />
                <h1 className="text-3xl font-bold text-gray-900">Tournament Winners</h1>
              </div>
              <p className="text-xl text-gray-600">{winnersData.event_name}</p>
              <p className="text-sm text-gray-500 mt-1">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Button
                onClick={loadWinners}
                variant="outline"
                size="lg"
                className="border-gray-300"
              >
                <RefreshCw className="h-5 w-5 mr-2" />
                Refresh
              </Button>
              <Button
                onClick={toggleFullScreen}
                variant="outline"
                size="lg"
                className="border-gray-300"
              >
                {isFullScreen ? (
                  <Minimize className="h-5 w-5" />
                ) : (
                  <Maximize className="h-5 w-5" />
                )}
              </Button>
            </div>
          </div>

          {/* Division Filter */}
          {divisions.length > 0 && (
            <div className="mt-4 w-full">
              <div className="flex w-full">
                <button
                  onClick={() => setSelectedDivision('all')}
                  className={`flex-1 py-2 rounded-lg font-medium transition-colors text-center ${
                    selectedDivision === 'all'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Best Gross & Nett
                </button>
                {divisions.map((division) => (
                  <button
                    key={division}
                    onClick={() => setSelectedDivision(division)}
                    className={`flex-1 py-2 rounded-lg font-medium transition-colors text-center ${
                      selectedDivision === division
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {division}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="w-full px-4 py-8">
        {/* Podium Section (Top 3) */}
        {podiumWinners.length > 0 && (
          <div className="mb-12">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">
              {selectedDivision === 'all' ? 'Best Gross & Nett Scores' : `${selectedDivision} Winners`}
            </h2>

            <div className="w-full">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 w-full">
                {podiumWinners.map((winner) => {
                  const rank =
                    selectedDivision === 'all' ? winner.overall_rank : winner.division_rank || 0;
                  const IconComponent = rank === 1 ? Trophy : rank === 2 ? Medal : Award;
                  const iconColor = rank === 1 ? 'text-yellow-500' : rank === 2 ? 'text-gray-400' : 'text-orange-500';

                  return (
                    <div
                      key={winner.id}
                      className={`bg-white rounded-xl shadow-lg border-2 ${rank === 1 ? 'border-yellow-300' : rank === 2 ? 'border-gray-300' : 'border-orange-300'} p-6 text-center transform transition-all hover:scale-105 hover:shadow-xl`}
                    >
                      <div className="mb-4">
                        <IconComponent className={`h-12 w-12 ${iconColor} mx-auto`} />
                      </div>

                      <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full ${getRankBadgeColor(rank)} text-lg font-bold mb-4`}>
                        {getRankDisplay(rank)}
                      </div>

                      <h3 className="text-lg font-bold text-gray-900 mb-2">
                        {winner.participant_name}
                      </h3>

                      {winner.division && selectedDivision === 'all' && (
                        <p className="text-sm text-gray-600 mb-3">{winner.division}</p>
                      )}

                      {/* Show achievement type for Best Gross & Nett */}
                      {selectedDivision === 'all' && (
                        <div className="mb-3">
                          {winner.gross_score === Math.min(...winnersData.winners.map(w => w.gross_score).filter(score => score > 0)) && (
                            <span className="inline-block px-3 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded-full mb-1">
                              🏆 Best Gross Score
                            </span>
                          )}
                          {winner.net_score && winner.net_score === Math.min(...winnersData.winners.map(w => w.net_score).filter(score => score !== null && score !== undefined && score > 0)) && (
                            <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full mb-1">
                              🏆 Best Net Score
                            </span>
                          )}
                        </div>
                      )}

                      <div className="space-y-2 mb-4">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Gross Score:</span>
                          <span className="font-bold text-lg">{winner.gross_score}</span>
                        </div>
                        {winner.net_score !== null && winner.net_score !== undefined && (
                          <div className="flex justify-between items-center">
                            <span className="text-gray-600">Net Score:</span>
                            <span className="font-bold text-lg text-blue-600">
                              {winner.net_score}
                            </span>
                          </div>
                        )}
                        <div className="flex justify-between items-center">
                          <span className="text-gray-600">Handicap:</span>
                          <span className="font-semibold">{winner.handicap}</span>
                        </div>
                      </div>

                      {winner.is_tied && (
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <p className="text-sm text-orange-600 font-medium">
                            {formatTieInformation(winner)}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Remaining Winners (4th and beyond) */}
        {remainingWinners.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Other Winners</h2>

            <div className="w-full">
              <div className="bg-white rounded-xl shadow-lg overflow-hidden w-full">
                <div className="overflow-x-auto w-full">
                  <table className="w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider w-16">
                          Rank
                        </th>
                        <th className="px-3 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider min-w-48">
                          Player
                        </th>
                        {selectedDivision === 'all' && (
                          <th className="px-2 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider w-32">
                            Division
                          </th>
                        )}
                        <th className="px-2 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider w-20">
                          Gross
                        </th>
                        <th className="px-2 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider w-20">
                          Net
                        </th>
                        <th className="px-2 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider w-20">
                          Handicap
                        </th>
                        <th className="px-3 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider min-w-40">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {remainingWinners.map((winner) => {
                        const rank =
                          selectedDivision === 'all' ? winner.overall_rank : winner.division_rank || 0;

                        return (
                          <tr key={winner.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-2 py-3 whitespace-nowrap text-center">
                              <div className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${getRankBadgeColor(rank)} text-sm font-bold`}>
                                {rank}
                              </div>
                            </td>
                            <td className="px-3 py-3 whitespace-nowrap">
                              <div className="text-sm font-semibold text-gray-900">
                                {winner.participant_name}
                              </div>
                            </td>
                            {selectedDivision === 'all' && (
                              <td className="px-2 py-3 whitespace-nowrap text-center">
                                <span className="px-3 py-1 inline-flex text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                                  {winner.division || 'N/A'}
                                </span>
                              </td>
                            )}
                            <td className="px-2 py-3 whitespace-nowrap text-center">
                              <span className="text-sm font-bold text-gray-900">
                                {winner.gross_score}
                              </span>
                            </td>
                            <td className="px-2 py-3 whitespace-nowrap text-center">
                              <span className="text-sm font-bold text-blue-600">
                                {winner.net_score !== null && winner.net_score !== undefined
                                  ? winner.net_score
                                  : '-'}
                              </span>
                            </td>
                            <td className="px-2 py-3 whitespace-nowrap text-center">
                              <span className="text-sm text-gray-700">{winner.handicap}</span>
                            </td>
                            <td className="px-3 py-3 whitespace-nowrap">
                              {winner.is_tied ? (
                                <span className="text-sm text-orange-600 font-medium">
                                  {formatTieInformation(winner)}
                                </span>
                              ) : (
                                <span className="text-sm text-gray-500">-</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 py-4 mt-8">
        <div className="w-full px-4 text-center text-gray-600">
          <p className="text-sm">
            Tournament Results • {winnersData.total_winners} Winners •{' '}
            {lastUpdated.toLocaleDateString()}
          </p>
        </div>
      </div>
    </div>
  );
};

export default WinnerPage;