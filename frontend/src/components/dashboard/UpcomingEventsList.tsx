/**
 * Upcoming Events List Component
 * 
 * Displays upcoming events in a responsive list/table format.
 * Shows event details and allows navigation to event detail pages.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar, MapPin, Users, Trophy, Clock } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '@/contexts/AuthContext';
import { handleApiError } from '@/utils/authErrorHandler';

interface UpcomingEvent {
  id: number;
  name: string;
  event_date: string;
  course_name: string;
  scoring_type: string;
  is_active: boolean;
}

interface UpcomingEventsResponse {
  events: UpcomingEvent[];
  total: number;
}

const UpcomingEventsList: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, token } = useAuth();
  const [events, setEvents] = useState<UpcomingEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated && token) {
      loadUpcomingEvents();
    } else {
      setLoading(false);
    }
  }, [isAuthenticated, token]);

  const loadUpcomingEvents = async () => {
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/v1/events/upcoming?limit=10', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        // Check if it's a 401 authentication error
        if (response.status === 401) {
          handleApiError({ response: { status: 401 } });
          return;
        }
        throw new Error('Failed to load upcoming events');
      }

      const data: UpcomingEventsResponse = await response.json();
      setEvents(data.events);
    } catch (error: any) {
      console.error('Error loading upcoming events:', error);
      setError(error.message);
      toast.error('Failed to load upcoming events');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getScoringTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      stroke: 'Stroke Play',
      net_stroke: 'Net Stroke',
      system_36: 'System 36',
      stableford: 'Stableford',
    };
    return labels[type] || type;
  };

  const handleEventClick = (eventId: number) => {
    navigate(`/events/${eventId}`);
  };

  const getDaysUntilEvent = (dateString: string) => {
    const eventDate = new Date(dateString);
    const today = new Date();
    const diffTime = eventDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Tomorrow';
    if (diffDays < 0) return `${Math.abs(diffDays)} days ago`;
    return `${diffDays} days`;
  };

  if (loading) {
    return (
      <Card className="border-0 shadow-lg bg-gradient-to-br from-white to-gray-50/50">
        <CardHeader className="bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 rounded-t-lg">
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 bg-white/60 rounded-lg backdrop-blur-sm">
              <Calendar className="h-5 w-5 text-gray-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Upcoming Events</h2>
              <p className="text-gray-600 text-sm font-normal">Loading events...</p>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-24 bg-gradient-to-r from-gray-200 to-gray-300 rounded-xl"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-0 shadow-lg bg-gradient-to-br from-white to-gray-50/50">
        <CardHeader className="bg-gradient-to-r from-red-600 to-red-700 text-white rounded-t-lg">
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
              <Calendar className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Upcoming Events</h2>
              <p className="text-red-100 text-sm font-normal">Error loading events</p>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="text-center py-8">
            <div className="w-20 h-20 bg-gradient-to-br from-red-500 to-red-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Calendar className="h-10 w-10 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">Failed to load events</h3>
            <p className="text-sm text-gray-600 mb-6">{error}</p>
            <Button 
              onClick={loadUpcomingEvents} 
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-200"
            >
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!isAuthenticated) {
    return (
      <Card className="border-0 shadow-lg bg-gradient-to-br from-white to-gray-50/50">
        <CardHeader className="bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 rounded-t-lg">
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 bg-white/60 rounded-lg backdrop-blur-sm">
              <Calendar className="h-5 w-5 text-gray-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Upcoming Events</h2>
              <p className="text-gray-600 text-sm font-normal">Authentication required</p>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-gradient-to-br from-gray-400 to-gray-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Calendar className="h-10 w-10 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">Please Log In</h3>
            <p className="text-gray-600 mb-6">
              Log in to view upcoming events and manage your tournaments.
            </p>
            <Button 
              onClick={() => navigate('/login')} 
              className="bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700 text-white shadow-lg hover:shadow-xl transition-all duration-200"
            >
              Go to Login
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (events.length === 0 && !loading) {
    return (
      <Card className="border-0 shadow-lg bg-gradient-to-br from-white to-gray-50/50">
        <CardHeader className="bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 rounded-t-lg">
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 bg-white/60 rounded-lg backdrop-blur-sm">
              <Calendar className="h-5 w-5 text-gray-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Upcoming Events</h2>
              <p className="text-gray-600 text-sm font-normal">No events scheduled</p>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-gradient-to-br from-gray-400 to-gray-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
              <Calendar className="h-10 w-10 text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">No Upcoming Events</h3>
            <p className="text-gray-600 mb-6">
              No upcoming events are scheduled. Create a new event to get started with your golf tournament.
            </p>
            <Button 
              onClick={() => navigate('/events')} 
              className="bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700 text-white shadow-lg hover:shadow-xl transition-all duration-200"
            >
              Create Event
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-0 shadow-lg bg-gradient-to-br from-white to-gray-50/50">
      <CardHeader className="bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 rounded-t-lg">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/60 rounded-lg backdrop-blur-sm">
              <Calendar className="h-5 w-5 text-gray-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Upcoming Events</h2>
              <p className="text-gray-600 text-sm font-normal">{events.length} event{events.length !== 1 ? 's' : ''} scheduled</p>
            </div>
          </div>
          <Button
            onClick={loadUpcomingEvents}
            variant="secondary"
            size="sm"
            className="bg-white/60 hover:bg-white/80 text-gray-700 border-gray-300 backdrop-blur-sm"
          >
            <Clock className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="space-y-0">
          {/* Desktop Table View */}
          <div className="hidden md:block">
            <div className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
                      <th className="text-left py-4 px-6 font-semibold text-gray-700 text-sm uppercase tracking-wider">Event Details</th>
                      <th className="text-left py-4 px-6 font-semibold text-gray-700 text-sm uppercase tracking-wider">Date & Time</th>
                      <th className="text-left py-4 px-6 font-semibold text-gray-700 text-sm uppercase tracking-wider">Location</th>
                      <th className="text-left py-4 px-6 font-semibold text-gray-700 text-sm uppercase tracking-wider">Scoring</th>
                      <th className="text-left py-4 px-6 font-semibold text-gray-700 text-sm uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {events.map((event, index) => (
                      <tr
                        key={event.id}
                        className="group hover:bg-gradient-to-r hover:from-gray-50 hover:to-gray-100 cursor-pointer transition-all duration-200 hover:shadow-sm"
                        onClick={() => handleEventClick(event.id)}
                        style={{ animationDelay: `${index * 100}ms` }}
                      >
                        <td className="py-6 px-6">
                          <div className="flex items-start space-x-4">
                            <div className="flex-shrink-0">
                              <div className="w-12 h-12 bg-gradient-to-br from-gray-500 to-gray-600 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-shadow duration-200">
                                <Calendar className="h-6 w-6 text-white" />
                              </div>
                            </div>
                            <div className="flex-1 min-w-0">
                              <h3 className="text-lg font-bold text-gray-900 group-hover:text-gray-700 transition-colors duration-200 truncate">
                                {event.name}
                              </h3>
                              <div className="flex items-center mt-1">
                                <Clock className="h-4 w-4 text-gray-400 mr-1" />
                                <span className="text-sm font-medium text-gray-600">
                                  {getDaysUntilEvent(event.event_date)}
                                </span>
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-6 px-6">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center shadow-md">
                              <Calendar className="h-5 w-5 text-white" />
                            </div>
                            <div>
                              <div className="font-semibold text-gray-900">{formatDate(event.event_date)}</div>
                              <div className="text-sm text-gray-500 font-medium">{formatTime(event.event_date)}</div>
                            </div>
                          </div>
                        </td>
                        <td className="py-6 px-6">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-md">
                              <MapPin className="h-5 w-5 text-white" />
                            </div>
                            <div>
                              <span className="font-semibold text-gray-900">{event.course_name}</span>
                            </div>
                          </div>
                        </td>
                        <td className="py-6 px-6">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center shadow-md">
                              <Trophy className="h-5 w-5 text-white" />
                            </div>
                            <div>
                              <span className="font-semibold text-gray-900">{getScoringTypeLabel(event.scoring_type)}</span>
                            </div>
                          </div>
                        </td>
                        <td className="py-6 px-6">
                          <div className="flex items-center">
                            <span
                              className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-semibold shadow-sm ${
                                event.is_active
                                  ? 'bg-gradient-to-r from-green-100 to-green-200 text-green-800 border border-green-300'
                                  : 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 border border-gray-300'
                              }`}
                            >
                              <div className={`w-2 h-2 rounded-full mr-2 ${
                                event.is_active ? 'bg-green-500' : 'bg-gray-500'
                              }`}></div>
                              {event.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Mobile Card View */}
          <div className="md:hidden space-y-4 p-6">
            {events.map((event, index) => (
              <Card
                key={event.id}
                className="cursor-pointer hover:shadow-xl transition-all duration-300 hover:scale-[1.02] border-0 bg-gradient-to-br from-white to-gray-50/50 shadow-lg"
                onClick={() => handleEventClick(event.id)}
                style={{ animationDelay: `${index * 150}ms` }}
              >
                <CardContent className="p-6">
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-4">
                        <div className="w-14 h-14 bg-gradient-to-br from-gray-500 to-gray-600 rounded-2xl flex items-center justify-center shadow-lg">
                          <Calendar className="h-7 w-7 text-white" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-bold text-gray-900 text-lg leading-tight mb-1">{event.name}</h3>
                          <div className="flex items-center text-sm text-gray-600 font-medium">
                            <Clock className="h-4 w-4 mr-1" />
                            {getDaysUntilEvent(event.event_date)}
                          </div>
                        </div>
                      </div>
                      <span
                        className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold shadow-sm ${
                          event.is_active
                            ? 'bg-gradient-to-r from-green-100 to-green-200 text-green-800 border border-green-300'
                            : 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 border border-gray-300'
                        }`}
                      >
                        <div className={`w-2 h-2 rounded-full mr-2 ${
                          event.is_active ? 'bg-green-500' : 'bg-gray-500'
                        }`}></div>
                        {event.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 gap-4">
                      <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-green-50 to-green-100 rounded-xl">
                        <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center shadow-md">
                          <Calendar className="h-5 w-5 text-white" />
                        </div>
                        <div>
                          <div className="font-semibold text-gray-900">{formatDate(event.event_date)}</div>
                          <div className="text-sm text-gray-600 font-medium">{formatTime(event.event_date)}</div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl">
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-md">
                          <MapPin className="h-5 w-5 text-white" />
                        </div>
                        <div>
                          <span className="font-semibold text-gray-900">{event.course_name}</span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-purple-50 to-purple-100 rounded-xl">
                        <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center shadow-md">
                          <Trophy className="h-5 w-5 text-white" />
                        </div>
                        <div>
                          <span className="font-semibold text-gray-900">{getScoringTypeLabel(event.scoring_type)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default UpcomingEventsList;
