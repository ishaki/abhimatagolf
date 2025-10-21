import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatScoreToPar } from '@/services/scorecardService';

interface ScoreSummaryProps {
  participantName: string;
  handicap: number;
  outTotal: number;
  outToPar: number;
  inTotal: number;
  inToPar: number;
  grossScore: number;
  netScore: number;
  scoreToPar: number;
  coursePar: number;
  holesCompleted: number;
}

const ScoreSummary: React.FC<ScoreSummaryProps> = ({
  participantName,
  handicap,
  outTotal,
  outToPar,
  inTotal,
  inToPar,
  grossScore,
  netScore,
  scoreToPar,
  coursePar,
  holesCompleted,
}) => {
  return (
    <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-bold text-gray-800">
          Score Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Player Info */}
        <div className="bg-white rounded-lg p-3 shadow-sm">
          <div className="font-semibold text-gray-800">{participantName}</div>
          <div className="text-sm text-gray-600">Handicap: {handicap}</div>
        </div>

        {/* Out/In Totals */}
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-white rounded-lg p-3 shadow-sm">
            <div className="text-xs text-gray-500 uppercase font-medium">OUT (1-9)</div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-gray-800">{outTotal || '-'}</span>
              {outTotal > 0 && (
                <span className={`text-sm font-medium ${outToPar >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {formatScoreToPar(outToPar)}
                </span>
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg p-3 shadow-sm">
            <div className="text-xs text-gray-500 uppercase font-medium">IN (10-18)</div>
            <div className="flex items-baseline space-x-2">
              <span className="text-2xl font-bold text-gray-800">{inTotal || '-'}</span>
              {inTotal > 0 && (
                <span className={`text-sm font-medium ${inToPar >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {formatScoreToPar(inToPar)}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Gross Score */}
        <div className="bg-white rounded-lg p-4 shadow-sm border-2 border-blue-200">
          <div className="text-sm text-gray-500 uppercase font-medium mb-1">Gross Score</div>
          <div className="flex items-baseline space-x-3">
            <span className="text-3xl font-bold text-gray-900">{grossScore || '-'}</span>
            {grossScore > 0 && (
              <span className={`text-lg font-bold ${scoreToPar >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                {formatScoreToPar(scoreToPar)}
              </span>
            )}
          </div>
        </div>

        {/* Net Score */}
        <div className="bg-gradient-to-r from-indigo-500 to-blue-500 rounded-lg p-4 shadow-md text-white">
          <div className="text-sm uppercase font-medium mb-1 text-indigo-100">Net Score</div>
          <div className="flex items-baseline space-x-3">
            <span className="text-3xl font-bold">{netScore || '-'}</span>
            {netScore > 0 && (
              <span className="text-lg font-bold text-indigo-100">
                ({formatScoreToPar(netScore - coursePar)})
              </span>
            )}
          </div>
        </div>

        {/* Progress */}
        <div className="bg-white rounded-lg p-3 shadow-sm">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Holes Completed:</span>
            <span className="font-bold text-gray-800">{holesCompleted}/18</span>
          </div>
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(holesCompleted / 18) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Course Par Reference */}
        <div className="text-center text-sm text-gray-500">
          Course Par: {coursePar}
        </div>
      </CardContent>
    </Card>
  );
};

export default ScoreSummary;
