/**
 * Live Score Page - Phase 3.2
 *
 * Public-facing real-time score display for tournaments.
 * Features: Table/grid layout showing all players, WebSocket updates, full-screen mode.
 *
 * Route: /live-score/:eventId (public, no auth required)
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { Maximize, Minimize, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { getLiveScore, SortBy, LiveScoreWebSocket } from '@/services/liveScoreService';
import { ScorecardResponse } from '@/services/scorecardService';
import { toast } from 'sonner';
import { tokenStorage } from '@/utils/tokenStorage';
import { getCountryFlag } from '@/utils/countryUtils';

// ========== AUTO-SCROLL CONFIGURATION ==========
// Easy configuration for auto-scroll behavior
const AUTO_SCROLL_CONFIG = {
  SCROLL_INTERVAL_MS: 7000,  // How fast to scroll (in milliseconds) - 7000 = 7 seconds
  ROWS_PER_PAGE: 10,          // Show exactly 10 records per page
};
// ================================================

const LiveScorePage: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const [scorecards, setScorecards] = useState<ScorecardResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortBy>('gross');
  const [filterEmpty, setFilterEmpty] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [isAutoScrolling, setIsAutoScrolling] = useState(true);
  const [currentScrollIndex, setCurrentScrollIndex] = useState(0);

  const socketRef = useRef<LiveScoreWebSocket | null>(null);
  const tableBodyRef = useRef<HTMLDivElement | null>(null);
  const autoScrollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load live score data
  const loadLiveScore = useCallback(async () => {
    if (!eventId) return;

    try {
      setLoading(true);
      const data = await getLiveScore(parseInt(eventId), sortBy, filterEmpty);
      setScorecards(data);
      setLastUpdated(new Date());
    } catch (error: any) {
      console.error('Error loading live score:', error);
      toast.error('Failed to load live scores');
    } finally {
      setLoading(false);
    }
  }, [eventId, sortBy, filterEmpty]);

  // Initial load
  useEffect(() => {
    loadLiveScore();
  }, [loadLiveScore]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!eventId) return;

    const token = tokenStorage.getAccessToken();
    const websocket = new LiveScoreWebSocket(parseInt(eventId));
    
    // Set up event handlers
    websocket.setOnConnect(() => {
      console.log('WebSocket connected for live score');
    });

    websocket.setOnDisconnect(() => {
      console.log('WebSocket disconnected');
    });

    websocket.setOnError((error) => {
      console.warn('WebSocket connection failed, live score will work without real-time updates:', error);
      // Don't show error to user, just log it
    });

    websocket.setOnScoreUpdate((data: any) => {
      console.log('Score updated:', data);
      // Refresh data after a short delay to allow backend to update
      setTimeout(() => {
        loadLiveScore();
      }, 500);
    });

    websocket.setOnLiveScoreUpdate((data: any) => {
      console.log('Live score update:', data);
      // Also refresh on live score update
      setTimeout(() => {
        loadLiveScore();
      }, 500);
    });

    websocket.setOnLeaderboardUpdate((data: any) => {
      console.log('Leaderboard update:', data);
      // Refresh data when leaderboard updates
      setTimeout(() => {
        loadLiveScore();
      }, 500);
    });

    socketRef.current = websocket;

    // Connect to WebSocket
    websocket.connect(token || undefined).catch((error) => {
      console.warn('WebSocket connection failed, live score will work without real-time updates:', error);
    });

    return () => {
      websocket.disconnect();
      socketRef.current = null;
    };
  }, [eventId, loadLiveScore]);

  // Periodic refresh as fallback when WebSocket is not available
  useEffect(() => {
    const refreshInterval = setInterval(() => {
      loadLiveScore();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(refreshInterval);
  }, [loadLiveScore]);

  // Auto-scroll logic - scroll by page based on configuration
  useEffect(() => {
    if (!isAutoScrolling || scorecards.length === 0) {
      // Clear interval if auto-scroll disabled or no data
      if (autoScrollIntervalRef.current) {
        clearInterval(autoScrollIntervalRef.current);
        autoScrollIntervalRef.current = null;
      }
      return;
    }

    // Use fixed rows per page from configuration
    const rowsPerPage = AUTO_SCROLL_CONFIG.ROWS_PER_PAGE;
    const totalRows = scorecards.length;

    // If all rows fit in one page, no need to scroll
    if (totalRows <= rowsPerPage) {
      if (autoScrollIntervalRef.current) {
        clearInterval(autoScrollIntervalRef.current);
        autoScrollIntervalRef.current = null;
      }
      return;
    }

    // Start auto-scroll - scroll by page (exactly 10 records at a time)
    autoScrollIntervalRef.current = setInterval(() => {
      setCurrentScrollIndex((prev) => {
        // Move to next page (jump by rowsPerPage)
        const nextIndex = prev + rowsPerPage;
        // Loop back to start when reaching the end
        if (nextIndex >= totalRows) {
          return 0;
        }
        return nextIndex;
      });
    }, AUTO_SCROLL_CONFIG.SCROLL_INTERVAL_MS);

    return () => {
      if (autoScrollIntervalRef.current) {
        clearInterval(autoScrollIntervalRef.current);
        autoScrollIntervalRef.current = null;
      }
    };
  }, [isAutoScrolling, scorecards.length]);

  // Scroll to current index when it changes
  useEffect(() => {
    if (!tableBodyRef.current || !isAutoScrolling) return;

    // Special case: When looping back to start (index 0), scroll to absolute top
    if (currentScrollIndex === 0) {
      tableBodyRef.current.scrollTo({
        top: 0,
        behavior: 'smooth',
      });
      return;
    }

    const tbody = tableBodyRef.current.querySelector('tbody');
    if (!tbody) return;

    const rows = tbody.querySelectorAll('tr');
    if (rows[currentScrollIndex]) {
      rows[currentScrollIndex].scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }
  }, [currentScrollIndex, isAutoScrolling]);

  // Toggle sort
  const toggleSort = () => {
    setSortBy((prev) => (prev === 'gross' ? 'net' : 'gross'));
  };

  // Full-screen toggle
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
    return () => document.removeEventListener('fullscreenchange', handleFullScreenChange);
  }, []);

  // Time since last update
  const [timeAgo, setTimeAgo] = useState('just now');
  useEffect(() => {
    const updateTimeAgo = () => {
      const seconds = Math.floor((new Date().getTime() - lastUpdated.getTime()) / 1000);
      if (seconds < 10) {
        setTimeAgo('just now');
      } else if (seconds < 60) {
        setTimeAgo(`${seconds}s ago`);
      } else {
        const minutes = Math.floor(seconds / 60);
        setTimeAgo(`${minutes}m ago`);
      }
    };

    updateTimeAgo();
    const interval = setInterval(updateTimeAgo, 1000);
    return () => clearInterval(interval);
  }, [lastUpdated]);

  // Calculate rankings with tie handling - using backend-sorted data
  const getScoreForRanking = useCallback((scorecard: ScorecardResponse) => {
    return sortBy === 'gross' ? (scorecard.gross_score || 999) : (scorecard.net_score || 999);
  }, [sortBy]);

  const scorecardsWithRanks = useMemo(() => {
    if (scorecards.length === 0) return [];

    // Backend already sorts by: holes completed (desc) → gross score (asc) → zeros last
    // We just need to assign ranks based on the backend's sorting
    let currentRank = 1;
    let previousHolesCompleted: number | null = null;
    let previousScore: number | null = null;
    let sameRankCount = 0;

    return scorecards.map((scorecard) => {
      const holesCompleted = scorecard.holes_completed || 0;
      const score = getScoreForRanking(scorecard);

      // Check if this player should have the same rank as the previous one
      if (previousHolesCompleted !== null && 
          previousScore !== null && 
          holesCompleted === previousHolesCompleted && 
          score === previousScore) {
        // Same holes completed AND same score = same rank
        sameRankCount++;
      } else {
        // Different holes completed OR different score = new rank (skip ranks if there were ties)
        currentRank += sameRankCount;
        sameRankCount = 1;
      }

      previousHolesCompleted = holesCompleted;
      previousScore = score;

      return {
        ...scorecard,
        rank: currentRank,
      };
    });
  }, [scorecards, getScoreForRanking]);

  if (loading && scorecards.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading live scores...</p>
        </div>
      </div>
    );
  }

  // Color function matching scoring page
  const getScoreColorClass = (score: number, par: number) => {
    if (score === 0) return 'bg-white';
    const diff = score - par;
    if (diff <= -2) return 'bg-green-600'; // Eagle or better
    if (diff === -1) return 'bg-green-400'; // Birdie
    if (diff === 0) return 'bg-white border border-gray-300'; // Par
    if (diff === 1) return 'bg-red-200'; // Bogey
    if (diff >= 2) return 'bg-red-400'; // Double bogey or worse
    return 'bg-white';
  };

  // Get rank badge styling
  const getRankBadgeClass = (rank: number) => {
    if (rank === 1) return 'bg-yellow-400 text-white font-bold px-2 py-1 rounded'; // Gold
    if (rank === 2) return 'bg-gray-400 text-white font-bold px-2 py-1 rounded'; // Silver
    if (rank === 3) return 'bg-amber-600 text-white font-bold px-2 py-1 rounded'; // Bronze
    return 'text-gray-700 font-medium';
  };

  // Get hole information from first scorecard (all should have same course)
  const allHoles = scorecards[0] ? [...scorecards[0].front_nine, ...scorecards[0].back_nine] : [];

  return (
    <div className="h-screen w-full flex flex-col bg-gray-50">
      {/* Fixed Header */}
      <div className="flex-shrink-0 bg-gradient-to-r from-blue-100 via-blue-50 to-blue-100 text-blue-900 shadow-lg border-b border-blue-200/50 px-8 py-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-blue-900 tracking-tight">
                {scorecards[0]?.event_name || 'Live Score'}
              </h1>
              {isAutoScrolling && scorecards.length > AUTO_SCROLL_CONFIG.ROWS_PER_PAGE && (
                <span className="px-2 py-1 bg-blue-200 text-blue-800 text-xs font-medium rounded-full animate-pulse">
                  Auto-scrolling (10 records/page)
                </span>
              )}
            </div>
            <p className="text-sm text-blue-700 mt-1">
              Updated {timeAgo} • {scorecards.length} participants
            </p>
          </div>

          {/* Controls */}
          <div className="flex gap-2">
            <Button
              onClick={toggleSort}
              variant="outline"
              size="sm"
              className="bg-blue-200/50 backdrop-blur-sm border-blue-300 text-blue-800 hover:bg-blue-300/50 hover:border-blue-400 transition-all duration-300"
            >
              Sort: {sortBy === 'gross' ? 'Gross' : 'Net'}
            </Button>
            <Button
              onClick={() => setFilterEmpty(!filterEmpty)}
              variant={filterEmpty ? "default" : "outline"}
              size="sm"
              className={filterEmpty ? "bg-blue-500 hover:bg-blue-600 text-white" : "bg-blue-200/50 backdrop-blur-sm border-blue-300 text-blue-800 hover:bg-blue-300/50 hover:border-blue-400 transition-all duration-300"}
            >
              {filterEmpty ? 'Show All' : 'Hide Empty'}
            </Button>
            <Button
              onClick={() => setIsAutoScrolling(!isAutoScrolling)}
              variant="outline"
              size="sm"
              className="bg-blue-200/50 backdrop-blur-sm border-blue-300 text-blue-800 hover:bg-blue-300/50 hover:border-blue-400 transition-all duration-300"
            >
              {isAutoScrolling ? 'Pause Scroll' : 'Resume Scroll'}
            </Button>
            <Button 
              onClick={toggleFullScreen} 
              variant="outline" 
              size="sm"
              className="bg-blue-200/50 backdrop-blur-sm border-blue-300 text-blue-800 hover:bg-blue-300/50 hover:border-blue-400 transition-all duration-300"
            >
              {isFullScreen ? (
                <Minimize className="h-4 w-4" />
              ) : (
                <Maximize className="h-4 w-4" />
              )}
            </Button>
            <Button 
              onClick={loadLiveScore} 
              variant="outline" 
              size="sm"
              className="bg-white/10 backdrop-blur-sm border-white/30 text-white hover:bg-white/20 hover:border-white/40 transition-all duration-300"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Color Legend */}
        <div className="p-4 bg-blue-100/50 backdrop-blur-sm rounded-lg border border-blue-200/50 shadow-sm">
          <div className="flex flex-wrap gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-8 h-6 bg-green-600 border border-gray-300 rounded"></div>
              <span className="font-medium text-blue-800">Eagle or Better (-2 or more)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-6 bg-green-400 border border-gray-300 rounded"></div>
              <span className="font-medium text-blue-800">Birdie (-1)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-6 bg-white border border-gray-300 rounded"></div>
              <span className="font-medium text-blue-800">Par (0)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-6 bg-red-200 border border-gray-300 rounded"></div>
              <span className="font-medium text-blue-800">Bogey (+1)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-6 bg-red-400 border border-gray-300 rounded"></div>
              <span className="font-medium text-blue-800">Double Bogey or Worse (+2 or more)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-hidden px-2 pb-2">
        {scorecards.length > 0 ? (
          <div className="h-full border rounded-lg shadow-sm bg-white overflow-auto" ref={tableBodyRef}>
            <table className="w-full text-sm border-collapse table-fixed">
              <thead className="sticky top-0 z-10 bg-gray-200 text-gray-800 border-gray-400 shadow-sm">
                {/* Header Row 1: Hole Numbers */}
                <tr>
                  <th className="border border-gray-400 px-3 py-2 text-center font-semibold w-16 bg-gray-200">
                    No
                  </th>
                  <th className="border border-gray-400 px-4 py-2 text-left font-semibold w-48 bg-gray-200">
                    Player / Hole No.
                  </th>
                  {allHoles.slice(0, 9).map((hole) => (
                    <th key={hole.hole_number} className="border border-gray-400 px-1 py-2 text-center font-semibold w-12 bg-gray-200">
                      {hole.hole_number}
                    </th>
                  ))}
                  <th className="border border-gray-400 px-3 py-2 text-center font-semibold bg-gray-300 w-16">
                    Out
                  </th>
                  {allHoles.slice(9, 18).map((hole) => (
                    <th key={hole.hole_number} className="border border-gray-400 px-1 py-2 text-center font-semibold w-12 bg-gray-200">
                      {hole.hole_number}
                    </th>
                  ))}
                  <th className="border border-gray-400 px-3 py-2 text-center font-semibold bg-gray-300 w-16">
                    In
                  </th>
                  <th className="border border-gray-400 px-3 py-2 text-center font-semibold bg-gray-200 w-20">
                    Total
                  </th>
                </tr>
                {/* Header Row 2: Par & Index */}
                <tr className="text-xs bg-gray-200">
                  <td className="border border-gray-400 px-3 py-2 bg-gray-200"></td>
                  <td className="border border-gray-400 px-4 py-2 bg-gray-200"></td>
                  {/* Front 9 Par/Index */}
                  {allHoles.slice(0, 9).map((hole) => (
                    <td key={`par-${hole.hole_number}`} className="border border-gray-400 px-1 py-1 text-center bg-gray-200">
                      <div className="font-medium">Par {hole.hole_par}</div>
                    </td>
                  ))}
                  {/* Out column - no par info */}
                  <td className="border border-gray-400 px-3 py-1 bg-gray-300"></td>
                  {/* Back 9 Par/Index */}
                  {allHoles.slice(9, 18).map((hole) => (
                    <td key={`par-${hole.hole_number}`} className="border border-gray-400 px-1 py-1 text-center bg-gray-200">
                      <div className="font-medium">Par {hole.hole_par}</div>
                    </td>
                  ))}
                  {/* In column - no par info */}
                  <td className="border border-gray-400 px-3 py-1 bg-gray-300"></td>
                  {/* Total column - no par info */}
                  <td className="border border-gray-400 px-3 py-1 bg-gray-200"></td>
                </tr>
              </thead>
              <tbody>
                {scorecardsWithRanks.map((scorecard) => {
                  const frontNineScores = allHoles.slice(0, 9).map((hole) => {
                    const holeScore = scorecard.front_nine.find((h) => h.hole_number === hole.hole_number);
                    return { hole, score: holeScore?.strokes || 0 };
                  });
                  const backNineScores = allHoles.slice(9, 18).map((hole) => {
                    const holeScore = scorecard.back_nine.find((h) => h.hole_number === hole.hole_number);
                    return { hole, score: holeScore?.strokes || 0 };
                  });

                  return (
                    <tr key={scorecard.participant_id} className="hover:bg-gray-50">
                      {/* Rank Number */}
                      <td className="border border-gray-200 px-3 py-2 text-center">
                        <span className={getRankBadgeClass(scorecard.rank)}>
                          {scorecard.rank}
                        </span>
                      </td>
                      {/* Player Name */}
                      <td className="border border-gray-200 px-4 py-2 font-medium text-sm">
                        <div className="flex items-center gap-2">
                          {scorecard.country && getCountryFlag(scorecard.country) && (
                            <span className="text-xl leading-none">{getCountryFlag(scorecard.country)}</span>
                          )}
                          <span>{scorecard.participant_name} ({scorecard.handicap})</span>
                        </div>
                      </td>

                      {/* Front 9 Scores */}
                      {frontNineScores.map(({ hole, score }) => (
                        <td
                          key={`score-${scorecard.participant_id}-${hole.hole_number}`}
                          className={`border border-gray-200 px-1 py-2 text-center font-semibold ${getScoreColorClass(score, hole.hole_par)}`}
                        >
                          {score > 0 ? score : '-'}
                        </td>
                      ))}

                      {/* Out Total */}
                      <td className="border border-gray-200 px-3 py-2 text-center font-bold bg-gray-50">
                        {scorecard.out_total || '-'}
                      </td>

                      {/* Back 9 Scores */}
                      {backNineScores.map(({ hole, score }) => (
                        <td
                          key={`score-${scorecard.participant_id}-${hole.hole_number}`}
                          className={`border border-gray-200 px-1 py-2 text-center font-semibold ${getScoreColorClass(score, hole.hole_par)}`}
                        >
                          {score > 0 ? score : '-'}
                        </td>
                      ))}

                      {/* In Total */}
                      <td className="border border-gray-200 px-3 py-2 text-center font-bold bg-gray-50">
                        {scorecard.in_total || '-'}
                      </td>

                      {/* Total */}
                      <td className="border border-gray-200 px-3 py-2 text-center font-bold">
                        {scorecard.gross_score || '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center bg-white rounded-lg shadow-md">
            <div className="text-center">
              <p className="text-gray-600">No scores available yet.</p>
              <Button onClick={loadLiveScore} className="mt-4" variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveScorePage;
