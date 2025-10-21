import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Event, getParticipantStats } from '@/services/eventService';
import { ParticipantStats } from '@/services/participantService';
import EventForm from './EventForm';
import ExcelExport from '@/components/excel/ExcelExport';

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
    <div className="space-y-6 max-w-7xl">
      {/* Event Information Card */}
      <Card>
        <CardHeader>
          <CardTitle>Event Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Event Name</h3>
              <p className="text-lg font-semibold text-gray-900">{event.name}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Status</h3>
              <span
                className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
                  event.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {event.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Course</h3>
              <p className="text-gray-900">{event.course_name || 'Unknown Course'}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Event Date</h3>
              <p className="text-gray-900">{formatDate(event.event_date)}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Scoring Type</h3>
              <p className="text-gray-900">{getScoringTypeLabel(event.scoring_type)}</p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">Created By</h3>
              <p className="text-gray-900">{event.creator_name || 'Unknown'}</p>
            </div>

            {event.description && (
              <div className="md:col-span-2">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Description</h3>
                <p className="text-gray-900">{event.description}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Participants
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {loadingStats ? '...' : stats?.total_participants || 0}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">
              Average Handicap
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {loadingStats ? '...' : stats?.average_handicap?.toFixed(1) || 'N/A'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-600">Divisions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900">
              {loadingStats
                ? '...'
                : stats?.by_division
                ? Object.keys(stats.by_division).length
                : 0}
            </div>
          </CardContent>
        </Card>

        {/* Participants by Division - Inline with other stats */}
        {stats && stats.by_division && Object.keys(stats.by_division).length > 0 && (
          <Card className="xl:col-span-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">
                Participants by Division
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(stats.by_division).slice(0, 3).map(([division, count]) => (
                  <div
                    key={division}
                    className="flex justify-between items-center py-1"
                  >
                    <div className="text-sm text-gray-600 truncate">
                      {division || 'No Division'}
                    </div>
                    <div className="text-lg font-bold text-gray-900">{count}</div>
                  </div>
                ))}
                {Object.keys(stats.by_division).length > 3 && (
                  <div className="text-xs text-gray-500 pt-1 border-t">
                    +{Object.keys(stats.by_division).length - 3} more
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Excel Export Section */}
      <Card>
        <CardHeader>
          <CardTitle>Export Data</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Export event data to Excel format for offline analysis and record keeping.
            </p>
            <ExcelExport
              eventId={event.id}
              hasParticipants={stats?.total_participants ? stats.total_participants > 0 : false}
              hasScorecards={false} // TODO: Add scorecard detection logic
            />
          </div>
        </CardContent>
      </Card>

    </div>
  );
};

export default EventOverview;
