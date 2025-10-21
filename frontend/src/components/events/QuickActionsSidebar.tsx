import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Event } from '@/services/eventService';

interface QuickActionsSidebarProps {
  event: Event;
  onEditEvent: () => void;
  onToggleStatus: () => void;
  onDeleteEvent: () => void;
}

const QuickActionsSidebar: React.FC<QuickActionsSidebarProps> = ({
  event,
  onEditEvent,
  onToggleStatus,
  onDeleteEvent,
}) => {
  return (
    <div className="hidden lg:block w-64 bg-white border-l border-gray-200 flex-shrink-0">
      <div className="p-6">
        <Card>
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold text-gray-900">
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              onClick={onEditEvent}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white justify-start"
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
              Edit Event Details
            </Button>

            <Button
              onClick={onToggleStatus}
              variant="outline"
              className={`w-full justify-start ${
                event.is_active
                  ? 'border-orange-300 text-orange-600 hover:bg-orange-50'
                  : 'border-green-300 text-green-600 hover:bg-green-50'
              }`}
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={
                    event.is_active
                      ? 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
                      : 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
                  }
                />
              </svg>
              {event.is_active ? 'Deactivate Event' : 'Activate Event'}
            </Button>

            <Button
              variant="outline"
              className="w-full border-purple-300 text-purple-600 hover:bg-purple-50 justify-start"
              disabled
              title="Export feature coming in Phase 2.5"
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              Export Data
            </Button>

            <Button
              onClick={onDeleteEvent}
              variant="outline"
              className="w-full border-red-300 text-red-600 hover:bg-red-50 justify-start"
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              Delete Event
            </Button>
          </CardContent>
        </Card>

        {/* Event Status Info */}
        <Card className="mt-4">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
                event.is_active
                  ? 'bg-green-100 text-green-800'
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {event.is_active ? 'Active Event' : 'Inactive Event'}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {event.is_active 
                  ? 'Event is currently active and accepting participants'
                  : 'Event is inactive and not accepting participants'
                }
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default QuickActionsSidebar;
