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
import { Participant, getEventParticipants } from '@/services/participantService';
import { eventDivisionService } from '@/services/eventDivisionService';
import { autoAssignDivisions } from '@/services/divisionAutoAssignService';
import MultiParticipantScorecard from '@/components/scoring/MultiParticipantScorecard';
import AddEventUserModal from '@/components/events/AddEventUserModal';
import EventUserPermissionsModal from '@/components/events/EventUserPermissionsModal';
import WinnerConfigurationForm from '@/components/winners/WinnerConfigurationForm';
import { ExternalLink, Trophy, Wand2, Loader2, Settings, Target } from 'lucide-react';
import { usePermissions } from '@/hooks/usePermissions';
import { useConfirm } from '@/hooks/useConfirm';

const EventDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { canAccessWinners, canConfigureWinners, canCreateEventUsers, canManageParticipants, isSuperAdmin } = usePermissions();
  const { confirm } = useConfirm();
  const [event, setEvent] = useState<Event | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [participantViewMode, setParticipantViewMode] = useState<'list' | 'form' | 'upload'>('list');
  const [calculatingWinners, setCalculatingWinners] = useState(false);
  const [editingParticipant, setEditingParticipant] = useState<Participant | undefined>(undefined);
  const [refreshKey, setRefreshKey] = useState(0);
  const [showAddEventUserModal, setShowAddEventUserModal] = useState(false);
  const [showPermissionsModal, setShowPermissionsModal] = useState(false);

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
    // For event detail changes (name, date, etc.) - reload event data
    loadEvent();
    setRefreshKey(prev => prev + 1);
  };

  const handleScoreUpdate = () => {
    // For scoring updates - no reload needed due to optimistic updates
    // The MultiParticipantScorecard handles its own state updates
  };

  const handleAddParticipant = () => {
    setEditingParticipant(undefined);
    setParticipantViewMode('form');
  };

  const handleUploadParticipants = () => {
    setParticipantViewMode('upload');
  };

  const handleAutoAssignDivisions = async () => {
    if (!event) return;

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
      const participants = await getEventParticipants(event.id);
      const divisions = await eventDivisionService.getDivisionsForEvent(event.id);

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
        handleParticipantRefresh();
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

  const handleAssignMenDivisionsByCourseHandicap = async () => {
    if (!event) return;

    // Only show for System 36 Standard events
    if (event.scoring_type !== 'system_36' || event.system36_variant !== 'standard') {
      toast.error('This feature is only available for System 36 Standard events');
      return;
    }

    const confirmed = await confirm({
      title: 'Assign Men Divisions by Course Handicap?',
      description: 'This will assign Men divisions (A/B/C) based on course handicap instead of declared handicap.\n\n✓ Only affects participants without divisions or in generic "Men" division\n✓ Requires teeboxes to be assigned first\n✓ Uses course handicap calculated from teebox slope rating',
      variant: 'warning',
      confirmText: 'Continue',
      cancelText: 'Cancel',
    });

    if (!confirmed) return;

    try {
      toast.loading('Assigning Men divisions by course handicap...', { id: 'men-assign' });

      const result = await eventDivisionService.assignMenDivisionsByCourseHandicap(event.id);

      toast.dismiss('men-assign');

      if (result.assigned > 0) {
        toast.success(
          `Successfully assigned ${result.assigned} participant(s) to Men divisions. ${result.skipped} skipped.`,
          { duration: 5000 }
        );
        
        // Refresh the participant list
        handleParticipantRefresh();
      } else {
        toast.warning(
          `No participants were assigned. ${result.skipped} skipped.`,
          { duration: 5000 }
        );
      }

      // Show errors if any
      if (result.errors.length > 0 && result.errors.length <= 5) {
        result.errors.forEach((error) => {
          toast.error(`${error.participant_name}: ${error.reason}`, { duration: 4000 });
        });
      } else if (result.errors.length > 5) {
        toast.error(`${result.errors.length} participants could not be assigned`, { duration: 4000 });
      }
    } catch (error: any) {
      toast.dismiss('men-assign');
      console.error('Error assigning Men divisions:', error);
      toast.error('Failed to assign Men divisions by course handicap');
    }
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

  const handleAddEventUser = () => {
    setShowAddEventUserModal(true);
  };

  const handleEventUserCreated = () => {
    setShowAddEventUserModal(false);
    // Could refresh event users list here if needed
    toast.success('Event user created successfully');
  };

  const handleManagePermissions = () => {
    setShowPermissionsModal(true);
  };

  const handlePermissionsUpdated = () => {
    // Could refresh event users list here if needed
    toast.success('Permissions updated successfully');
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
    
    const confirmed = await confirm({
      title: `Delete "${event.name}"?`,
      description: `Are you sure you want to delete "${event.name}"? This will permanently delete all participants, scores, and data associated with this event.`,
      variant: 'danger',
      confirmText: 'Delete',
      cancelText: 'Cancel',
    });

    if (confirmed) {
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
    <div className="h-screen w-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 flex flex-col">
      {/* Modern Header */}
      <div className="bg-gradient-to-r from-blue-100 via-blue-50 to-blue-100 text-blue-900 shadow-lg border-b border-blue-200/50 px-8 py-6 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            {/* Event Title */}
            <div className="space-y-2">
              <h1 className="text-3xl font-bold text-blue-900 tracking-tight">
                {event.name}
              </h1>
              <p className="text-sm text-blue-700">
                {event.course_name || 'Unknown Course'} • {formatDate(event.event_date)}
              </p>
            </div>
          </div>

          <Button
            onClick={() => navigate('/events')}
            variant="outline"
            className="bg-blue-200/50 backdrop-blur-sm border-blue-300 text-blue-800 hover:bg-blue-300/50 hover:border-blue-400 transition-all duration-300 shadow-lg"
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Events
          </Button>
        </div>
      </div>

      {/* Main Content with Sidebar */}
      <div className="flex-1 flex min-h-0">
        {/* Main Content Area */}
        <div className="flex-1 min-h-0 overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
            <div className="bg-white/95 backdrop-blur-sm border-b border-gray-200/50 px-8 flex-shrink-0 shadow-sm">
              <TabsList className="bg-transparent border-b-0 h-14">
                <TabsTrigger
                  value="overview"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg rounded-lg mx-1 transition-all duration-300 hover:bg-blue-50 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <span>Overview</span>
                </TabsTrigger>
                <TabsTrigger
                  value="divisions"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-500 data-[state=active]:to-purple-600 data-[state=active]:text-white data-[state=active]:shadow-lg rounded-lg mx-1 transition-all duration-300 hover:bg-purple-50 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  <span>Divisions</span>
                </TabsTrigger>
                <TabsTrigger
                  value="participants"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-500 data-[state=active]:to-emerald-600 data-[state=active]:text-white data-[state=active]:shadow-lg rounded-lg mx-1 transition-all duration-300 hover:bg-emerald-50 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <span>Participants</span>
                </TabsTrigger>
                <TabsTrigger
                  value="scoring"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-orange-600 data-[state=active]:text-white data-[state=active]:shadow-lg rounded-lg mx-1 transition-all duration-300 hover:bg-orange-50 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                  </svg>
                  <span>Scoring</span>
                </TabsTrigger>
                <TabsTrigger
                  value="livescore"
                  className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-red-500 data-[state=active]:to-red-600 data-[state=active]:text-white data-[state=active]:shadow-lg rounded-lg mx-1 transition-all duration-300 hover:bg-red-50 flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span>Live Score</span>
                </TabsTrigger>
                {canConfigureWinners(event?.id, event) && (
                  <TabsTrigger
                    value="winner-config"
                    className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-indigo-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-lg rounded-lg mx-1 transition-all duration-300 hover:bg-indigo-50 flex items-center space-x-2"
                  >
                    <Settings className="w-4 h-4" />
                    <span>Winner Configuration</span>
                  </TabsTrigger>
                )}
                {canAccessWinners(event?.id, event) && (
                  <TabsTrigger
                    value="winners"
                    className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-yellow-500 data-[state=active]:to-yellow-600 data-[state=active]:text-white data-[state=active]:shadow-lg rounded-lg mx-1 transition-all duration-300 hover:bg-yellow-50 flex items-center space-x-2"
                  >
                    <Trophy className="w-4 h-4" />
                    <span>Winners</span>
                  </TabsTrigger>
                )}
              </TabsList>
            </div>

            <div className="flex-1 overflow-y-auto overflow-x-hidden">
            <TabsContent value="overview" className="p-8 pb-20 m-0 pt-2 animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
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

            <TabsContent value="divisions" className="p-8 pb-20 m-0 pt-2 animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
              <EventDivisionManager
                eventId={event.id}
                event={event}
                onDivisionsChange={() => {
                  setRefreshKey(prev => prev + 1);
                  loadEvent(); // Refresh participant count
                }}
              />
            </TabsContent>

            <TabsContent value="participants" className="p-8 pb-20 m-0 pt-2 animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
              {participantViewMode === 'list' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h2 className="text-xl font-semibold text-gray-900">
                      Manage Participants
                    </h2>
                    <div className="flex space-x-2">
                      {canManageParticipants(event?.id, event) && (
                        <>
                          <Button
                            onClick={handleAddParticipant}
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
                          {/* {event.scoring_type === 'system_36' && event.system36_variant === 'standard' && (
                            <Button
                              onClick={handleAssignMenDivisionsByCourseHandicap}
                              variant="outline"
                              className="border-orange-300 text-orange-600 hover:bg-orange-50 flex items-center gap-1"
                            >
                              <Target className="w-4 h-4" />
                              Assign Men Divisions (Course HCP)
                            </Button>
                          )} */}
                          <Button
                            onClick={handleUploadParticipants}
                            className="bg-blue-500 hover:bg-blue-600 text-white"
                          >
                            Upload Participants
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                  <ParticipantList
                    key={refreshKey}
                    eventId={event.id}
                    event={event}
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

            <TabsContent value="scoring" className="p-8 pb-20 m-0 pt-2 animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
              <MultiParticipantScorecard
                eventId={event!.id}
                event={event}
                onScoreUpdate={handleScoreUpdate}
              />
            </TabsContent>

            <TabsContent value="livescore" className="p-8 pb-20 m-0 pt-2 animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
              <div className="max-w-4xl mx-auto">
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

            {canConfigureWinners(event?.id, event) && (
              <TabsContent value="winner-config" className="p-8 pb-20 m-0 pt-2 animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
                <WinnerConfigurationForm
                  eventId={event!.id}
                  onSuccess={() => {
                    toast.success('Configuration saved successfully');
                  }}
                />
              </TabsContent>
            )}

            {canAccessWinners(event?.id, event) && (
              <TabsContent value="winners" className="p-8 pb-20 m-0 pt-2 animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
              <div className="max-w-4xl mx-auto">
                <div className="bg-white rounded-lg shadow-md p-6 text-center">
                  <div className="mb-4">
                    <Trophy className="h-12 w-12 text-yellow-500 mx-auto mb-3" />
                    <h2 className="text-xl font-bold text-gray-900 mb-2">
                      Tournament Winners
                    </h2>
                    <p className="text-gray-600">
                      Display the official tournament winners and results
                    </p>
                  </div>

                  <div className="space-y-3">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                      <p className="text-sm text-blue-700 mb-3">
                        Winners must be calculated before they can be displayed. This will analyze all scorecards and determine rankings with proper tie-breaking.
                      </p>

                    </div>
                  <Button
                        onClick={async () => {
                          if (calculatingWinners) return; // Prevent multiple clicks
                          
                          try {
                            setCalculatingWinners(true);
                            toast.loading('Calculating winners...', { id: 'calculate-winners' });
                            
                            const { calculateEventWinners } = await import('@/services/winnerService');
                            await calculateEventWinners(event!.id);
                            
                            // Dismiss loading toast
                            toast.dismiss('calculate-winners');
                            
                            // Show success with enhanced message
                            toast.success('🎉 Winners calculated successfully! Tournament results are now ready.', {
                              duration: 5000,
                              description: 'You can now view the official tournament winners and rankings.'
                            });
                            
                          } catch (error) {
                            console.error('Error calculating winners:', error);
                            toast.dismiss('calculate-winners');
                            toast.error('Failed to calculate winners', {
                              description: 'Please try again or contact support if the issue persists.'
                            });
                          } finally {
                            setCalculatingWinners(false);
                          }
                        }}
                        disabled={calculatingWinners}
                        variant="outline"
                        className={`w-full transition-all duration-200 ${
                          calculatingWinners 
                            ? 'bg-yellow-400 text-white cursor-not-allowed' 
                            : 'bg-yellow-500 hover:bg-yellow-600 text-white hover:scale-105'
                        }`}
                      >
                        {calculatingWinners ? (
                          <>
                            <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                            Calculating Winners...
                          </>
                        ) : (
                          <>
                            <Wand2 className="h-5 w-5 mr-2" />
                            Calculate Winners Now
                          </>
                        )}
                      </Button>
                    <Button
                      onClick={() => window.open(`/winners/${event!.id}`, '_blank')}
                      size="lg"
                      className="w-full bg-blue-500 hover:bg-blue-600 text-white"
                    >
                      <ExternalLink className="h-5 w-5 mr-2" />
                      Open Winners Display
                    </Button>

                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-left">
                      <h3 className="font-semibold text-gray-900 mb-2">Share this link:</h3>
                      <div className="flex items-center gap-2">
                        <code className="flex-1 bg-white border border-gray-300 rounded px-3 py-2 text-sm text-gray-700">
                          {window.location.origin}/winners/{event!.id}
                        </code>
                        <Button
                          onClick={() => {
                            navigator.clipboard.writeText(`${window.location.origin}/winners/${event!.id}`);
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
            )}
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
            onAddEventUser={handleAddEventUser}
            onManagePermissions={handleManagePermissions}
            canCreateEventUsers={canCreateEventUsers()}
            canManagePermissions={isSuperAdmin()}
          />
        )}
      </div>

      {/* Mobile Quick Actions - Enhanced Bottom Bar - Only show on Overview tab */}
      {event && activeTab === 'overview' && (
        <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-gradient-to-r from-white via-gray-50/95 to-white border-t border-gray-200/50 p-4 z-50 backdrop-blur-sm shadow-2xl">
          <div className="flex space-x-3 overflow-x-auto pb-2">
            <Button
              onClick={handleEditEvent}
              size="sm"
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white whitespace-nowrap shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 flex items-center space-x-2 px-4 py-2"
            >
              <div className="w-5 h-5 bg-white/20 rounded-md flex items-center justify-center">
                <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </div>
              <span className="font-semibold">Edit</span>
            </Button>
            
            <Button
              onClick={handleToggleEventStatus}
              size="sm"
              variant="outline"
              className={`whitespace-nowrap shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 flex items-center space-x-2 px-4 py-2 border-2 ${
                event.is_active
                  ? 'border-orange-300 text-orange-600 hover:bg-orange-50 hover:border-orange-400'
                  : 'border-green-300 text-green-600 hover:bg-green-50 hover:border-green-400'
              }`}
            >
              <div className={`w-5 h-5 rounded-md flex items-center justify-center ${
                event.is_active ? 'bg-orange-100' : 'bg-green-100'
              }`}>
                <svg className={`w-3 h-3 ${
                  event.is_active ? 'text-orange-600' : 'text-green-600'
                }`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={
                    event.is_active
                      ? 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
                      : 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
                  } />
                </svg>
              </div>
              <span className="font-semibold">{event.is_active ? 'Deactivate' : 'Activate'}</span>
            </Button>
            
            <Button
              onClick={handleDeleteEvent}
              size="sm"
              variant="outline"
              className="border-2 border-red-300 text-red-600 hover:bg-red-50 hover:border-red-400 whitespace-nowrap shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 flex items-center space-x-2 px-4 py-2"
            >
              <div className="w-5 h-5 bg-red-100 rounded-md flex items-center justify-center">
                <svg className="w-3 h-3 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </div>
              <span className="font-semibold">Delete</span>
            </Button>
          </div>
        </div>
      )}

      {/* Add Event User Modal */}
      {event && (
        <AddEventUserModal
          isOpen={showAddEventUserModal}
          onClose={() => setShowAddEventUserModal(false)}
          eventId={event.id}
          eventName={event.name}
          onUserCreated={handleEventUserCreated}
        />
      )}

      {/* Event User Permissions Modal */}
      {event && (
        <EventUserPermissionsModal
          isOpen={showPermissionsModal}
          onClose={() => setShowPermissionsModal(false)}
          eventId={event.id}
          eventName={event.name}
          eventCreatedBy={event.created_by}
          onPermissionsUpdated={handlePermissionsUpdated}
        />
      )}
    </div>
  );
};

export default EventDetailPage;
