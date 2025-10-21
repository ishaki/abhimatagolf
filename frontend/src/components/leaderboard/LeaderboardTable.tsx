import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Trophy, Users, Clock, Filter, Maximize2, Minimize2, Play, Pause, RotateCcw, ChevronDown, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import {
  getEventLeaderboard,
  type LeaderboardResponse,
  type LeaderboardEntry,
  type LeaderboardFilters,
  formatScoreToPar,
  getRankColor,
  getScoreColor,
  formatLastUpdated
} from '@/services/leaderboardService';
import LeaderboardRowDetail from './LeaderboardRowDetail';

interface LeaderboardTableProps {
  eventId: number;
  onScoreUpdate?: () => void;
  isFullScreen?: boolean;
  onToggleFullScreen?: () => void;
  autoScrollInterval?: number; // Auto-scroll interval in seconds (default: 15)
  enableAutoScroll?: boolean; // Enable/disable auto-scroll (default: true)
}

const LeaderboardTable: React.FC<LeaderboardTableProps> = ({
  eventId,
  onScoreUpdate,
  isFullScreen = false,
  onToggleFullScreen,
  autoScrollInterval = 5,
  enableAutoScroll = true
}) => {
  const [leaderboard, setLeaderboard] = useState<LeaderboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [filters, setFilters] = useState<LeaderboardFilters>({});
  const [showFilters, setShowFilters] = useState(false);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());
  
  // Auto-scroll state
  const [isAutoScrolling, setIsAutoScrolling] = useState(enableAutoScroll);
  const [currentScrollIndex, setCurrentScrollIndex] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const tableBodyRef = useRef<HTMLDivElement>(null);
  const scrollIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    loadLeaderboard();
  }, [eventId, filters]);

  // Auto-scroll effect
  useEffect(() => {
    if (!leaderboard?.entries.length || !isAutoScrolling || isHovered) {
      return;
    }

    const startAutoScroll = () => {
      scrollIntervalRef.current = setInterval(() => {
        setCurrentScrollIndex(prev => {
          const nextIndex = (prev + 1) % leaderboard.entries.length;
          return nextIndex;
        });
      }, autoScrollInterval * 1000);
    };

    startAutoScroll();

    return () => {
      if (scrollIntervalRef.current) {
        clearInterval(scrollIntervalRef.current);
      }
    };
  }, [leaderboard?.entries.length, isAutoScrolling, isHovered, autoScrollInterval]);

  // Scroll to current index
  useEffect(() => {
    if (tableBodyRef.current && leaderboard?.entries.length) {
      const rowHeight = 60; // Approximate row height
      const scrollTop = currentScrollIndex * rowHeight;
      tableBodyRef.current.scrollTo({
        top: scrollTop,
        behavior: 'smooth'
      });
    }
  }, [currentScrollIndex, leaderboard?.entries.length]);

  const loadLeaderboard = async () => {
    try {
      setLoading(true);
      const data = await getEventLeaderboard(eventId, filters);
      setLeaderboard(data);
    } catch (error: any) {
      console.error('Error loading leaderboard:', error);
      toast.error('Failed to load leaderboard');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      await loadLeaderboard();
      if (onScoreUpdate) {
        onScoreUpdate();
      }
      toast.success('Leaderboard refreshed');
    } catch (error: any) {
      console.error('Error refreshing leaderboard:', error);
      toast.error('Failed to refresh leaderboard');
    } finally {
      setRefreshing(false);
    }
  };

  const handleFilterChange = (key: keyof LeaderboardFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }));
  };

  const clearFilters = () => {
    setFilters({});
  };

  const toggleRowExpansion = (participantId: number) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(participantId)) {
        newSet.delete(participantId);
      } else {
        newSet.add(participantId);
      }
      return newSet;
    });
  };

  // Auto-scroll control functions
  const toggleAutoScroll = () => {
    setIsAutoScrolling(prev => !prev);
    if (!isAutoScrolling) {
      setCurrentScrollIndex(0); // Reset to top when starting
    }
  };

  const resetScroll = () => {
    setCurrentScrollIndex(0);
    if (tableBodyRef.current) {
      tableBodyRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  };

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
  };

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="h-4 w-4 text-yellow-600" />;
    if (rank === 2) return <Trophy className="h-4 w-4 text-gray-600" />;
    if (rank === 3) return <Trophy className="h-4 w-4 text-orange-600" />;
    return null;
  };

  if (loading && !leaderboard) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-600">Loading leaderboard...</div>
      </div>
    );
  }

  if (!leaderboard) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-600">No leaderboard data available</div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${isFullScreen ? 'h-screen overflow-hidden' : ''}`}>
      {/* Header with Stats - Only show in normal mode */}
      {!isFullScreen && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <Users className="h-4 w-4 mr-2" />
                Total Participants
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {leaderboard.total_participants}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                With Scores
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {leaderboard.participants_with_scores}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Course Par
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {leaderboard.course_par}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center">
                <Clock className="h-4 w-4 mr-2" />
                Last Updated
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-gray-900">
                {formatLastUpdated(leaderboard.last_updated)}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            onClick={handleRefresh}
            disabled={refreshing}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          <Button
            onClick={() => setShowFilters(!showFilters)}
            variant="outline"
            size="sm"
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>

          {Object.keys(filters).length > 0 && (
            <Button
              onClick={clearFilters}
              variant="outline"
              size="sm"
            >
              Clear Filters
            </Button>
          )}

          {/* Auto-scroll controls */}
          {leaderboard?.entries.length > 0 && (
            <>
              <Button
                onClick={toggleAutoScroll}
                variant={isAutoScrolling ? "default" : "outline"}
                size="sm"
              >
                {isAutoScrolling ? (
                  <>
                    <Pause className="h-4 w-4 mr-2" />
                    Pause Scroll
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Auto Scroll
                  </>
                )}
              </Button>

              <Button
                onClick={resetScroll}
                variant="outline"
                size="sm"
                disabled={isAutoScrolling}
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Reset
              </Button>
            </>
          )}

          {onToggleFullScreen && (
            <Button
              onClick={onToggleFullScreen}
              variant="outline"
              size="sm"
            >
              {isFullScreen ? (
                <>
                  <Minimize2 className="h-4 w-4 mr-2" />
                  Exit Full Screen
                </>
              ) : (
                <>
                  <Maximize2 className="h-4 w-4 mr-2" />
                  Full Screen
                </>
              )}
            </Button>
          )}
        </div>

        <div className="flex items-center space-x-4">
          {/* Scroll position indicator */}
          {leaderboard?.entries.length > 0 && isAutoScrolling && (
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <Clock className="h-4 w-4" />
              <span>
                {currentScrollIndex + 1} / {leaderboard.entries.length}
              </span>
              <div className="w-16 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${((currentScrollIndex + 1) / leaderboard.entries.length) * 100}%` 
                  }}
                />
              </div>
            </div>
          )}

          <div className="text-sm text-gray-600">
            {leaderboard.scoring_type.replace('_', ' ').toUpperCase()} Scoring
          </div>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Filter Leaderboard</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Minimum Holes
                </label>
                <input
                  type="number"
                  min="0"
                  max="18"
                  value={filters.min_holes || ''}
                  onChange={(e) => handleFilterChange('min_holes', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Maximum Rank
                </label>
                <input
                  type="number"
                  min="1"
                  value={filters.max_rank || ''}
                  onChange={(e) => handleFilterChange('max_rank', e.target.value ? parseInt(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="All"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Division Name
                </label>
                <input
                  type="text"
                  value={filters.division_name || ''}
                  onChange={(e) => handleFilterChange('division_name', e.target.value || undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Any division"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Leaderboard Table */}
      <Card className={isFullScreen ? 'flex-1 flex flex-col' : ''}>
        <CardHeader className={isFullScreen ? 'flex-shrink-0' : ''}>
          <CardTitle className="flex items-center justify-between">
            <span>Leaderboard</span>
            <Badge variant="outline">
              {leaderboard.event_name}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className={isFullScreen ? 'flex-1 overflow-hidden' : ''}>
          {leaderboard.entries.length === 0 ? (
            <div className="text-center py-8 text-gray-600">
              No participants with scores yet
            </div>
          ) : (
            <div 
              ref={tableBodyRef}
              className={`overflow-x-auto ${isFullScreen ? 'h-full' : 'max-h-96'} overflow-y-auto`}
              onMouseEnter={handleMouseEnter}
              onMouseLeave={handleMouseLeave}
            >
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-700 w-12"></th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Rank</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Player</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Division</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Thru</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Gross</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Net</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">To Par</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Handicap</th>
                    {leaderboard.scoring_type === 'system_36' && (
                      <th className="text-left py-3 px-4 font-medium text-gray-700">Points</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.entries.map((entry: LeaderboardEntry) => (
                    <React.Fragment key={entry.participant_id}>
                      <tr className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleRowExpansion(entry.participant_id)}
                            className="h-6 w-6 p-0"
                          >
                            {expandedRows.has(entry.participant_id) ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </Button>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center space-x-2">
                            {getRankIcon(entry.rank)}
                            <span className={`font-semibold ${getRankColor(entry.rank)}`}>
                              {entry.rank}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium text-gray-900">
                            {entry.participant_name}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          {entry.division && (
                            <Badge variant="secondary" className="text-xs">
                              {entry.division}
                            </Badge>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-600">
                            {entry.thru}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-medium">
                            {entry.gross_score || '-'}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="font-medium">
                            {entry.net_score || '-'}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-1 rounded text-sm font-medium ${getScoreColor(entry.score_to_par)}`}>
                            {formatScoreToPar(entry.score_to_par)}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-sm text-gray-600">
                            {entry.handicap}
                          </span>
                        </td>
                        {leaderboard.scoring_type === 'system_36' && (
                          <td className="py-3 px-4">
                            <span className="font-medium text-blue-600">
                              {entry.system36_points || '-'}
                            </span>
                          </td>
                        )}
                      </tr>
                      {expandedRows.has(entry.participant_id) && (
                        <tr>
                          <td colSpan={leaderboard.scoring_type === 'system_36' ? 10 : 9} className="p-0">
                            <LeaderboardRowDetail
                              participantId={entry.participant_id}
                              participantName={entry.participant_name}
                              scoringType={leaderboard.scoring_type}
                            />
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default LeaderboardTable;
