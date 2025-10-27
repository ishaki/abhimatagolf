import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Edit2 } from 'lucide-react';
import { getEventScorecards, ScorecardResponse } from '@/services/scorecardService';
import { toast } from 'sonner';
import ScoreEditModal from './ScoreEditModal';
import { usePermissions } from '@/hooks/usePermissions';

interface MultiParticipantScorecardProps {
  eventId: number;
  event?: any; // Add event data for permission checking
  onScoreUpdate?: () => void;
}

const MultiParticipantScorecard: React.FC<MultiParticipantScorecardProps> = ({
  eventId,
  event,
  onScoreUpdate,
}) => {
  const { canManageScores } = usePermissions();
  const [scorecards, setScorecards] = useState<ScorecardResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingParticipant, setEditingParticipant] = useState<ScorecardResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    loadScorecards();
  }, [eventId]);

  // Initialize search term from searchQuery
  useEffect(() => {
    setSearchTerm(searchQuery);
  }, []);

  // Debounced search effect
  useEffect(() => {
    if (searchTerm !== searchQuery) {
      setIsSearching(true);
    }
    
    const timeoutId = setTimeout(() => {
      setSearchQuery(searchTerm);
      setIsSearching(false);
    }, 300); // 300ms delay

    return () => clearTimeout(timeoutId);
  }, [searchTerm, searchQuery]);

  const loadScorecards = async () => {
    try {
      setLoading(true);
      const data = await getEventScorecards(eventId);
      setScorecards(data.scorecards);
    } catch (error: any) {
      console.error('Error loading scorecards:', error);
      toast.error('Failed to load scorecards');
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = (scorecard: ScorecardResponse) => {
    setEditingParticipant(scorecard);
  };

  const handleModalClose = (updatedScorecard?: ScorecardResponse) => {
    setEditingParticipant(null);
    
    if (updatedScorecard) {
      // Optimistic update: update only the specific scorecard in the state
      setScorecards(prevScorecards => 
        prevScorecards.map(scorecard => 
          scorecard.participant_id === updatedScorecard.participant_id 
            ? updatedScorecard 
            : scorecard
        )
      );
    } else {
      // If no updated scorecard (cancelled), reload all scorecards to ensure consistency
      loadScorecards();
    }
    
    // Still notify parent component for any side effects (like updating event stats)
    if (onScoreUpdate) {
      onScoreUpdate();
    }
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
  };

  const getScoreColor = (score: number, par: number) => {
    if (score === 0) return 'bg-white';
    const diff = score - par;
    if (diff <= -2) return 'bg-green-600'; // Eagle or better
    if (diff === -1) return 'bg-green-400'; // Birdie
    if (diff === 0) return 'bg-white border border-gray-300'; // Par
    if (diff === 1) return 'bg-red-200'; // Bogey
    if (diff >= 2) return 'bg-red-400'; // Double bogey or worse
    return 'bg-white';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-600">Loading scorecards...</div>
      </div>
    );
  }

  if (scorecards.length === 0) {
    return (
      <div className="bg-yellow-50 border-2 border-dashed border-yellow-200 rounded-lg p-12 text-center">
        <p className="text-gray-600">No participants found for this event.</p>
      </div>
    );
  }

  // Get hole information from first scorecard (all should have same course)
  const allHoles = scorecards[0] ? [...scorecards[0].front_nine, ...scorecards[0].back_nine] : [];

  // Filter scorecards based on search query
  const filteredScorecards = scorecards.filter((scorecard) => {
    if (!searchQuery.trim()) return true;
    
    const searchLower = searchQuery.toLowerCase();
    return (
      scorecard.participant_name?.toLowerCase().includes(searchLower)
    );
  }).sort((a, b) => {
    // Sort by participant name in ascending order
    const nameA = a.participant_name?.toLowerCase() || '';
    const nameB = b.participant_name?.toLowerCase() || '';
    return nameA.localeCompare(nameB);
  });

  return (
    <>
      {/* Color Legend with Search */}
      <div className="mb-4 p-4 bg-blue-100/50 rounded-lg border border-blue-200/50 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          {/* Score Legend */}
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-blue-800 mb-2">Score Legend:</h3>
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
              <div className="flex items-center gap-2">
                <div className="w-8 h-6 bg-white border border-gray-300 rounded"></div>
                <span className="font-medium text-blue-800">No Score</span>
              </div>
            </div>
          </div>

          {/* Search Input */}
          <div className="lg:w-80">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                placeholder="Search participants..."
                value={searchTerm}
                onChange={(e) => handleSearch(e.target.value)}
                className="block w-full pl-10 pr-8 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
              />
              {isSearching && (
                <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                </div>
              )}
              {searchTerm && !isSearching && (
                <button
                  onClick={() => handleSearch('')}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  <svg className="h-4 w-4 text-gray-400 hover:text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
            {searchQuery && (
              <div className="mt-1 text-xs text-gray-500">
                Showing {filteredScorecards.length} of {scorecards.length} participants
              </div>
            )}
          </div>
        </div>
      </div>

      {/* No Results Message */}
      {searchQuery && filteredScorecards.length === 0 && (
        <div className="bg-gray-50 border-2 border-dashed border-gray-200 rounded-lg p-8 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No participants found</h3>
          <p className="text-gray-600">No participants match your search for "{searchQuery}"</p>
          <button
            onClick={() => handleSearch('')}
            className="mt-3 text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            Clear search
          </button>
        </div>
      )}

      {/* Scorecard Table */}
      {(!searchQuery || filteredScorecards.length > 0) && (
        <div className="overflow-auto border rounded-lg shadow-sm bg-white" style={{ maxHeight: 'calc(100vh - 200px)' }}>
          <table className="w-full text-sm">
          <thead>
            {/* Header Row 1: Hole Numbers */}
            <tr className="border-b bg-gradient-to-r from-gray-50 via-gray-25 to-gray-50 text-gray-700">
              <th className="sticky left-0 z-20 bg-gradient-to-r from-gray-50 via-gray-25 to-gray-50 border-r px-4 py-2 text-left font-semibold text-gray-700">
                Player
              </th>
              {allHoles.slice(0, 9).map((hole) => (
                <th key={hole.hole_number} className="px-1 py-2 text-center font-semibold min-w-[45px]">
                  {hole.hole_number}
                </th>
              ))}
              <th className="px-2 py-2 text-center font-semibold bg-blue-50 border-x min-w-[45px]">
                Out
              </th>
              {allHoles.slice(9, 18).map((hole) => (
                <th key={hole.hole_number} className="px-1 py-2 text-center font-semibold min-w-[45px]">
                  {hole.hole_number}
                </th>
              ))}
              <th className="px-2 py-2 text-center font-semibold bg-blue-50 border-x min-w-[45px]">
                In
              </th>
              <th className="px-2 py-2 text-center font-semibold bg-gray-100 border-x min-w-[60px]">
                Total
              </th>
              <th className="sticky right-0 z-20 bg-gradient-to-r from-gray-50 via-gray-25 to-gray-50 border-l px-4 py-2 text-center font-semibold text-gray-700 min-w-[80px]">
                Edit
              </th>
            </tr>
            {/* Header Row 2: Par & Index */}
            <tr className="border-b bg-gradient-to-r from-gray-50 via-gray-25 to-gray-50 text-xs text-gray-700">
              <td className="sticky left-0 z-20 bg-gradient-to-r from-gray-50 via-gray-25 to-gray-50 border-r px-4 py-2"></td>
              {/* Front 9 Par/Index */}
              {allHoles.slice(0, 9).map((hole) => (
                <td key={`par-${hole.hole_number}`} className="px-1 py-1 text-center">
                  <div className="font-medium">Par {hole.hole_par}</div>
                  <div className="text-gray-500">Id {hole.handicap_index}</div>
                </td>
              ))}
              {/* Out column - no par info */}
              <td className="px-2 py-1 bg-blue-100 border-x"></td>
              {/* Back 9 Par/Index */}
              {allHoles.slice(9, 18).map((hole) => (
                <td key={`par-${hole.hole_number}`} className="px-1 py-1 text-center">
                  <div className="font-medium">Par {hole.hole_par}</div>
                  <div className="text-gray-500">Id {hole.handicap_index}</div>
                </td>
              ))}
              {/* In column - no par info */}
              <td className="px-2 py-1 bg-blue-100 border-x"></td>
              {/* Total column - no par info */}
              <td className="px-2 py-1 bg-gray-100 border-x"></td>
              {/* Edit column - no par info */}
              <td className="sticky right-0 z-20 bg-blue-50 border-l"></td>
            </tr>
          </thead>
          <tbody>
            {filteredScorecards.map((scorecard) => {
              const frontNineScores = allHoles.slice(0, 9).map((hole) => {
                const holeScore = scorecard.front_nine.find((h) => h.hole_number === hole.hole_number);
                return { hole, score: holeScore?.strokes || 0 };
              });
              const backNineScores = allHoles.slice(9, 18).map((hole) => {
                const holeScore = scorecard.back_nine.find((h) => h.hole_number === hole.hole_number);
                return { hole, score: holeScore?.strokes || 0 };
              });

              return (
                <tr key={scorecard.participant_id} className="border-b hover:bg-gray-50">
                  {/* Player Name */}
                  <td className="sticky left-0 z-20 bg-white border-r px-2 py-2 font-medium w-32">
                    <div 
                      className="truncate" 
                      title={`${scorecard.participant_name} (${scorecard.handicap})`}
                    >
                      {scorecard.participant_name} ({scorecard.handicap})
                    </div>
                  </td>

                  {/* Front 9 Scores */}
                  {frontNineScores.map(({ hole, score }) => (
                    <td
                      key={`score-${scorecard.participant_id}-${hole.hole_number}`}
                      className={`px-1 py-2 text-center font-semibold ${getScoreColor(score, hole.hole_par)}`}
                    >
                      {score > 0 ? score : '-'}
                    </td>
                  ))}

                  {/* Out Total */}
                  <td className="px-2 py-2 text-center font-bold bg-blue-100 border-x">
                    {scorecard.out_total || '-'}
                  </td>

                  {/* Back 9 Scores */}
                  {backNineScores.map(({ hole, score }) => (
                    <td
                      key={`score-${scorecard.participant_id}-${hole.hole_number}`}
                      className={`px-1 py-2 text-center font-semibold ${getScoreColor(score, hole.hole_par)}`}
                    >
                      {score > 0 ? score : '-'}
                    </td>
                  ))}

                  {/* In Total */}
                  <td className="px-2 py-2 text-center font-bold bg-blue-100 border-x">
                    {scorecard.in_total || '-'}
                  </td>

                  {/* Total */}
                  <td className="px-2 py-2 text-center font-bold bg-gray-100 border-x">
                    {scorecard.gross_score || '-'}
                  </td>

                  {/* Edit Button */}
                  <td className="sticky right-0 z-20 bg-white border-l px-4 py-2 text-center">
                    {canManageScores(eventId, event) && (
                      <Button
                        onClick={() => handleEditClick(scorecard)}
                        size="sm"
                        variant="outline"
                        className="border-blue-300 text-blue-600 hover:bg-blue-50"
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      )}

      {/* Score Edit Modal */}
      {editingParticipant && (
        <ScoreEditModal
          scorecard={editingParticipant}
          onClose={handleModalClose}
        />
      )}
    </>
  );
};

export default MultiParticipantScorecard;
