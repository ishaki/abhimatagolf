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
import { getLiveScore, SortBy } from '@/services/liveScoreService';
import { ScorecardResponse } from '@/services/scorecardService';
import { toast } from 'sonner';
import { io, Socket } from 'socket.io-client';

// ========== AUTO-SCROLL CONFIGURATION ==========
// Easy configuration for auto-scroll behavior
const AUTO_SCROLL_CONFIG = {
  SCROLL_INTERVAL_MS: 5000,  // How fast to scroll (in milliseconds) - 5000 = 5 seconds
  ROW_HEIGHT_PX: 45,          // Estimated height of each row in pixels
};
// ================================================

const LiveScorePage: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const [scorecards, setScorecards] = useState<ScorecardResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<SortBy>('gross');
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [isAutoScrolling, setIsAutoScrolling] = useState(true);
  const [currentScrollIndex, setCurrentScrollIndex] = useState(0);

  const socketRef = useRef<Socket | null>(null);
  const tableBodyRef = useRef<HTMLDivElement | null>(null);
  const autoScrollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load live score data
  const loadLiveScore = useCallback(async () => {
    if (!eventId) return;

    try {
      setLoading(true);
      const data = await getLiveScore(parseInt(eventId), sortBy);
      setScorecards(data);
      setLastUpdated(new Date());
    } catch (error: any) {
      console.error('Error loading live score:', error);
      toast.error('Failed to load live scores');
    } finally {
      setLoading(false);
    }
  }, [eventId, sortBy]);

  // Initial load
  useEffect(() => {
    loadLiveScore();
  }, [loadLiveScore]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!eventId) return;

    const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('WebSocket connected for live score');
      // Join event room
      socket.emit('join_event', { event_id: parseInt(eventId) });
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    // Listen for live score updates
    socket.on('live_score_update', (data: any) => {
      console.log('Live score update received:', data);
      // Refresh data after a short delay to allow backend to update
      setTimeout(() => {
        loadLiveScore();
      }, 500);
    });

    socket.on('score_updated', (data: any) => {
      console.log('Score updated:', data);
      // Also refresh on legacy event
      setTimeout(() => {
        loadLiveScore();
      }, 500);
    });

    return () => {
      socket.emit('leave_event', { event_id: parseInt(eventId) });
      socket.disconnect();
      socketRef.current = null;
    };
  }, [eventId, loadLiveScore]);

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

    // Calculate how many rows fit in viewport based on configuration
    const rowsPerPage = Math.floor(window.innerHeight / AUTO_SCROLL_CONFIG.ROW_HEIGHT_PX);
    const totalRows = scorecards.length;

    // If all rows fit in viewport, no need to scroll
    if (totalRows <= rowsPerPage) {
      if (autoScrollIntervalRef.current) {
        clearInterval(autoScrollIntervalRef.current);
        autoScrollIntervalRef.current = null;
      }
      return;
    }

    // Start auto-scroll - scroll by page
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

  // Calculate rankings with tie handling - MUST be before early return
  const getScoreForRanking = useCallback((scorecard: ScorecardResponse) => {
    return sortBy === 'gross' ? (scorecard.gross_score || 999) : (scorecard.net_score || 999);
  }, [sortBy]);

  const scorecardsWithRanks = useMemo(() => {
    if (scorecards.length === 0) return [];

    // Sort by score
    const sorted = [...scorecards].sort((a, b) => getScoreForRanking(a) - getScoreForRanking(b));

    // Assign ranks with tie handling
    let currentRank = 1;
    let previousScore: number | null = null;
    let sameRankCount = 0;

    return sorted.map((scorecard) => {
      const score = getScoreForRanking(scorecard);

      if (previousScore !== null && score === previousScore) {
        // Same score as previous = same rank
        sameRankCount++;
      } else {
        // Different score = new rank (skip ranks if there were ties)
        currentRank += sameRankCount;
        sameRankCount = 1;
      }

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
    if (diff <= -2) return 'bg-blue-300'; // Eagle or better
    if (diff === -1) return 'bg-blue-200'; // Birdie
    if (diff === 0) return 'bg-white border border-gray-300'; // Par
    if (diff === 1) return 'bg-yellow-300'; // Bogey
    if (diff >= 2) return 'bg-red-300'; // Double bogey or worse
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
      <div className="flex-shrink-0 bg-gray-50 px-2 py-4 border-b">
        <div className="flex justify-between items-center mb-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-gray-900">
                {scorecards[0]?.event_name || 'Live Score'}
              </h1>
              {isAutoScrolling && scorecards.length > Math.floor(window.innerHeight / AUTO_SCROLL_CONFIG.ROW_HEIGHT_PX) && (
                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full animate-pulse">
                  Auto-scrolling (by page)
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Updated {timeAgo} • {scorecards.length} participants
            </p>
          </div>

          {/* Controls */}
          <div className="flex gap-2">
            <Button
              onClick={toggleSort}
              variant="outline"
              size="sm"
            >
              Sort: {sortBy === 'gross' ? 'Gross' : 'Net'}
            </Button>
            <Button
              onClick={() => setIsAutoScrolling(!isAutoScrolling)}
              variant="outline"
              size="sm"
            >
              {isAutoScrolling ? 'Pause Scroll' : 'Resume Scroll'}
            </Button>
            <Button onClick={toggleFullScreen} variant="outline" size="sm">
              {isFullScreen ? (
                <Minimize className="h-4 w-4" />
              ) : (
                <Maximize className="h-4 w-4" />
              )}
            </Button>
            <Button onClick={loadLiveScore} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Color Legend */}
        <div className="p-4 bg-white rounded-lg border shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Score Legend:</h3>
          <div className="flex flex-wrap gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-8 h-6 bg-blue-300 border border-gray-300 rounded"></div>
              <span className="font-medium">Eagle or Better (-2 or more)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-6 bg-blue-200 border border-gray-300 rounded"></div>
              <span className="font-medium">Birdie (-1)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-6 bg-white border border-gray-300 rounded"></div>
              <span className="font-medium">Par (0)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-6 bg-yellow-300 border border-gray-300 rounded"></div>
              <span className="font-medium">Bogey (+1)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-6 bg-red-300 border border-gray-300 rounded"></div>
              <span className="font-medium">Double Bogey or Worse (+2 or more)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-hidden px-2 pb-2">
        {scorecards.length > 0 ? (
          <div className="h-full border rounded-lg shadow-sm bg-white overflow-auto" ref={tableBodyRef}>
            <table className="w-full text-sm border-collapse">
              <thead className="sticky top-0 z-10 bg-orange-400 text-white">
                {/* Header Row 1: Hole Numbers */}
                <tr>
                  <th className="border border-gray-200 px-3 py-2 text-center font-semibold min-w-[50px]">
                    No
                  </th>
                  <th className="border border-gray-200 px-4 py-2 text-left font-semibold">
                    Player
                  </th>
                  {allHoles.slice(0, 9).map((hole) => (
                    <th key={hole.hole_number} className="border border-gray-200 px-2 py-2 text-center font-semibold min-w-[60px]">
                      {hole.hole_number}
                    </th>
                  ))}
                  <th className="border border-gray-200 px-3 py-2 text-center font-semibold bg-orange-500 min-w-[60px]">
                    Out
                  </th>
                  {allHoles.slice(9, 18).map((hole) => (
                    <th key={hole.hole_number} className="border border-gray-200 px-2 py-2 text-center font-semibold min-w-[60px]">
                      {hole.hole_number}
                    </th>
                  ))}
                  <th className="border border-gray-200 px-3 py-2 text-center font-semibold bg-orange-500 min-w-[60px]">
                    In
                  </th>
                  <th className="border border-gray-200 px-3 py-2 text-center font-semibold min-w-[70px]">
                    Total
                  </th>
                </tr>
                {/* Header Row 2: Par & Index */}
                <tr className="text-xs">
                  <td className="border border-gray-200 px-3 py-2"></td>
                  <td className="border border-gray-200 px-4 py-2"></td>
                  {/* Front 9 Par/Index */}
                  {allHoles.slice(0, 9).map((hole) => (
                    <td key={`par-${hole.hole_number}`} className="border border-gray-200 px-2 py-1 text-center">
                      <div className="font-medium">Par {hole.hole_par}</div>
                    </td>
                  ))}
                  {/* Out column - no par info */}
                  <td className="border border-gray-200 px-3 py-1 bg-orange-500"></td>
                  {/* Back 9 Par/Index */}
                  {allHoles.slice(9, 18).map((hole) => (
                    <td key={`par-${hole.hole_number}`} className="border border-gray-200 px-2 py-1 text-center">
                      <div className="font-medium">Par {hole.hole_par}</div>
                    </td>
                  ))}
                  {/* In column - no par info */}
                  <td className="border border-gray-200 px-3 py-1 bg-orange-500"></td>
                  {/* Total column - no par info */}
                  <td className="border border-gray-200 px-3 py-1"></td>
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
                        <div>{scorecard.participant_name} ({scorecard.handicap})</div>
                      </td>

                      {/* Front 9 Scores */}
                      {frontNineScores.map(({ hole, score }) => (
                        <td
                          key={`score-${scorecard.participant_id}-${hole.hole_number}`}
                          className={`border border-gray-200 px-2 py-2 text-center font-semibold ${getScoreColorClass(score, hole.hole_par)}`}
                        >
                          {score > 0 ? score : '-'}
                        </td>
                      ))}

                      {/* Out Total */}
                      <td className="border border-gray-200 px-3 py-2 text-center font-bold bg-orange-50">
                        {scorecard.out_total || '-'}
                      </td>

                      {/* Back 9 Scores */}
                      {backNineScores.map(({ hole, score }) => (
                        <td
                          key={`score-${scorecard.participant_id}-${hole.hole_number}`}
                          className={`border border-gray-200 px-2 py-2 text-center font-semibold ${getScoreColorClass(score, hole.hole_par)}`}
                        >
                          {score > 0 ? score : '-'}
                        </td>
                      ))}

                      {/* In Total */}
                      <td className="border border-gray-200 px-3 py-2 text-center font-bold bg-orange-50">
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
