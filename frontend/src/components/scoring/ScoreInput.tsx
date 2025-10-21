import React from 'react';
import { Minus, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { getScoreColor } from '@/services/scorecardService';

interface ScoreInputProps {
  holeNumber: number;
  par: number;
  distance: number;
  strokes: number;
  onChange: (strokes: number) => void;
  colorCode: string;
  disabled?: boolean;
}

const ScoreInput: React.FC<ScoreInputProps> = ({
  holeNumber,
  par,
  distance,
  strokes,
  onChange,
  colorCode,
  disabled = false,
}) => {
  const handleIncrement = () => {
    if (strokes < 15) {
      onChange(strokes + 1);
    }
  };

  const handleDecrement = () => {
    if (strokes > 0) {
      onChange(strokes - 1);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value) || 0;
    if (value >= 0 && value <= 15) {
      onChange(value);
    }
  };

  const scoreToPar = strokes > 0 ? strokes - par : 0;
  const scoreColorClass = getScoreColor(colorCode);

  return (
    <div className="flex flex-col space-y-2 p-3 border rounded-lg bg-white">
      {/* Hole Header */}
      <div className="flex justify-between items-center">
        <div className="font-semibold text-sm text-gray-700">
          Hole {holeNumber}
        </div>
        <div className="text-xs text-gray-500">
          Par {par} • {distance}m
        </div>
      </div>

      {/* Score Input with +/- buttons */}
      <div className="flex items-center space-x-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleDecrement}
          disabled={disabled || strokes === 0}
          className="h-8 w-8 p-0"
        >
          <Minus className="h-4 w-4" />
        </Button>

        <Input
          type="number"
          min="0"
          max="15"
          value={strokes || ''}
          onChange={handleInputChange}
          disabled={disabled}
          className={`text-center font-bold text-lg h-10 w-16 ${scoreColorClass} border-2`}
          placeholder="-"
        />

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleIncrement}
          disabled={disabled || strokes === 15}
          className="h-8 w-8 p-0"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {/* Score to Par indicator */}
      {strokes > 0 && (
        <div className={`text-center text-xs font-medium ${scoreColorClass.split(' ')[0]}`}>
          {scoreToPar === 0 ? 'Par' : scoreToPar > 0 ? `+${scoreToPar}` : scoreToPar}
        </div>
      )}
    </div>
  );
};

export default ScoreInput;
