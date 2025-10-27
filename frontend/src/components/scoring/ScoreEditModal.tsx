import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import { Save, X, RefreshCw } from 'lucide-react';
import {
  bulkSubmitScores,
  ScorecardResponse,
  HoleScore,
} from '@/services/scorecardService';

interface ScoreEditModalProps {
  scorecard: ScorecardResponse;
  onClose: (updatedScorecard?: ScorecardResponse) => void;
}

const ScoreEditModal: React.FC<ScoreEditModalProps> = ({ scorecard, onClose }) => {
  const [scores, setScores] = useState<Record<number, number>>({});
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    // Initialize scores from scorecard
    const initialScores: Record<number, number> = {};
    [...scorecard.front_nine, ...scorecard.back_nine].forEach((hole) => {
      if (hole.strokes > 0) {
        initialScores[hole.hole_number] = hole.strokes;
      }
    });
    setScores(initialScores);
    setHasChanges(false);
  }, [scorecard]);

  const handleScoreChange = (holeNumber: number, value: string) => {
    const strokes = parseInt(value) || 0;
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

      const updatedScorecard = await bulkSubmitScores({
        participant_id: scorecard.participant_id,
        scores: holeScores,
      });

      toast.success('Scores saved successfully!');
      setHasChanges(false);
      onClose(updatedScorecard);
    } catch (error: any) {
      console.error('Error saving scores:', error);
      toast.error(error.response?.data?.detail || 'Failed to save scores');
    } finally {
      setSaving(false);
    }
  };

  const getScoreColor = (holeNumber: number) => {
    const hole = [...scorecard.front_nine, ...scorecard.back_nine].find(
      (h) => h.hole_number === holeNumber
    );
    const strokes = scores[holeNumber] || 0;
    if (!hole || strokes === 0) return '';

    const diff = strokes - hole.hole_par;
    if (diff <= -2) return 'bg-blue-100 text-blue-800 border-blue-300';
    if (diff === -1) return 'bg-green-100 text-green-800 border-green-300';
    if (diff === 0) return 'bg-white text-gray-800 border-gray-300';
    if (diff === 1) return 'bg-orange-100 text-orange-800 border-orange-300';
    return 'bg-red-100 text-red-800 border-red-300';
  };

  const calculateSubtotal = (start: number, end: number) => {
    let total = 0;
    for (let i = start; i <= end; i++) {
      total += scores[i] || 0;
    }
    return total;
  };

  const outTotal = calculateSubtotal(1, 9);
  const inTotal = calculateSubtotal(10, 18);
  const grossScore = outTotal + inTotal;

  return (
    <Dialog open={true} onOpenChange={() => onClose()}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold flex items-center justify-between">
            <div>
              <div>Edit Scores - {scorecard.participant_name}</div>
              <div className="text-sm font-normal text-gray-600 mt-1">
                {scorecard.event_name} • Handicap: {scorecard.handicap}
              </div>
            </div>
            <Button
              onClick={() => onClose()}
              variant="ghost"
              size="sm"
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="h-5 w-5" />
            </Button>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Front Nine */}
          <div>
            <h3 className="text-lg font-semibold mb-3 text-blue-700">Front Nine</h3>
            <div className="grid grid-cols-9 gap-2">
              {scorecard.front_nine.map((hole) => (
                <div key={hole.hole_number} className="text-center">
                  <div className="text-xs font-medium text-gray-500 mb-1">
                    Hole {hole.hole_number}
                  </div>
                  <div className="text-xs text-gray-600 mb-2">
                    Par {hole.hole_par}
                  </div>
                  <input
                    type="number"
                    min="0"
                    max="15"
                    value={scores[hole.hole_number] || ''}
                    onChange={(e) => handleScoreChange(hole.hole_number, e.target.value)}
                    onFocus={(e) => e.target.select()}
                    disabled={saving}
                    className={`w-full px-2 py-2 text-center text-lg font-bold border-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      scores[hole.hole_number] > 0 ? getScoreColor(hole.hole_number) : 'border-gray-300'
                    }`}
                    placeholder="-"
                  />
                </div>
              ))}
            </div>
            <div className="mt-3 text-right">
              <span className="text-sm font-medium text-gray-600">Out: </span>
              <span className="text-xl font-bold text-blue-600">{outTotal || '-'}</span>
            </div>
          </div>

          {/* Back Nine */}
          <div>
            <h3 className="text-lg font-semibold mb-3 text-indigo-700">Back Nine</h3>
            <div className="grid grid-cols-9 gap-2">
              {scorecard.back_nine.map((hole) => (
                <div key={hole.hole_number} className="text-center">
                  <div className="text-xs font-medium text-gray-500 mb-1">
                    Hole {hole.hole_number}
                  </div>
                  <div className="text-xs text-gray-600 mb-2">
                    Par {hole.hole_par}
                  </div>
                  <input
                    type="number"
                    min="0"
                    max="15"
                    value={scores[hole.hole_number] || ''}
                    onChange={(e) => handleScoreChange(hole.hole_number, e.target.value)}
                    onFocus={(e) => e.target.select()}
                    disabled={saving}
                    className={`w-full px-2 py-2 text-center text-lg font-bold border-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      scores[hole.hole_number] > 0 ? getScoreColor(hole.hole_number) : 'border-gray-300'
                    }`}
                    placeholder="-"
                  />
                </div>
              ))}
            </div>
            <div className="mt-3 text-right">
              <span className="text-sm font-medium text-gray-600">In: </span>
              <span className="text-xl font-bold text-indigo-600">{inTotal || '-'}</span>
            </div>
          </div>

          {/* Summary */}
          <div className="border-t pt-4 flex justify-between items-center">
            <div className="flex gap-6">
              <div>
                <div className="text-sm text-gray-600">Total Gross</div>
                <div className="text-2xl font-bold text-gray-900">{grossScore || '-'}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Net Score</div>
                <div className="text-2xl font-bold text-blue-600">
                  {grossScore > 0 ? grossScore - scorecard.handicap : '-'}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Holes Completed</div>
                <div className="text-2xl font-bold text-gray-900">
                  {Object.values(scores).filter((s) => s > 0).length}/18
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                onClick={() => onClose()}
                variant="outline"
                disabled={saving}
                className="border-gray-400 text-gray-700 bg-gray-100 hover:bg-gray-200 hover:border-gray-500"
              >
                Cancel
              </Button>
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
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ScoreEditModal;
