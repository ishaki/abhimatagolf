import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import ParticipantList from '@/components/participants/ParticipantList';
import ParticipantForm from '@/components/participants/ParticipantForm';
import ParticipantUpload from '@/components/participants/ParticipantUpload';
import { Participant, getEventParticipants } from '@/services/participantService';
import { Event, getEvents } from '@/services/eventService';
import { eventDivisionService } from '@/services/eventDivisionService';
import { autoAssignDivisions } from '@/services/divisionAutoAssignService';
import { toast } from 'sonner';
import { Wand2 } from 'lucide-react';
import { useConfirm } from '@/hooks/useConfirm';

const ParticipantsPage: React.FC = () => {
  const { confirm } = useConfirm();
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | undefined>(undefined);
  const [selectedEvent, setSelectedEvent] = useState<Event | undefined>(undefined);
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [viewMode, setViewMode] = useState<'list' | 'form' | 'upload'>('list');
  const [editingParticipant, setEditingParticipant] = useState<Participant | undefined>(undefined);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    loadEvents();
  }, []);

  useEffect(() => {
    if (selectedEventId) {
      const event = events.find((e) => e.id === selectedEventId);
      setSelectedEvent(event);
    } else {
      setSelectedEvent(undefined);
    }
  }, [selectedEventId, events]);

  const loadEvents = async () => {
    try {
      setLoadingEvents(true);
      const response = await getEvents({ per_page: 100, is_active: true });
      setEvents(response.events);

      // Auto-select first event if available
      if (response.events.length > 0 && !selectedEventId) {
        setSelectedEventId(response.events[0].id);
      }
    } catch (error) {
      console.error('Error loading events:', error);
      toast.error('Failed to load events');
    } finally {
      setLoadingEvents(false);
    }
  };

  const handleCreateParticipant = () => {
    if (!selectedEventId) {
      toast.error('Please select an event first');
      return;
    }
    setEditingParticipant(undefined);
    setViewMode('form');
  };

  const handleUploadParticipants = () => {
    if (!selectedEventId) {
      toast.error('Please select an event first');
      return;
    }
    setViewMode('upload');
  };

  const handleAutoAssignDivisions = async () => {
    if (!selectedEventId) {
      toast.error('Please select an event first');
      return;
    }

    const confirmed = await confirm({
      title: 'Auto-Assign Divisions?',
      description: 'This will ONLY assign divisions to participants who have NO division currently assigned.\n\n✓ Participants WITH divisions will be SKIPPED (not changed)\n✓ Assignments based on: Handicap, Sex, and Name',
      variant: 'warning',
      confirmText: 'Continue',
      cancelText: 'Cancel',
    });

    if (!confirmed) return;

    try {
      toast.loading('Auto-assigning divisions...', { id: 'auto-assign' });

      // Fetch participants and divisions
      const participants = await getEventParticipants(selectedEventId);
      const divisions = await eventDivisionService.getDivisionsForEvent(selectedEventId);

      // Run auto-assignment
      const result = await autoAssignDivisions(participants, divisions);

      // Show result
      toast.dismiss('auto-assign');

      if (result.assigned > 0) {
        toast.success(
          `Successfully assigned ${result.assigned} participant(s) to divisions. ${result.skipped} skipped.`,
          { duration: 5000 }
        );
        
        // Refresh the participant list
        handleRefresh();
      } else {
        toast.warning(
          `No participants were assigned. ${result.skipped} skipped.`,
          { duration: 5000 }
        );
      }

      // Show errors if any
      if (result.errors.length > 0 && result.errors.length <= 5) {
        result.errors.forEach((error) => {
          toast.error(`${error.participantName}: ${error.reason}`, { duration: 4000 });
        });
      } else if (result.errors.length > 5) {
        toast.error(`${result.errors.length} participants could not be assigned`, { duration: 4000 });
      }
    } catch (error: any) {
      toast.dismiss('auto-assign');
      console.error('Error auto-assigning divisions:', error);
      toast.error('Failed to auto-assign divisions');
    }
  };

  const handleEditParticipant = (participant: Participant) => {
    setEditingParticipant(participant);
    setViewMode('form');
  };

  const handleFormSuccess = () => {
    setViewMode('list');
    setEditingParticipant(undefined);
    setRefreshKey((prev) => prev + 1);
    loadEvents(); // Refresh to update participant counts
  };

  const handleFormCancel = () => {
    setViewMode('list');
    setEditingParticipant(undefined);
  };

  const handleUploadSuccess = () => {
    setViewMode('list');
    setRefreshKey((prev) => prev + 1);
    loadEvents(); // Refresh to update participant counts
  };

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
    loadEvents(); // Refresh to update participant counts
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-lg border-b border-gray-200 px-8 py-3 flex-shrink-0">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Participant Management</h1>
            <p className="text-xs text-gray-600">
              Manage participants for golf tournaments
            </p>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-y-auto p-8">
        {/* Event Selector Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Select Event</CardTitle>
          </CardHeader>
          <CardContent>
            {loadingEvents ? (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-gray-600 mt-2">Loading events...</p>
              </div>
            ) : events.length === 0 ? (
              <div className="text-center py-8">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400 mb-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No active events found</h3>
                <p className="text-gray-600 mb-4">
                  Create an event first to manage participants.
                </p>
                <Button onClick={() => (window.location.href = '/events')}>
                  Go to Events
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Choose an event to manage participants:
                  </label>
                  <select
                    value={selectedEventId || ''}
                    onChange={(e) => {
                      const eventId = parseInt(e.target.value);
                      setSelectedEventId(eventId);
                      setViewMode('list'); // Reset to list view when changing events
                    }}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base"
                  >
                    <option value="">-- Select an event --</option>
                    {events.map((event) => (
                      <option key={event.id} value={event.id}>
                        {event.name} - {formatDate(event.event_date)} ({event.participant_count || 0}{' '}
                        participants)
                      </option>
                    ))}
                  </select>
                </div>

                {selectedEvent && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start">
                      <svg
                        className="h-5 w-5 text-blue-600 mr-3 mt-0.5"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-blue-900 mb-1">
                          Selected Event: {selectedEvent.name}
                        </h4>
                        <div className="text-sm text-blue-800 space-y-1">
                          <p>
                            <strong>Course:</strong> {selectedEvent.course_name || 'Unknown'}
                          </p>
                          <p>
                            <strong>Date:</strong> {formatDate(selectedEvent.event_date)}
                          </p>
                          <p>
                            <strong>Participants:</strong> {selectedEvent.participant_count || 0}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Participants Section - Only show if event is selected */}
        {selectedEventId && (
          <>
            {viewMode === 'list' && (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Participants for {selectedEvent?.name}
                  </h2>
                  <div className="flex space-x-2">
                    <Button
                      onClick={handleCreateParticipant}
                      variant="outline"
                      className="border-blue-300 text-blue-600 hover:bg-blue-50"
                    >
                      Add Participant
                    </Button>
                    <Button
                      onClick={handleAutoAssignDivisions}
                      variant="outline"
                      className="border-purple-300 text-purple-600 hover:bg-purple-50 flex items-center gap-1"
                    >
                      <Wand2 className="w-4 h-4" />
                      Auto-Assign Divisions
                    </Button>
                    <Button
                      onClick={handleUploadParticipants}
                      className="bg-blue-500 hover:bg-blue-600 text-white"
                    >
                      Upload Participants
                    </Button>
                  </div>
                </div>
                <ParticipantList
                  key={refreshKey}
                  eventId={selectedEventId}
                  onEditParticipant={handleEditParticipant}
                  onRefresh={handleRefresh}
                />
              </div>
            )}

            {viewMode === 'form' && (
              <div>
                <Button onClick={handleFormCancel} variant="outline" className="mb-4">
                  ← Back to List
                </Button>
                <ParticipantForm
                  participant={editingParticipant}
                  eventId={selectedEventId}
                  onSuccess={handleFormSuccess}
                  onCancel={handleFormCancel}
                />
              </div>
            )}

            {viewMode === 'upload' && (
              <div>
                <Button onClick={handleFormCancel} variant="outline" className="mb-4">
                  ← Back to List
                </Button>
                <ParticipantUpload
                  eventId={selectedEventId}
                  onUploadSuccess={handleUploadSuccess}
                  onCancel={handleFormCancel}
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ParticipantsPage;
