import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import EventList from '@/components/events/EventList';
import EventForm from '@/components/events/EventForm';
import { Event } from '@/services/eventService';
import { usePermissions } from '@/hooks/usePermissions';

const EventsPage: React.FC = () => {
  const { canCreateEvents } = usePermissions();
  const [showForm, setShowForm] = useState(false);
  const [editingEvent, setEditingEvent] = useState<Event | undefined>(undefined);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleCreateEvent = () => {
    setEditingEvent(undefined);
    setShowForm(true);
  };

  const handleEditEvent = (event: Event) => {
    setEditingEvent(event);
    setShowForm(true);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setEditingEvent(undefined);
    setRefreshKey(prev => prev + 1);
  };

  const handleFormCancel = () => {
    setShowForm(false);
    setEditingEvent(undefined);
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-lg border-b border-gray-200 px-8 py-3 flex-shrink-0">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Event Management</h1>
            <p className="text-xs text-gray-600">Manage golf tournaments and events</p>
          </div>
          {canCreateEvents() && (
            <Button 
              onClick={handleCreateEvent} 
              className="bg-blue-500 hover:bg-blue-600 text-white"
            >
              Create Event
            </Button>
          )}
        </div>
      </div>

            {/* Main content */}
            <div className="flex-1 overflow-y-auto">
              {showForm ? (
                <div className="p-8 pb-16">
                  <EventForm
                    event={editingEvent}
                    onSuccess={handleFormSuccess}
                    onCancel={handleFormCancel}
                  />
                </div>
              ) : (
                <div className="p-8">
                  {/* Events List */}
                  <EventList
                    key={refreshKey}
                    onEditEvent={handleEditEvent}
                    onRefresh={handleRefresh}
                  />
                </div>
              )}
            </div>
    </div>
  );
};

export default EventsPage;

