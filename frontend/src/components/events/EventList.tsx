import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Event, EventFilters, getEvents, deleteEvent } from '@/services/eventService';
import { toast } from 'sonner';
import { usePermissions } from '@/hooks/usePermissions';
import { useConfirm } from '@/hooks/useConfirm';

interface EventListProps {
  onEditEvent: (event: Event) => void;
  onRefresh: () => void;
}

const EventList: React.FC<EventListProps> = ({ onEditEvent, onRefresh }) => {
  const navigate = useNavigate();
  const { canManageParticipants, canManageScores } = usePermissions();
  const { confirm } = useConfirm();
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<EventFilters>({
    page: 1,
    per_page: 10,
    search: '',
    is_active: undefined
  });
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const response = await getEvents(filters);
      setEvents(response.events);
      setTotal(response.total);
      setCurrentPage(response.page);
    } catch (error) {
      console.error('Error loading events:', error);
      toast.error('Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [filters]);

  const handleSearch = (searchTerm: string) => {
    setFilters(prev => ({ ...prev, search: searchTerm, page: 1 }));
  };

  const handleFilterChange = (key: keyof EventFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  const handleDelete = async (eventId: number) => {
    const confirmed = await confirm({
      title: 'Delete Event?',
      description: 'Are you sure you want to delete this event? This action cannot be undone.',
      variant: 'danger',
      confirmText: 'Delete',
      cancelText: 'Cancel',
    });

    if (confirmed) {
      try {
        await deleteEvent(eventId);
        toast.success('Event deleted successfully');
        loadEvents();
        onRefresh();
      } catch (error) {
        console.error('Error deleting event:', error);
        toast.error('Failed to delete event');
      }
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getScoringTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      stroke: 'Stroke Play',
      net_stroke: 'Net Stroke',
      system_36: 'System 36',
      stableford: 'Stableford'
    };
    return labels[type] || type;
  };

  const totalPages = Math.ceil(total / (filters.per_page || 10));

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading events...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Compact Filters */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          {/* Search Input */}
          <div className="flex-1">
            <Input
              placeholder="Search events..."
              value={filters.search || ''}
              onChange={(e) => handleSearch(e.target.value)}
              className="h-9"
            />
          </div>

          {/* Filter Dropdowns */}
          <div className="flex flex-wrap gap-3">
            <select
              className="px-3 py-2 h-10 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-[120px]"
              value={filters.is_active === undefined ? '' : filters.is_active.toString()}
              onChange={(e) => {
                const value = e.target.value === '' ? undefined : e.target.value === 'true';
                handleFilterChange('is_active', value);
              }}
            >
              <option value="">All Status</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>

            <select
              className="px-3 py-2 h-10 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-[120px]"
              value={filters.scoring_type || ''}
              onChange={(e) => handleFilterChange('scoring_type', e.target.value || undefined)}
            >
              <option value="">All Types</option>
              <option value="stroke">Stroke Play</option>
              <option value="net_stroke">Net Stroke</option>
              <option value="system_36">System 36</option>
              <option value="stableford">Stableford</option>
            </select>

            <select
              className="px-3 py-2 h-10 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-[100px]"
              value={filters.per_page || 10}
              onChange={(e) => handleFilterChange('per_page', parseInt(e.target.value))}
            >
              <option value="10">10/page</option>
              <option value="25">25/page</option>
              <option value="50">50/page</option>
            </select>
          </div>
        </div>
      </div>

      {/* Events List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {events.map((event) => (
          <Card
            key={event.id}
            className="hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => navigate(`/events/${event.id}`)}
          >
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{event.name}</CardTitle>
                  <p className="text-sm text-gray-600 mt-1">
                    {event.course_name || 'Unknown Course'}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    event.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {event.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Event Date:</span>
                  <span className="font-medium">{formatDate(event.event_date)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Scoring Type:</span>
                  <span className="font-medium">{getScoringTypeLabel(event.scoring_type)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Participants:</span>
                  <span className="font-medium">{event.participant_count || 0}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Created by:</span>
                  <span className="font-medium">{event.creator_name || 'Unknown'}</span>
                </div>

                <div className="flex space-x-2 pt-4">
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/events/${event.id}`);
                    }}
                    className="flex-1 bg-blue-500 hover:bg-blue-600 text-white"
                    disabled={!canManageParticipants(event.id) && !canManageScores(event.id)}
                  >
                    Manage
                  </Button>
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      onEditEvent(event);
                    }}
                    variant="outline"
                    className="flex-1 border-blue-300 text-blue-600 hover:bg-blue-50"
                  >
                    Edit
                  </Button>
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(event.id);
                    }}
                    variant="outline"
                    className="flex-1 border-red-300 text-red-600 hover:bg-red-50"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {events.length === 0 && !loading && (
        <Card>
          <CardContent className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No events found</h3>
            <p className="text-gray-600">
              {filters.search || filters.is_active !== undefined || filters.scoring_type
                ? 'Try adjusting your filters to see more events.'
                : 'Get started by creating your first event.'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2">
          <Button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            variant="outline"
          >
            Previous
          </Button>
          
          <div className="flex space-x-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const page = i + 1;
              return (
                <Button
                  key={page}
                  onClick={() => handlePageChange(page)}
                  variant={currentPage === page ? "default" : "outline"}
                  className="w-10"
                >
                  {page}
                </Button>
              );
            })}
          </div>
          
          <Button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            variant="outline"
          >
            Next
          </Button>
        </div>
      )}

      {/* Results Summary */}
      <div className="text-center text-sm text-gray-600">
        Showing {events.length} of {total} events
      </div>
    </div>
  );
};

export default EventList;

