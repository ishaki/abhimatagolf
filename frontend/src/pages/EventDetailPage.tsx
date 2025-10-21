import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Event, getEvent } from '@/services/eventService';
import { toast } from 'sonner';
import EventOverview from '@/components/events/EventOverview';
import QuickActionsSidebar from '@/components/events/QuickActionsSidebar';
import EventDivisionManager from '@/components/events/EventDivisionManager';
import ParticipantList from '@/components/participants/ParticipantList';
import ParticipantForm from '@/components/participants/ParticipantForm';
import ParticipantUpload from '@/components/participants/ParticipantUpload';
import { Participant } from '@/services/participantService';
import MultiParticipantScorecard from '@/components/scoring/MultiParticipantScorecard';
import { ExternalLink, Trophy } from 'lucide-react';

const EventDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [event, setEvent] = useState<Event | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [participantViewMode, setParticipantViewMode] = useState<'list' | 'form' | 'upload'>('list');
  const [editingParticipant, setEditingParticipant] = useState<Participant | undefined>(undefined);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (id) {
      loadEvent();
    }
  }, [id]);

  const loadEvent = async () => {
    try {
      setLoading(true);
      const eventData = await getEvent(parseInt(id!));
      setEvent(eventData);
    } catch (error) {
      console.error('Error loading event:', error);
      toast.error('Failed to load event details');
      navigate('/events');
    } finally {
      setLoading(false);
    }
  };

  const handleEventUpdate = () => {
    loadEvent();
    setRefreshKey(prev => prev + 1);
  };

  const handleAddParticipant = () => {
    setEditingParticipant(undefined);
    setParticipantViewMode('form');
  };

  const handleUploadParticipants = () => {
    setParticipantViewMode('upload');
  };

  const handleEditParticipant = (participant: Participant) => {
    setEditingParticipant(participant);
    setParticipantViewMode('form');
  };

  const handleParticipantFormSuccess = () => {
    setParticipantViewMode('list');
    setEditingParticipant(undefined);
    setRefreshKey(prev => prev + 1);
    loadEvent(); // Refresh participant count
  };

  const handleParticipantFormCancel = () => {
    setParticipantViewMode('list');
    setEditingParticipant(undefined);
  };

  const handleParticipantUploadSuccess = () => {
    setParticipantViewMode('list');
    setRefreshKey(prev => prev + 1);
    loadEvent(); // Refresh participant count
  };

  const handleParticipantRefresh = () => {
    setRefreshKey(prev => prev + 1);
    loadEvent(); // Refresh participant count
  };

  // Quick Actions Sidebar handlers
  const handleEditEvent = () => {
    // This will trigger edit mode in EventOverview
    // We need to pass a ref or state to EventOverview to trigger edit mode
    // For now, we'll use a simple approach with a state variable
    setActiveTab('overview'); // Ensure we're on overview tab
    // The edit functionality will be handled by EventOverview's internal state
  };

  const handleToggleEventStatus = async () => {
    if (!event) return;
    
    try {
      const { updateEvent } = await import('@/services/eventService');
      await updateEvent(event.id, { is_active: !event.is_active });
      toast.success(
        `Event ${event.is_active ? 'deactivated' : 'activated'} successfully`
      );
      loadEvent(); // Refresh event data
    } catch (error) {
      console.error('Error updating event status:', error);
      toast.error('Failed to update event status');
    }
  };

  const handleDeleteEvent = async () => {
    if (!event) return;
    
    if (
      window.confirm(
        `Are you sure you want to delete "${event.name}"? This will permanently delete all participants, scores, and data associated with this event.`
      )
    ) {
      try {
        // Import deleteEvent function
        const { deleteEvent } = await import('@/services/eventService');
        await deleteEvent(event.id);
        toast.success('Event deleted successfully');
        navigate('/events');
      } catch (error) {
        console.error('Error deleting event:', error);
        toast.error('Failed to delete event');
      }
    }
  };

  if (loading) {
    return (
      <div className="h-screen w-screen overflow-hidden bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading event details...</p>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="h-screen w-screen overflow-hidden bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Event not found</p>
          <Button onClick={() => navigate('/events')} className="mt-4">
            Back to Events
          </Button>
        </div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-lg border-b border-gray-200 px-8 py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex-1">

            {/* Event Title */}
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                {event.name}
                <span className={`ml-3 px-2 py-1 rounded-full text-xs font-medium ${
                  event.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {event.is_active ? 'Active' : 'Inactive'}
                </span>
              </h1>
              <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                <span className="flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {event.course_name || 'Unknown Course'}
                </span>
                <span className="flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  {formatDate(event.event_date)}
                </span>
                <span className="flex items-center">
                  <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  {event.participant_count || 0} Participants
                </span>
              </div>
            </div>
          </div>

          <Button
            onClick={() => navigate('/events')}
            variant="outline"
            className="border-gray-300"
          >
            Back to Events
          </Button>
        </div>
      </div>

      {/* Main Content with Sidebar */}
      <div className="flex-1 overflow-hidden flex">
        {/* Main Content Area */}
        <div className="flex-1 overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <div className="bg-white border-b border-gray-200 px-8 flex-shrink-0">
              <TabsList className="bg-transparent border-b-0">
                <TabsTrigger
                  value="overview"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-blue-600 rounded-none"
                >
                  Overview
                </TabsTrigger>
                <TabsTrigger
                  value="divisions"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-blue-600 rounded-none"
                >
                  Divisions
                </TabsTrigger>
                <TabsTrigger
                  value="participants"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-blue-600 rounded-none"
                >
                  Participants
                </TabsTrigger>
                <TabsTrigger
                  value="scoring"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-blue-600 rounded-none"
                >
                  Scoring
                </TabsTrigger>
                <TabsTrigger
                  value="livescore"
                  className="data-[state=active]:border-b-2 data-[state=active]:border-blue-600 rounded-none"
                >
                  Live Score
                </TabsTrigger>
              </TabsList>
            </div>

            <div className={`flex-1 overflow-y-auto ${activeTab === 'overview' ? 'pb-20 lg:pb-0' : ''}`}>
            <TabsContent value="overview" className="p-8 m-0">
              <EventOverview 
                event={event} 
                onEventUpdate={handleEventUpdate}
                onEditEvent={() => {
                  // This will be handled by EventOverview's internal edit state
                }}
                onToggleStatus={handleToggleEventStatus}
                onDeleteEvent={handleDeleteEvent}
              />
            </TabsContent>

            <TabsContent value="divisions" className="p-8 m-0">
              <EventDivisionManager
                eventId={event.id}
                onDivisionsChange={() => {
                  setRefreshKey(prev => prev + 1);
                  loadEvent(); // Refresh participant count
                }}
              />
            </TabsContent>

            <TabsContent value="participants" className="p-8 m-0">
              {participantViewMode === 'list' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h2 className="text-xl font-semibold text-gray-900">
                      Manage Participants
                    </h2>
                    <div className="flex space-x-2">
                      <Button
                        onClick={handleAddParticipant}
                        variant="outline"
                        className="border-blue-300 text-blue-600 hover:bg-blue-50"
                      >
                        Add Participant
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
                    eventId={event.id}
                    onEditParticipant={handleEditParticipant}
                    onRefresh={handleParticipantRefresh}
                  />
                </div>
              )}

              {participantViewMode === 'form' && (
                <div>
                  <Button
                    onClick={handleParticipantFormCancel}
                    variant="outline"
                    className="mb-4"
                  >
                    ← Back to List
                  </Button>
                  <ParticipantForm
                    participant={editingParticipant}
                    eventId={event.id}
                    onSuccess={handleParticipantFormSuccess}
                    onCancel={handleParticipantFormCancel}
                  />
                </div>
              )}

              {participantViewMode === 'upload' && (
                <div>
                  <Button
                    onClick={handleParticipantFormCancel}
                    variant="outline"
                    className="mb-4"
                  >
                    ← Back to List
                  </Button>
                  <ParticipantUpload
                    eventId={event.id}
                    onUploadSuccess={handleParticipantUploadSuccess}
                    onCancel={handleParticipantFormCancel}
                  />
                </div>
              )}
            </TabsContent>

            <TabsContent value="scoring" className="p-8 m-0">
              <MultiParticipantScorecard
                eventId={event!.id}
                onScoreUpdate={handleEventUpdate}
              />
            </TabsContent>

            <TabsContent value="livescore" className="p-8 m-0">
              <div className="max-w-2xl mx-auto">
                <div className="bg-white rounded-lg shadow-md p-8 text-center">
                  <div className="mb-6">
                    <Trophy className="h-16 w-16 text-blue-500 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">
                      Live Score Display
                    </h2>
                    <p className="text-gray-600">
                      View real-time scores in a public display optimized for TV and projectors
                    </p>
                  </div>

                  <div className="space-y-4">
                    <Button
                      onClick={() => window.open(`/live-score/${event!.id}`, '_blank')}
                      size="lg"
                      className="w-full bg-blue-500 hover:bg-blue-600 text-white"
                    >
                      <ExternalLink className="h-5 w-5 mr-2" />
                      Open Live Score Display
                    </Button>

                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
                      <h3 className="font-semibold text-blue-900 mb-2">Features:</h3>
                      <ul className="text-sm text-blue-800 space-y-1">
                        <li>✓ Auto-scrolling carousel (5 seconds per page)</li>
                        <li>✓ Real-time score updates via WebSocket</li>
                        <li>✓ Full-screen mode for TV/projector</li>
                        <li>✓ Color-coded hole scores (Eagle, Birdie, Par, Bogey, Double+)</li>
                        <li>✓ Manual navigation controls (prev/next)</li>
                        <li>✓ No authentication required (public display)</li>
                      </ul>
                    </div>

                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-left">
                      <h3 className="font-semibold text-gray-900 mb-2">Share this link:</h3>
                      <div className="flex items-center gap-2">
                        <code className="flex-1 bg-white border border-gray-300 rounded px-3 py-2 text-sm text-gray-700">
                          {window.location.origin}/live-score/{event!.id}
                        </code>
                        <Button
                          onClick={() => {
                            navigator.clipboard.writeText(`${window.location.origin}/live-score/${event!.id}`);
                            toast.success('Link copied to clipboard!');
                          }}
                          variant="outline"
                          size="sm"
                        >
                          Copy
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
            </div>
          </Tabs>
        </div>

        {/* Quick Actions Sidebar - Only show on Overview tab */}
        {activeTab === 'overview' && (
          <QuickActionsSidebar
            event={event}
            onEditEvent={handleEditEvent}
            onToggleStatus={handleToggleEventStatus}
            onDeleteEvent={handleDeleteEvent}
          />
        )}
      </div>

      {/* Mobile Quick Actions - Bottom Bar - Only show on Overview tab */}
      {event && activeTab === 'overview' && (
        <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 z-50">
          <div className="flex space-x-2 overflow-x-auto">
            <Button
              onClick={handleEditEvent}
              size="sm"
              className="bg-blue-500 hover:bg-blue-600 text-white whitespace-nowrap"
            >
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Edit
            </Button>
            
            <Button
              onClick={handleToggleEventStatus}
              size="sm"
              variant="outline"
              className={`whitespace-nowrap ${
                event.is_active
                  ? 'border-orange-300 text-orange-600 hover:bg-orange-50'
                  : 'border-green-300 text-green-600 hover:bg-green-50'
              }`}
            >
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={
                  event.is_active
                    ? 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
                    : 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
                } />
              </svg>
              {event.is_active ? 'Deactivate' : 'Activate'}
            </Button>
            
            <Button
              onClick={handleDeleteEvent}
              size="sm"
              variant="outline"
              className="border-red-300 text-red-600 hover:bg-red-50 whitespace-nowrap"
            >
              <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              Delete
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventDetailPage;
