import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { eventDivisionService, EventDivision, EventDivisionCreate } from '@/services/eventDivisionService';
import { getCourseTeeboxes, Teebox } from '@/services/courseService';
import { getEvent } from '@/services/eventService';
import { toast } from 'sonner';
import { useConfirm } from '@/hooks/useConfirm';

interface EventDivisionManagerProps {
  eventId: number;
  onDivisionsChange?: () => void;
}

const EventDivisionManager: React.FC<EventDivisionManagerProps> = ({
  eventId,
  onDivisionsChange,
}) => {
  const { confirm } = useConfirm();
  const [divisions, setDivisions] = useState<EventDivision[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingDivision, setEditingDivision] = useState<EventDivision | null>(null);
  const [teeboxes, setTeeboxes] = useState<Teebox[]>([]);
  const [loadingTeeboxes, setLoadingTeeboxes] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    handicap_min: '',
    handicap_max: '',
    max_participants: '',
    teebox_id: '',
  });

  useEffect(() => {
    loadDivisions();
    loadEventCourseAndTeeboxes();
  }, [eventId]);

  const loadEventCourseAndTeeboxes = async () => {
    try {
      setLoadingTeeboxes(true);
      // Get event to find course_id
      const event = await getEvent(eventId);

      // Load teeboxes for the course
      const teeboxData = await getCourseTeeboxes(event.course_id);
      setTeeboxes(teeboxData);
    } catch (error) {
      console.error('Error loading teeboxes:', error);
      toast.error('Failed to load teeboxes');
    } finally {
      setLoadingTeeboxes(false);
    }
  };

  const loadDivisions = async () => {
    try {
      setLoading(true);
      const data = await eventDivisionService.getDivisionsForEvent(eventId);
      setDivisions(data);
    } catch (error) {
      console.error('Error loading divisions:', error);
      toast.error('Failed to load divisions');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      handicap_min: '',
      handicap_max: '',
      max_participants: '',
      teebox_id: '',
    });
    setEditingDivision(null);
    setShowForm(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error('Division name is required');
      return;
    }

    try {
      const divisionData: EventDivisionCreate = {
        event_id: eventId,
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        handicap_min: formData.handicap_min ? parseFloat(formData.handicap_min) : undefined,
        handicap_max: formData.handicap_max ? parseFloat(formData.handicap_max) : undefined,
        max_participants: formData.max_participants ? parseInt(formData.max_participants) : undefined,
        teebox_id: formData.teebox_id ? parseInt(formData.teebox_id) : undefined,
      };

      if (editingDivision) {
        await eventDivisionService.updateDivision(editingDivision.id, divisionData);
        toast.success('Division updated successfully');
      } else {
        await eventDivisionService.createDivision(divisionData);
        toast.success('Division created successfully');
      }

      resetForm();
      loadDivisions();
      onDivisionsChange?.();
    } catch (error: any) {
      console.error('Error saving division:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to save division';
      toast.error(errorMessage);
    }
  };

  const handleEdit = (division: EventDivision) => {
    setFormData({
      name: division.name,
      description: division.description || '',
      handicap_min: division.handicap_min?.toString() || '',
      handicap_max: division.handicap_max?.toString() || '',
      max_participants: division.max_participants?.toString() || '',
      teebox_id: division.teebox_id?.toString() || '',
    });
    setEditingDivision(division);
    setShowForm(true);
  };

  const handleDelete = async (divisionId: number, divisionName: string) => {
    const confirmed = await confirm({
      title: `Delete Division "${divisionName}"?`,
      description: `Are you sure you want to delete the division "${divisionName}"? This action cannot be undone.`,
      variant: 'danger',
      confirmText: 'Delete',
      cancelText: 'Cancel',
    });

    if (confirmed) {
      try {
        await eventDivisionService.deleteDivision(divisionId);
        toast.success('Division deleted successfully');
        loadDivisions();
        onDivisionsChange?.();
      } catch (error: any) {
        console.error('Error deleting division:', error);
        const errorMessage = error.response?.data?.detail || 'Failed to delete division';
        toast.error(errorMessage);
      }
    }
  };

  const createDefaultDivisions = async () => {
    const defaultDivisions = [
      { name: 'A Flight', description: 'Men Low handicap players', handicap_min: 1, handicap_max: 12 },
      { name: 'B Flight', description: 'Men Higher handicap players', handicap_min: 13, handicap_max: 18 },
      { name: 'C Flight', description: 'Men Highest handicap players', handicap_min: 19, handicap_max: 27 },
      { name: 'Senior Flight', description: 'Senior players'},
      { name: 'Ladies Flight', description: 'Ladies players'},
    ];

    try {
      await eventDivisionService.createDivisionsBulk({
        event_id: eventId,
        divisions: defaultDivisions,
      });
      toast.success('Default divisions created successfully');
      loadDivisions();
      onDivisionsChange?.();
    } catch (error: any) {
      console.error('Error creating default divisions:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to create default divisions';
      toast.error(errorMessage);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading divisions...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Event Divisions</h2>
          <p className="text-sm text-gray-600">Manage divisions for this event</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={createDefaultDivisions}
            variant="outline"
            className="border-green-300 text-green-600 hover:bg-green-50"
          >
            Create Default Divisions
          </Button>
          <Button
            onClick={() => setShowForm(true)}
            className="bg-blue-500 hover:bg-blue-600 text-white"
          >
            Add Division
          </Button>
        </div>
      </div>

      {/* Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>
              {editingDivision ? 'Edit Division' : 'Add New Division'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Division Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="e.g., Championship, Senior, Ladies"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Optional description"
                  />
                </div>
                <div>
                  <Label htmlFor="handicap_min">Min Handicap</Label>
                  <Input
                    id="handicap_min"
                    type="number"
                    step="0.1"
                    min="0"
                    max="54"
                    value={formData.handicap_min}
                    onChange={(e) => handleInputChange('handicap_min', e.target.value)}
                    placeholder="0"
                  />
                </div>
                <div>
                  <Label htmlFor="handicap_max">Max Handicap</Label>
                  <Input
                    id="handicap_max"
                    type="number"
                    step="0.1"
                    min="0"
                    max="54"
                    value={formData.handicap_max}
                    onChange={(e) => handleInputChange('handicap_max', e.target.value)}
                    placeholder="54"
                  />
                </div>
                <div>
                  <Label htmlFor="max_participants">Max Participants</Label>
                  <Input
                    id="max_participants"
                    type="number"
                    min="1"
                    value={formData.max_participants}
                    onChange={(e) => handleInputChange('max_participants', e.target.value)}
                    placeholder="No limit"
                  />
                </div>
                <div>
                  <Label htmlFor="teebox_id">Teebox</Label>
                  <select
                    id="teebox_id"
                    value={formData.teebox_id}
                    onChange={(e) => handleInputChange('teebox_id', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    disabled={loadingTeeboxes || teeboxes.length === 0}
                  >
                    <option value="">No Teebox</option>
                    {teeboxes.map((teebox) => (
                      <option key={teebox.id} value={teebox.id}>
                        {teebox.name} (CR: {teebox.course_rating}, SR: {teebox.slope_rating})
                      </option>
                    ))}
                  </select>
                  {teeboxes.length === 0 && !loadingTeeboxes && (
                    <p className="text-xs text-gray-500 mt-1">No teeboxes available for this course</p>
                  )}
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  type="submit"
                  className="bg-blue-500 hover:bg-blue-600 text-white"
                >
                  {editingDivision ? 'Update Division' : 'Create Division'}
                </Button>
                <Button
                  type="button"
                  onClick={resetForm}
                  variant="outline"
                  className="border-gray-400 text-gray-700 bg-gray-100 hover:bg-gray-200 hover:border-gray-500"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Divisions List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {divisions.map((division) => (
          <Card key={division.id} className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{division.name}</CardTitle>
                  {division.description && (
                    <p className="text-sm text-gray-600 mt-1">{division.description}</p>
                  )}
                </div>
                <div className="flex gap-1">
                  <Button
                    onClick={() => handleEdit(division)}
                    size="sm"
                    variant="outline"
                    className="border-blue-300 text-blue-600 hover:bg-blue-50"
                  >
                    Edit
                  </Button>
                  <Button
                    onClick={() => handleDelete(division.id, division.name)}
                    size="sm"
                    variant="outline"
                    className="border-red-300 text-red-600 hover:bg-red-50"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                {division.handicap_min !== null && division.handicap_max !== null && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Handicap Range:</span>
                    <span className="font-medium">
                      {division.handicap_min} - {division.handicap_max}
                    </span>
                  </div>
                )}
                {division.handicap_min !== null && division.handicap_max === null && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Min Handicap:</span>
                    <span className="font-medium">{division.handicap_min}+</span>
                  </div>
                )}
                {division.handicap_min === null && division.handicap_max !== null && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Max Handicap:</span>
                    <span className="font-medium">{division.handicap_max} and below</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-600">Participants:</span>
                  <span className="font-medium">
                    {division.participant_count || 0}
                    {division.max_participants && ` / ${division.max_participants}`}
                  </span>
                </div>
                {division.teebox && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Teebox:</span>
                    <span className="font-medium">
                      {division.teebox.name} (CR: {division.teebox.course_rating}, SR: {division.teebox.slope_rating})
                    </span>
                  </div>
                )}
                {division.max_participants && (
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{
                        width: `${Math.min(
                          ((division.participant_count || 0) / division.max_participants) * 100,
                          100
                        )}%`,
                      }}
                    ></div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {divisions.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No divisions created</h3>
            <p className="text-gray-600 mb-4">
              Create divisions to organize participants by skill level or category.
            </p>
            <Button
              onClick={() => setShowForm(true)}
              className="bg-blue-500 hover:bg-blue-600 text-white"
            >
              Create First Division
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default EventDivisionManager;
