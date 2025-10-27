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
import { Trophy, RefreshCw, Maximize, Minimize, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import MultiDivisionWinnerTable from '@/components/winners/MultiDivisionWinnerTable';
import {
  getEventWinners,
  WinnersListResponse,
  exportParticipantScores,
} from '@/services/winnerService';
import { toast } from 'sonner';

const WinnerPage: React.FC = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const [winnersData, setWinnersData] = useState<WinnersListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [exporting, setExporting] = useState(false);

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

  // Export participant scores
  const handleExportScores = async () => {
    if (!eventId) return;

    try {
      setExporting(true);
      await exportParticipantScores(parseInt(eventId));
      toast.success('Participant scores exported successfully');
    } catch (error: any) {
      console.error('Error exporting scores:', error);
      toast.error('Failed to export participant scores');
    } finally {
      setExporting(false);
    }
  };

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
    <div className="h-screen w-full flex flex-col bg-gray-50 overflow-hidden">
      {/* Header - Fixed at top */}
      <div className="bg-white shadow-sm border-b border-gray-200 flex-shrink-0">
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
                onClick={handleExportScores}
                disabled={exporting}
                variant="outline"
                size="lg"
                className="border-green-500 text-green-600 hover:bg-green-50"
              >
                <Download className="h-5 w-5 mr-2" />
                {exporting ? 'Exporting...' : 'Export Scores'}
              </Button>
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
        </div>
      </div>

      {/* Main Content - Scrollable */}
      <div className="flex-1 overflow-y-auto">
        <div className="w-full px-4 py-8">
          {winnersData && winnersData.winners.length > 0 ? (
            <MultiDivisionWinnerTable
              winners={winnersData.winners}
              eventName={winnersData.event_name}
              scoringType={winnersData.scoring_type}
            />
          ) : (
            <div className="w-full bg-white rounded-xl shadow-lg p-8 text-center">
              <Trophy className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h2 className="text-xl font-bold text-gray-600 mb-2">No Winners Yet</h2>
              <p className="text-gray-500">
                Winners need to be calculated before they can be displayed
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Footer - Fixed at bottom */}
      <div className="bg-white border-t border-gray-200 py-4 flex-shrink-0">
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