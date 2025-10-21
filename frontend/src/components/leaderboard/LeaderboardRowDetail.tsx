import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Loader2 } from 'lucide-react';
import { getParticipantScorecard, ScorecardResponse, HoleScoreResponse } from '../../services/scorecardService';

interface LeaderboardRowDetailProps {
  participantId: number;
  participantName: string;
  scoringType: string;
}

const LeaderboardRowDetail: React.FC<LeaderboardRowDetailProps> = ({
  participantId,
  participantName,
  scoringType
}) => {
  const [scorecard, setScorecard] = useState<ScorecardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchScorecard = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getParticipantScorecard(participantId);
        setScorecard(data);
      } catch (err) {
        setError('Failed to load scorecard');
        console.error('Error fetching scorecard:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchScorecard();
  }, [participantId]);

  const getScoreColor = (scoreToPar: number): string => {
    if (scoreToPar <= -2) return 'bg-red-100 text-red-800'; // Eagle or better
    if (scoreToPar === -1) return 'bg-yellow-100 text-yellow-800'; // Birdie
    if (scoreToPar === 0) return 'bg-green-100 text-green-800'; // Par
    if (scoreToPar === 1) return 'bg-orange-100 text-orange-800'; // Bogey
    if (scoreToPar >= 2) return 'bg-red-100 text-red-800'; // Double bogey or worse
    return 'bg-gray-100 text-gray-800';
  };

  const formatScoreToPar = (scoreToPar: number): string => {
    if (scoreToPar === 0) return 'E';
    if (scoreToPar > 0) return `+${scoreToPar}`;
    return scoreToPar.toString();
  };

  const renderHoleGrid = (holes: HoleScoreResponse[], title: string, total: number, toPar: number) => (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-900">{title}</h4>
        <div className="flex items-center space-x-4 text-sm">
          <span className="font-medium">Total: {total}</span>
          <Badge variant="outline" className={getScoreColor(toPar)}>
            {formatScoreToPar(toPar)}
          </Badge>
        </div>
      </div>
      
      <div className="grid grid-cols-9 gap-2">
        {holes.map((hole) => (
          <div key={hole.hole_number} className="text-center">
            <div className="text-xs text-gray-500 mb-1">Hole {hole.hole_number}</div>
            <div className="text-xs text-gray-400 mb-1">Par {hole.hole_par}</div>
            <div className={`px-2 py-1 rounded text-sm font-medium ${getScoreColor(hole.score_to_par)}`}>
              {hole.strokes}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {formatScoreToPar(hole.score_to_par)}
            </div>
            {scoringType === 'system_36' && hole.system36_points !== undefined && (
              <div className="text-xs text-blue-600 font-medium mt-1">
                {hole.system36_points}p
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  if (loading) {
    return (
      <Card className="mt-2">
        <CardContent className="py-6">
          <div className="flex items-center justify-center space-x-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Loading scorecard...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="mt-2">
        <CardContent className="py-6">
          <div className="text-center text-red-600">
            {error}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!scorecard) {
    return (
      <Card className="mt-2">
        <CardContent className="py-6">
          <div className="text-center text-gray-600">
            No scorecard data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-2">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">
          {participantName} - Hole by Hole Details
        </CardTitle>
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <span>Handicap: {scorecard.handicap}</span>
          <span>Course Par: {scorecard.course_par}</span>
          <span>Holes Completed: {scorecard.holes_completed}</span>
          {scorecard.last_updated && (
            <span>Last Updated: {new Date(scorecard.last_updated).toLocaleString()}</span>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Front Nine */}
        {renderHoleGrid(
          scorecard.front_nine,
          'Front Nine',
          scorecard.out_total,
          scorecard.out_to_par
        )}

        {/* Back Nine */}
        {renderHoleGrid(
          scorecard.back_nine,
          'Back Nine',
          scorecard.in_total,
          scorecard.in_to_par
        )}

        {/* Overall Summary */}
        <div className="border-t pt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-sm text-gray-500">Gross Score</div>
              <div className="text-lg font-semibold">{scorecard.gross_score}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Net Score</div>
              <div className="text-lg font-semibold">{scorecard.net_score}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">To Par</div>
              <div className={`text-lg font-semibold ${getScoreColor(scorecard.score_to_par)}`}>
                {formatScoreToPar(scorecard.score_to_par)}
              </div>
            </div>
            {scoringType === 'system_36' && (
              <div className="text-center">
                <div className="text-sm text-gray-500">System 36 Points</div>
                <div className="text-lg font-semibold text-blue-600">
                  {scorecard.system36_points || 0}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default LeaderboardRowDetail;
