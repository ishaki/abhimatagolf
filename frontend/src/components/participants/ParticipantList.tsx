import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import {
  Participant,
  ParticipantFilters,
  getParticipants,
  deleteParticipant,
} from '@/services/participantService';
import { eventDivisionService, EventDivision } from '@/services/eventDivisionService';
import { toast } from 'sonner';
import { usePermissions } from '@/hooks/usePermissions';
import { useConfirm } from '@/hooks/useConfirm';
import { getCountryFlag } from '@/utils/countryUtils';

interface ParticipantListProps {
  eventId?: number;
  event?: any; // Add event data for permission checking
  onEditParticipant: (participant: Participant) => void;
  onRefresh: () => void;
}

const ParticipantList: React.FC<ParticipantListProps> = ({
  eventId,
  event,
  onEditParticipant,
  onRefresh,
}) => {
  const { canManageParticipants } = usePermissions();
  const { confirm } = useConfirm();
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<ParticipantFilters>({
    page: 1,
    per_page: 20,
    search: '',
    event_id: eventId,
  });
  const [searchTerm, setSearchTerm] = useState(filters.search || '');
  const [isSearching, setIsSearching] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [divisions, setDivisions] = useState<EventDivision[]>([]);
  const [loadingDivisions, setLoadingDivisions] = useState(false);
  const [assigningSubdivisions, setAssigningSubdivisions] = useState(false);

  // Initialize search term from filters
  useEffect(() => {
    setSearchTerm(filters.search || '');
  }, []);

  // Load divisions when eventId changes
  useEffect(() => {
    if (eventId) {
      loadDivisions();
    } else {
      setDivisions([]);
    }
  }, [eventId]);

  const loadDivisions = async () => {
    if (!eventId) return;

    try {
      setLoadingDivisions(true);
      const eventDivisions = await eventDivisionService.getDivisionsForEvent(eventId);
      setDivisions(eventDivisions);
    } catch (error) {
      console.error('Error loading divisions:', error);
      toast.error('Failed to load divisions');
    } finally {
      setLoadingDivisions(false);
    }
  };

  const handleAutoAssignSubdivisions = async () => {
    if (!eventId) return;

    try {
      setAssigningSubdivisions(true);
      const result = await eventDivisionService.autoAssignSubdivisions(eventId);

      toast.success(
        `Auto-assigned ${result.assigned} participants to sub-divisions. ${result.skipped} skipped.`
      );

      if (result.errors.length > 0) {
        console.warn('Assignment errors:', result.errors);
      }

      // Reload participants and divisions
      loadParticipants();
      loadDivisions();
      onRefresh();
    } catch (error: any) {
      console.error('Error auto-assigning sub-divisions:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to auto-assign participants';
      toast.error(errorMessage);
    } finally {
      setAssigningSubdivisions(false);
    }
  };

  const canAutoAssignSubdivisions = () => {
    if (!event) return false;
    // Can auto-assign for Net Stroke and System 36 Modified
    return (
      event.scoring_type === 'net_stroke' ||
      (event.scoring_type === 'system_36' && event.system36_variant === 'modified')
    );
  };

  const loadParticipants = async () => {
    try {
      setLoading(true);
      const response = await getParticipants(filters);
      setParticipants(response.participants);
      setTotal(response.total);
      setCurrentPage(response.page);
    } catch (error) {
      console.error('Error loading participants:', error);
      toast.error('Failed to load participants');
    } finally {
      setLoading(false);
    }
  };

  // Debounced search effect
  useEffect(() => {
    if (searchTerm !== filters.search) {
      setIsSearching(true);
    }
    
    const timeoutId = setTimeout(() => {
      setFilters((prev) => ({ ...prev, search: searchTerm, page: 1 }));
      setIsSearching(false);
    }, 300); // 300ms delay

    return () => clearTimeout(timeoutId);
  }, [searchTerm, filters.search]);

  // Load participants when filters change (excluding search term)
  useEffect(() => {
    loadParticipants();
  }, [filters.page, filters.per_page, filters.event_id, filters.search, filters.division]);

  const handleSearch = (value: string) => {
    setSearchTerm(value);
  };

  const handleFilterChange = (key: keyof ParticipantFilters, value: any) => {
    // Handle special case for empty division filter
    if (key === 'division' && value === '__empty__') {
      setFilters((prev) => ({ ...prev, [key]: '__empty__', page: 1 }));
    } else {
      setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
    }
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handleDelete = async (participantId: number, participantName: string) => {
    const confirmed = await confirm({
      title: `Delete ${participantName}?`,
      description: `Are you sure you want to delete ${participantName}? This will also delete all their scores.`,
      variant: 'danger',
      confirmText: 'Delete',
      cancelText: 'Cancel',
    });

    if (confirmed) {
      try {
        await deleteParticipant(participantId);
        toast.success('Participant deleted successfully');
        loadParticipants();
        onRefresh();
      } catch (error) {
        console.error('Error deleting participant:', error);
        toast.error('Failed to delete participant');
      }
    }
  };

  const totalPages = Math.ceil(total / (filters.per_page || 20));

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading participants...</p>
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
          <div className="flex-1 relative">
            <Input
              placeholder="Search participants..."
              value={searchTerm}
              onChange={(e) => handleSearch(e.target.value)}
              className="h-9 pr-8"
            />
            {isSearching && (
              <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              </div>
            )}
          </div>

          {/* Filter Dropdowns */}
          <div className="flex flex-wrap gap-3">
            {/* Division Filter */}
            <select
              className="px-3 py-2 h-10 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-[120px]"
              value={filters.division || ''}
              onChange={(e) =>
                handleFilterChange('division', e.target.value || undefined)
              }
              disabled={loadingDivisions}
            >
              <option value="">All Divisions</option>
              <option value="__empty__">NONE</option>
              {divisions.map((division) => (
                <option key={division.id} value={division.name}>
                  {division.name}
                </option>
              ))}
            </select>

            {/* Records per page */}
            <select
              className="px-3 py-2 h-10 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-w-[100px]"
              value={filters.per_page || 20}
              onChange={(e) =>
                handleFilterChange('per_page', parseInt(e.target.value))
              }
            >
              <option value="20">20/page</option>
              <option value="50">50/page</option>
              <option value="100">100/page</option>
            </select>

            {/* Auto-Assign Sub-Divisions Button */}
            {canAutoAssignSubdivisions() && canManageParticipants(eventId, event) && (
              <Button
                onClick={handleAutoAssignSubdivisions}
                disabled={assigningSubdivisions}
                className="bg-purple-500 hover:bg-purple-600 text-white h-10"
                size="sm"
              >
                {assigningSubdivisions ? 'Assigning...' : 'Auto-Assign Sub-Divisions'}
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Participants Table */}
      <Card className="shadow-sm border-0 overflow-hidden">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px]">
              <thead className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Name
                  </th>
                  {!eventId && (
                    <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                      Event
                    </th>
                  )}
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Handicap
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Division
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Country
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Sex
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Event Status
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Event Description
                  </th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Scorecards
                  </th>
                  <th className="px-6 py-4 text-right text-sm font-semibold text-gray-700 uppercase tracking-wide">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {participants.map((participant) => (
                  <tr key={participant.id} className="hover:bg-gray-50 transition-colors duration-150">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {participant.name}
                          </div>
                        </div>
                      </div>
                    </td>
                    {!eventId && (
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {participant.event_name || `Event #${participant.event_id}`}
                      </td>
                    )}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {participant.declared_handicap.toFixed(0)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {participant.division ? (
                        <div className="flex flex-col">
                          <span className="text-gray-900 font-medium">{participant.division}</span>
                          {participant.division_id && divisions.find(d => d.id === participant.division_id)?.parent_division_id && (
                            <span className="text-xs text-blue-600">Sub-Division</span>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {participant.country ? (
                        <div className="flex items-center space-x-2">
                          {(() => {
                            const flagEmoji = getCountryFlag(participant.country);
                            return flagEmoji ? (
                              <span className="text-lg" title={participant.country}>
                                {flagEmoji}
                              </span>
                            ) : (
                              <div className="w-5 h-3.5 bg-gray-200 rounded-sm flex items-center justify-center">
                                <span className="text-xs text-gray-500">?</span>
                              </div>
                            );
                          })()}
                          <span>{participant.country}</span>
                        </div>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {participant.sex || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                        participant.event_status === 'Ok' ? 'bg-green-100 text-green-800' :
                        participant.event_status === 'No Show' ? 'bg-yellow-100 text-yellow-800' :
                        participant.event_status === 'Disqualified' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {participant.event_status || 'Ok'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title={participant.event_description || ''}>
                      {participant.event_description || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {participant.scorecard_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {canManageParticipants(eventId, event) && (
                        <div className="flex items-center justify-end space-x-2">
                          <Button
                            onClick={() => onEditParticipant(participant)}
                            size="sm"
                            variant="outline"
                            className="text-xs px-3 py-1 h-7 border-gray-300 text-gray-700 hover:bg-gray-50"
                          >
                            Edit
                          </Button>
                          <Button
                            onClick={() =>
                              handleDelete(participant.id, participant.name)
                            }
                            size="sm"
                            variant="outline"
                            className="text-xs px-3 py-1 h-7 border-red-300 text-red-600 hover:bg-red-50"
                          >
                            Delete
                          </Button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Empty State */}
          {participants.length === 0 && !loading && (
            <div className="text-center py-16 bg-gray-50/50">
              <svg
                className="mx-auto h-16 w-16 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                No participants found
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                {filters.search
                  ? 'Try adjusting your search filters.'
                  : 'Get started by adding participants.'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

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
                  variant={currentPage === page ? 'default' : 'outline'}
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
        Showing {participants.length} of {total} participants
      </div>
    </div>
  );
};

export default ParticipantList;
