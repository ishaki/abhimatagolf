import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Save, RefreshCw, AlertCircle } from 'lucide-react';
import {
  getParticipantScorecard,
  bulkSubmitScores,
  type ScorecardResponse,
  type HoleScore,
} from '@/services/scorecardService';
import { useConfirm } from '@/hooks/useConfirm';

interface ScorecardGridProps {
  participantId: number;
  eventId: number;
  onScoreUpdate?: () => void;
}

const ScorecardGrid: React.FC<ScorecardGridProps> = ({
  participantId,
  onScoreUpdate,
}) => {
  const { confirm } = useConfirm();
  const [scorecard, setScorecard] = useState<ScorecardResponse | null>(null);
  const [scores, setScores] = useState<Record<number, number>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // Load scorecard on mount
  useEffect(() => {
    loadScorecard();
  }, [participantId]);

  const loadScorecard = async () => {
    try {
      setLoading(true);
      const data = await getParticipantScorecard(participantId);
      setScorecard(data);

      // Initialize scores from loaded scorecard
      const initialScores: Record<number, number> = {};
      [...data.front_nine, ...data.back_nine].forEach((hole) => {
        if (hole.strokes > 0) {
          initialScores[hole.hole_number] = hole.strokes;
        }
      });
      setScores(initialScores);
      setHasChanges(false);
    } catch (error: any) {
      console.error('Error loading scorecard:', error);
      toast.error('Failed to load scorecard');
    } finally {
      setLoading(false);
    }
  };

  const handleScoreChange = (holeNumber: number, value: string) => {
    const strokes = parseInt(value) || 0;

    // Validate range
    if (strokes < 0 || strokes > 15) return;

    setScores((prev) => ({
      ...prev,
      [holeNumber]: strokes,
    }));
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      // Prepare scores for submission
      const holeScores: HoleScore[] = Object.entries(scores)
        .filter(([_, strokes]) => strokes > 0)
        .map(([holeNumber, strokes]) => ({
          hole_number: parseInt(holeNumber),
          strokes,
        }));

      if (holeScores.length === 0) {
        toast.error('Please enter at least one score');
        return;
      }

      // Submit scores
      await bulkSubmitScores({
        participant_id: participantId,
        scores: holeScores,
      });

      toast.success('Scores saved successfully!');
      setHasChanges(false);

      // Reload scorecard to get updated calculations
      await loadScorecard();

      // Notify parent component
      if (onScoreUpdate) {
        onScoreUpdate();
      }
    } catch (error: any) {
      console.error('Error saving scores:', error);
      toast.error(error.response?.data?.detail || 'Failed to save scores');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    const confirmed = await confirm({
      title: 'Reset Changes?',
      description: 'Are you sure you want to reset all unsaved changes? This will discard any modifications you have made.',
      variant: 'warning',
      confirmText: 'Reset',
      cancelText: 'Cancel',
    });

    if (confirmed) {
      loadScorecard();
    }
  };

  // Calculate helpers
  const getScoreToPar = (holeNumber: number) => {
    if (!scorecard) return 0;
    const hole = [...scorecard.front_nine, ...scorecard.back_nine].find(
      (h) => h.hole_number === holeNumber
    );
    const strokes = scores[holeNumber] || 0;
    return strokes > 0 && hole ? strokes - hole.hole_par : 0;
  };

  const getColorClass = (scoreToPar: number) => {
    if (scoreToPar <= -2) return 'bg-blue-100 text-blue-800 font-semibold';
    if (scoreToPar === -1) return 'bg-green-100 text-green-800 font-semibold';
    if (scoreToPar === 0) return 'bg-white text-gray-800 border border-gray-300';
    if (scoreToPar === 1) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const formatToPar = (score: number) => {
    if (score === 0) return 'E';
    if (score > 0) return `+${score}`;
    return score.toString();
  };

  const calculateSubtotal = (start: number, end: number) => {
    let total = 0;
    for (let i = start; i <= end; i++) {
      total += scores[i] || 0;
    }
    return total;
  };

  const calculateToPar = (start: number, end: number) => {
    if (!scorecard) return 0;
    let totalStrokes = 0;
    let totalPar = 0;

    for (let i = start; i <= end; i++) {
      const hole = [...scorecard.front_nine, ...scorecard.back_nine].find(
        (h) => h.hole_number === i
      );
      if (hole) {
        totalStrokes += scores[i] || 0;
        totalPar += hole.hole_par;
      }
    }

    return totalStrokes > 0 ? totalStrokes - totalPar : 0;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-3 text-gray-600">Loading scorecard...</span>
      </div>
    );
  }

  if (!scorecard) {
    return (
      <div className="flex items-center justify-center py-12">
        <AlertCircle className="h-8 w-8 text-yellow-500" />
        <span className="ml-3 text-gray-600">No scorecard found</span>
      </div>
    );
  }

  const outTotal = calculateSubtotal(1, 9);
  const inTotal = calculateSubtotal(10, 18);
  const grossScore = outTotal + inTotal;
  // PHASE 3: No net score calculation - will be done on Winner Page

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            {scorecard.participant_name}
          </h2>
          <p className="text-sm text-gray-600">
            {scorecard.event_name} • Handicap: {scorecard.handicap} • Par: {scorecard.course_par}
          </p>
        </div>
        <div className="flex space-x-2">
          {hasChanges && (
            <Button onClick={handleReset} variant="outline" disabled={saving}>
              Reset
            </Button>
          )}
          <Button
            onClick={handleSave}
            disabled={!hasChanges || saving}
            className="bg-blue-500 hover:bg-blue-600"
          >
            {saving ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save Scores
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Scorecard Table */}
      <div className="border rounded-lg overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Hole
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Par
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Score
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  To Par
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {/* Front Nine */}
              {scorecard.front_nine.map((hole) => {
                const scoreToPar = getScoreToPar(hole.hole_number);
                return (
                  <tr key={hole.hole_number} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-semibold text-gray-900">{hole.hole_number}</span>
                    </td>
                    <td className="px-4 py-3 text-center text-sm text-gray-600">
                      {hole.hole_par}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <input
                        type="number"
                        min="0"
                        max="15"
                        value={scores[hole.hole_number] || ''}
                        onChange={(e) => handleScoreChange(hole.hole_number, e.target.value)}
                        disabled={saving}
                        className={`w-16 px-2 py-1 text-center border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          scores[hole.hole_number] > 0 ? getColorClass(scoreToPar) : ''
                        }`}
                        placeholder="-"
                      />
                    </td>
                    <td className="px-4 py-3 text-center">
                      {scores[hole.hole_number] > 0 && (
                        <span className={`text-sm font-medium ${
                          scoreToPar < 0 ? 'text-green-600' : scoreToPar > 0 ? 'text-red-600' : 'text-gray-600'
                        }`}>
                          {formatToPar(scoreToPar)}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}

              {/* OUT Subtotal */}
              <tr className="bg-blue-50 font-semibold">
                <td className="px-4 py-3">OUT</td>
                <td className="px-4 py-3 text-center">{scorecard.front_nine.reduce((sum, h) => sum + h.hole_par, 0)}</td>
                <td className="px-4 py-3 text-center text-blue-700">{outTotal || '-'}</td>
                <td className="px-4 py-3 text-center">
                  {outTotal > 0 && (
                    <span className={outTotal - scorecard.front_nine.reduce((sum, h) => sum + h.hole_par, 0) >= 0 ? 'text-red-600' : 'text-green-600'}>
                      {formatToPar(calculateToPar(1, 9))}
                    </span>
                  )}
                </td>
              </tr>

              {/* Back Nine */}
              {scorecard.back_nine.map((hole) => {
                const scoreToPar = getScoreToPar(hole.hole_number);
                return (
                  <tr key={hole.hole_number} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="font-semibold text-gray-900">{hole.hole_number}</span>
                    </td>
                    <td className="px-4 py-3 text-center text-sm text-gray-600">
                      {hole.hole_par}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <input
                        type="number"
                        min="0"
                        max="15"
                        value={scores[hole.hole_number] || ''}
                        onChange={(e) => handleScoreChange(hole.hole_number, e.target.value)}
                        disabled={saving}
                        className={`w-16 px-2 py-1 text-center border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                          scores[hole.hole_number] > 0 ? getColorClass(scoreToPar) : ''
                        }`}
                        placeholder="-"
                      />
                    </td>
                    <td className="px-4 py-3 text-center">
                      {scores[hole.hole_number] > 0 && (
                        <span className={`text-sm font-medium ${
                          scoreToPar < 0 ? 'text-green-600' : scoreToPar > 0 ? 'text-red-600' : 'text-gray-600'
                        }`}>
                          {formatToPar(scoreToPar)}
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}

              {/* IN Subtotal */}
              <tr className="bg-indigo-50 font-semibold">
                <td className="px-4 py-3">IN</td>
                <td className="px-4 py-3 text-center">{scorecard.back_nine.reduce((sum, h) => sum + h.hole_par, 0)}</td>
                <td className="px-4 py-3 text-center text-indigo-700">{inTotal || '-'}</td>
                <td className="px-4 py-3 text-center">
                  {inTotal > 0 && (
                    <span className={inTotal - scorecard.back_nine.reduce((sum, h) => sum + h.hole_par, 0) >= 0 ? 'text-red-600' : 'text-green-600'}>
                      {formatToPar(calculateToPar(10, 18))}
                    </span>
                  )}
                </td>
              </tr>

              {/* Total */}
              <tr className="bg-gray-100 font-bold text-lg">
                <td className="px-4 py-4">TOTAL</td>
                <td className="px-4 py-4 text-center">{scorecard.course_par}</td>
                <td className="px-4 py-4 text-center text-blue-700">{grossScore || '-'}</td>
                <td className="px-4 py-4 text-center">
                  {grossScore > 0 && (
                    <span className={grossScore - scorecard.course_par >= 0 ? 'text-red-600' : 'text-green-600'}>
                      {formatToPar(grossScore - scorecard.course_par)}
                    </span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary - PHASE 3: Simplified (Gross Score + To Par only) */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-600">Holes Completed</div>
          <div className="text-2xl font-bold text-gray-900">
            {Object.values(scores).filter((s) => s > 0).length}/18
          </div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-600">Gross Score</div>
          <div className="text-2xl font-bold text-blue-600">{grossScore || '-'}</div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="text-sm text-gray-600">To Par</div>
          <div className={`text-2xl font-bold ${
            grossScore > 0 ? (grossScore - scorecard.course_par >= 0 ? 'text-red-600' : 'text-green-600') : 'text-gray-400'
          }`}>
            {grossScore > 0 ? formatToPar(grossScore - scorecard.course_par) : '-'}
          </div>
        </div>
      </div>

      {/* Phase 3 Note */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-sm text-blue-800">
          <span className="font-semibold">Note:</span> Final rankings, net scores, and awards will be calculated on the Winner Page after all scores are submitted.
        </p>
      </div>

      {/* Unsaved Changes Warning */}
      {hasChanges && (
        <div className="fixed bottom-4 right-4 bg-yellow-50 border-2 border-yellow-400 rounded-lg shadow-lg p-4 max-w-sm">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div>
              <div className="font-semibold text-yellow-900">Unsaved Changes</div>
              <div className="text-sm text-yellow-700">
                Don't forget to save your scores!
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScorecardGrid;
