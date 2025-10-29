import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Event, getParticipantStats } from '@/services/eventService';
import { ParticipantStats } from '@/services/participantService';
import EventForm from './EventForm';

interface EventOverviewProps {
  event: Event;
  onEventUpdate: () => void;
  onEditEvent?: () => void;
  onToggleStatus?: () => void;
  onDeleteEvent?: () => void;
}

const EventOverview: React.FC<EventOverviewProps> = ({ 
  event, 
  onEventUpdate
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [stats, setStats] = useState<ParticipantStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);

  useEffect(() => {
    loadParticipantStats();
  }, [event.id]);

  const loadParticipantStats = async () => {
    try {
      setLoadingStats(true);
      const statsData = await getParticipantStats(event.id);
      setStats(statsData);
    } catch (error) {
      console.error('Error loading participant stats:', error);
      // Don't show error toast, just fail silently for stats
    } finally {
      setLoadingStats(false);
    }
  };

  const handleEditSuccess = () => {
    setIsEditing(false);
    onEventUpdate();
  };

  const handleEditCancel = () => {
    setIsEditing(false);
  };

  // Use passed handlers or local fallbacks

  const getScoringTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      stroke: 'Stroke Play',
      net_stroke: 'Net Stroke',
      system_36: 'System 36',
      stableford: 'Stableford'
    };
    return labels[type] || type;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (isEditing) {
    return (
      <div className="max-w-4xl">
        <div className="mb-4">
          <Button onClick={handleEditCancel} variant="outline" className="border-gray-400 text-gray-700 bg-gray-100 hover:bg-gray-200 hover:border-gray-500">
            ← Cancel Editing
          </Button>
        </div>
        <EventForm event={event} onSuccess={handleEditSuccess} onCancel={handleEditCancel} />
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl">

      {/* Statistics Cards - Modern Design */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Participants Card */}
        <Card className="shadow-sm hover:shadow-md transition-shadow border border-gray-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Participants
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-4xl font-bold text-gray-900">
                {loadingStats ? (
                  <div className="animate-pulse bg-gray-200 rounded-lg w-16 h-10"></div>
                ) : (
                  stats?.total_participants || 0
                )}
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Average Handicap Card */}
        <Card className="shadow-sm hover:shadow-md transition-shadow border border-gray-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Average Handicap
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-4xl font-bold text-gray-900">
                {loadingStats ? (
                  <div className="animate-pulse bg-gray-200 rounded-lg w-16 h-10"></div>
                ) : (
                  stats?.average_handicap?.toFixed(1) || 'N/A'
                )}
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Total Divisions Card */}
        <Card className="shadow-sm hover:shadow-md transition-shadow border border-gray-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Divisions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-4xl font-bold text-gray-900">
                {loadingStats ? (
                  <div className="animate-pulse bg-gray-200 rounded-lg w-16 h-10"></div>
                ) : (
                  stats?.by_division ? Object.keys(stats.by_division).length : 0
                )}
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Scoring Type Card */}
        <Card className="shadow-sm hover:shadow-md transition-shadow border border-gray-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Scoring Type
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-lg font-semibold text-gray-900">
                  {getScoringTypeLabel(event.scoring_type)}
                </div>
                {event.scoring_type === 'system_36' && event.system36_variant && (
                  <div className="text-xs text-gray-600 mt-1 capitalize">
                    {event.system36_variant}
                  </div>
                )}
              </div>
              <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Participants by Division - Full Width Card with 3-Column Layout */}
      {stats && stats.by_division && Object.keys(stats.by_division).length > 0 && (
        <Card className="shadow-sm border border-gray-200">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-gray-900">
              Participants by Division
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(stats.by_division).map(([division, count]) => (
                <div
                  key={division}
                  className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors duration-200"
                >
                  <div className="flex-1 min-w-0 mr-3">
                    <div className="text-sm font-medium text-gray-900 truncate" title={division || 'No Division'}>
                      {division || 'No Division'}
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {count === 1 ? '1 participant' : `${count} participants`}
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <div className="inline-flex items-center justify-center w-10 h-10 bg-gray-100 rounded-lg">
                      <span className="text-lg font-bold text-gray-900">{count}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default EventOverview;
