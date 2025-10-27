import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { eventDivisionService, EventDivision, EventDivisionCreate, EventDivisionTree } from '@/services/eventDivisionService';
import { getCourseTeeboxes, Teebox } from '@/services/courseService';
import { getEvent } from '@/services/eventService';
import { usePermissions } from '@/hooks/usePermissions';
import { useConfirm } from '@/hooks/useConfirm';
import { toast } from 'sonner';

interface EventDivisionManagerProps {
  eventId: number;
  event?: any; // Add event data for permission checking
  onDivisionsChange?: () => void;
}

const EventDivisionManager: React.FC<EventDivisionManagerProps> = ({
  eventId,
  event,
  onDivisionsChange,
}) => {
  const { canEditEvent } = usePermissions();
  const { confirm } = useConfirm();
  const [divisions, setDivisions] = useState<EventDivision[]>([]);
  const [divisionsTree, setDivisionsTree] = useState<EventDivisionTree[]>([]);
  const [showHierarchical, setShowHierarchical] = useState(true);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingDivision, setEditingDivision] = useState<EventDivision | null>(null);
  const [showSubdivisionForm, setShowSubdivisionForm] = useState(false);
  const [parentDivisionForSubdivision, setParentDivisionForSubdivision] = useState<number | null>(null);
  const [teeboxes, setTeeboxes] = useState<Teebox[]>([]);
  const [loadingTeeboxes, setLoadingTeeboxes] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    division_type: '',
    handicap_min: '',
    handicap_max: '',
    use_course_handicap_for_assignment: false,
    max_participants: '',
    teebox_id: '',
  });
  const [subdivisionFormData, setSubdivisionFormData] = useState({
    name: '',
    handicap_min: '',
    handicap_max: '',
    description: '',
  });

  useEffect(() => {
    loadDivisions();
    loadEventCourseAndTeeboxes();
  }, [eventId]);

  // Auto-set use_course_handicap_for_assignment based on division type and event scoring (HYBRID APPROACH)
  useEffect(() => {
    if (event && formData.division_type === 'men') {
      // Apply smart default for System 36 STANDARD + Men divisions
      const shouldUseCourseHandicap =
        event.scoring_type === 'system_36' &&
        event.system36_variant === 'standard';

      // Only auto-set if user hasn't manually changed it (when opening fresh form)
      if (!editingDivision) {
        setFormData(prev => ({
          ...prev,
          use_course_handicap_for_assignment: shouldUseCourseHandicap
        }));
      }
    } else if (formData.division_type && formData.division_type !== 'men') {
      // Auto-uncheck for non-Men divisions
      setFormData(prev => ({
        ...prev,
        use_course_handicap_for_assignment: false
      }));
    }
  }, [formData.division_type, event, editingDivision]);

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

      // Also load hierarchical tree
      const treeData = await eventDivisionService.getDivisionsTree(eventId);
      setDivisionsTree(treeData);
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

  const handleCheckboxChange = (field: string, checked: boolean) => {
    setFormData(prev => ({ ...prev, [field]: checked }));
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      division_type: '',
      handicap_min: '',
      handicap_max: '',
      use_course_handicap_for_assignment: false,
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
        division_type: formData.division_type || undefined,
        handicap_min: formData.handicap_min !== '' ? parseFloat(formData.handicap_min) : undefined,
        handicap_max: formData.handicap_max !== '' ? parseFloat(formData.handicap_max) : undefined,
        use_course_handicap_for_assignment: formData.use_course_handicap_for_assignment,
        max_participants: formData.max_participants !== '' ? parseInt(formData.max_participants) : undefined,
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
      division_type: division.division_type || '',
      handicap_min: division.handicap_min?.toString() || '',
      handicap_max: division.handicap_max?.toString() || '',
      use_course_handicap_for_assignment: division.use_course_handicap_for_assignment || false,
      max_participants: division.max_participants !== null && division.max_participants !== undefined
        ? division.max_participants.toString()
        : '',
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

  // Sub-division handlers
  const handleAddSubdivision = (parentDivisionId: number) => {
    setParentDivisionForSubdivision(parentDivisionId);
    setSubdivisionFormData({
      name: '',
      handicap_min: '',
      handicap_max: '',
      description: '',
    });
    setShowSubdivisionForm(true);
  };

  const handleSubdivisionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!subdivisionFormData.name.trim() || !parentDivisionForSubdivision) {
      toast.error('Sub-division name is required');
      return;
    }

    try {
      await eventDivisionService.createSubdivision({
        parent_division_id: parentDivisionForSubdivision,
        name: subdivisionFormData.name.trim(),
        handicap_min: subdivisionFormData.handicap_min !== '' ? parseFloat(subdivisionFormData.handicap_min) : undefined,
        handicap_max: subdivisionFormData.handicap_max !== '' ? parseFloat(subdivisionFormData.handicap_max) : undefined,
        description: subdivisionFormData.description.trim() || undefined,
      });

      toast.success('Sub-division created successfully');
      setShowSubdivisionForm(false);
      setParentDivisionForSubdivision(null);
      loadDivisions();
      onDivisionsChange?.();
    } catch (error: any) {
      console.error('Error creating sub-division:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to create sub-division';
      toast.error(errorMessage);
    }
  };

  const handleDeleteSubdivision = async (subdivisionId: number, subdivisionName: string) => {
    const confirmed = await confirm({
      title: `Delete Sub-Division "${subdivisionName}"?`,
      description: `Are you sure you want to delete this sub-division? Participants will be unassigned.`,
      variant: 'danger',
      confirmText: 'Delete',
      cancelText: 'Cancel',
    });

    if (confirmed) {
      try {
        await eventDivisionService.deleteSubdivision(subdivisionId);
        toast.success('Sub-division deleted successfully');
        loadDivisions();
        onDivisionsChange?.();
      } catch (error: any) {
        console.error('Error deleting sub-division:', error);
        const errorMessage = error.response?.data?.detail || 'Failed to delete sub-division';
        toast.error(errorMessage);
      }
    }
  };

  const canCreateSubdivisions = () => {
    if (!event) return false;
    // Can create pre-defined sub-divisions for Net Stroke and System 36 Modified
    return (
      event.scoring_type === 'net_stroke' ||
      (event.scoring_type === 'system_36' && event.system36_variant === 'modified')
    );
  };

  const createDefaultDivisions = async () => {
    const defaultDivisions = [
      { 
        name: 'A Flight', 
        description: 'Men Low handicap players', 
        division_type: 'men',
        handicap_min: 1, 
        handicap_max: 12,
        use_course_handicap_for_assignment: event?.scoring_type === 'system_36' && event?.system36_variant === 'standard'
      },
      { 
        name: 'B Flight', 
        description: 'Men Higher handicap players', 
        division_type: 'men',
        handicap_min: 13, 
        handicap_max: 18,
        use_course_handicap_for_assignment: event?.scoring_type === 'system_36' && event?.system36_variant === 'standard'
      },
      { 
        name: 'C Flight', 
        description: 'Men Highest handicap players', 
        division_type: 'men',
        handicap_min: 19, 
        handicap_max: 27,
        use_course_handicap_for_assignment: event?.scoring_type === 'system_36' && event?.system36_variant === 'standard'
      },
      { 
        name: 'Senior Flight', 
        description: 'Senior players',
        division_type: 'senior'
      },
      { 
        name: 'Ladies Flight', 
        description: 'Ladies players',
        division_type: 'women'
      },
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
          {canEditEvent(eventId, event) && (
            <>
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
            </>
          )}
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
				  <Label htmlFor="division_type" className="text-sm font-semibold">Division Type</Label>
				  <Select value={formData.division_type} onValueChange={(value) => handleInputChange('division_type', value)}>
					<SelectTrigger id="division_type" className="h-11 rounded-lg border-gray-300 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
					  <SelectValue placeholder="Select division type" />
					</SelectTrigger>
					<SelectContent className="bg-white rounded-md shadow-md border border-gray-200">
					  <SelectItem value="men" className="text-sm py-2.5 px-2 cursor-pointer hover:bg-gray-50 focus:bg-gray-50">Men</SelectItem>
					  <SelectItem value="women" className="text-sm py-2.5 px-2 cursor-pointer hover:bg-gray-50 focus:bg-gray-50">Women</SelectItem>
					  <SelectItem value="senior" className="text-sm py-2.5 px-2 cursor-pointer hover:bg-gray-50 focus:bg-gray-50">Senior</SelectItem>
					  <SelectItem value="vip" className="text-sm py-2.5 px-2 cursor-pointer hover:bg-gray-50 focus:bg-gray-50">VIP</SelectItem>
					  <SelectItem value="mixed" className="text-sm py-2.5 px-2 cursor-pointer hover:bg-gray-50 focus:bg-gray-50">Mixed</SelectItem>
					</SelectContent>
				  </Select>
				  <p className="mt-1 text-xs text-gray-500">Select the primary category for this division.</p>
                </div>
                {event?.scoring_type === 'system_36' && formData.division_type === 'men' && (
                  <>
                    <div className="md:col-span-2">
                      <Label className="text-sm font-semibold block mb-3">
                        Handicap Type for Division Assignment
                      </Label>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <label
                          className={`flex items-start gap-3 p-3 border-2 rounded-lg cursor-pointer transition-all ${
                            !formData.use_course_handicap_for_assignment
                              ? 'border-green-500 bg-green-50 hover:bg-green-100'
                              : 'border-gray-300 bg-white hover:border-gray-400 hover:bg-gray-50'
                          }`}
                        >
                          <input
                            type="radio"
                            name="handicap_type"
                            value="declared"
                            checked={!formData.use_course_handicap_for_assignment}
                            onChange={() => handleCheckboxChange('use_course_handicap_for_assignment', false)}
                            className="mt-1 h-4 w-4 text-green-600 border-gray-300 focus:ring-green-500"
                          />
                          <div className="flex-1">
                            <div className={`font-medium ${
                              !formData.use_course_handicap_for_assignment ? 'text-green-700' : 'text-gray-700'
                            }`}>
                              Declared Handicap
                            </div>
                            <div className="text-xs text-gray-600 mt-1">
                              Use participant's declared handicap (default)
                            </div>
                          </div>
                        </label>

                        <label
                          className={`flex items-start gap-3 p-3 border-2 rounded-lg cursor-pointer transition-all ${
                            formData.use_course_handicap_for_assignment
                              ? 'border-orange-500 bg-orange-50 hover:bg-orange-100'
                              : 'border-gray-300 bg-white hover:border-gray-400 hover:bg-gray-50'
                          }`}
                        >
                          <input
                            type="radio"
                            name="handicap_type"
                            value="course"
                            checked={formData.use_course_handicap_for_assignment}
                            onChange={() => handleCheckboxChange('use_course_handicap_for_assignment', true)}
                            className="mt-1 h-4 w-4 text-orange-600 border-gray-300 focus:ring-orange-500"
                          />
                          <div className="flex-1">
                            <div className={`font-medium ${
                              formData.use_course_handicap_for_assignment ? 'text-orange-700' : 'text-gray-700'
                            }`}>
                              Course Handicap
                              {event?.system36_variant === 'standard' && (
                                <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                                  Recommended
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-gray-600 mt-1">
                              Based on course rating/slope (System 36 Standard)
                            </div>
                          </div>
                        </label>
                      </div>
                      {event?.system36_variant !== 'standard' && (
                        <p className="text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded p-2 mt-2">
                          ℹ️ <strong>Note:</strong> System 36 Modified typically uses declared handicap.
                        </p>
                      )}
                    </div>
                  </>
                )}
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
                  <Label htmlFor="max_participants">Max Participants (0 = No limit)</Label>
                  <Input
                    id="max_participants"
                    type="number"
                    min="0"
                    value={formData.max_participants}
                    onChange={(e) => handleInputChange('max_participants', e.target.value)}
                    placeholder="0 for no limit"
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

      {/* Sub-Division Form */}
      {showSubdivisionForm && parentDivisionForSubdivision && (
        <Card>
          <CardHeader>
            <CardTitle>Add Sub-Division</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubdivisionSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="sub_name">Sub-Division Name *</Label>
                  <Input
                    id="sub_name"
                    value={subdivisionFormData.name}
                    onChange={(e) => setSubdivisionFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g., Men A, Ladies B"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="sub_description">Description</Label>
                  <Input
                    id="sub_description"
                    value={subdivisionFormData.description}
                    onChange={(e) => setSubdivisionFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Optional description"
                  />
                </div>
                <div>
                  <Label htmlFor="sub_handicap_min">Min Handicap</Label>
                  <Input
                    id="sub_handicap_min"
                    type="number"
                    step="0.1"
                    value={subdivisionFormData.handicap_min}
                    onChange={(e) => setSubdivisionFormData(prev => ({ ...prev, handicap_min: e.target.value }))}
                    placeholder="0"
                  />
                </div>
                <div>
                  <Label htmlFor="sub_handicap_max">Max Handicap</Label>
                  <Input
                    id="sub_handicap_max"
                    type="number"
                    step="0.1"
                    value={subdivisionFormData.handicap_max}
                    onChange={(e) => setSubdivisionFormData(prev => ({ ...prev, handicap_max: e.target.value }))}
                    placeholder="36"
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <Button type="submit" className="bg-blue-500 hover:bg-blue-600 text-white">
                  Create Sub-Division
                </Button>
                <Button
                  type="button"
                  onClick={() => {
                    setShowSubdivisionForm(false);
                    setParentDivisionForSubdivision(null);
                  }}
                  variant="outline"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Divisions List - Hidden when form is shown */}
      {!showForm && (
      <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {showHierarchical && divisionsTree.length > 0 ? (
          // Hierarchical view
          divisionsTree.map((division) => (
            <div key={division.id} className="space-y-2">
              <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{division.name}</CardTitle>
                  {division.description && (
                    <p className="text-sm text-gray-600 mt-1">{division.description}</p>
                  )}
                </div>
                <div className="flex gap-1">
                  {canEditEvent(eventId, event) && (
                    <>
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
                    </>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                {division.division_type && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Type:</span>
                    <span className="font-medium capitalize">{division.division_type}</span>
                  </div>
                )}
                {division.is_auto_assigned && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Type:</span>
                    <span className="font-medium text-purple-600">Auto-Assigned</span>
                  </div>
                )}
                {division.use_course_handicap_for_assignment && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Assignment:</span>
                    <span className="font-medium text-orange-600">Course Handicap</span>
                  </div>
                )}
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
                    {division.max_participants && division.max_participants > 0
                      ? ` / ${division.max_participants}`
                      : ' / Unlimited'}
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
                {division.max_participants && division.max_participants > 0 && (
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

                {/* Add Sub-Division Button for parent divisions */}
                {canEditEvent(eventId, event) && canCreateSubdivisions() && !division.parent_division_id && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <Button
                      onClick={() => handleAddSubdivision(division.id)}
                      size="sm"
                      variant="outline"
                      className="w-full border-green-300 text-green-600 hover:bg-green-50"
                    >
                      + Add Sub-Division
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

              {/* Render Sub-Divisions */}
              {showHierarchical && division.sub_divisions && division.sub_divisions.length > 0 && (
                <div className="ml-6 space-y-2">
                  {division.sub_divisions.map((subdiv) => (
                    <Card key={subdiv.id} className="border-l-4 border-blue-400 bg-blue-50/30">
                      <CardHeader className="pb-2">
                        <div className="flex justify-between items-start">
                          <div>
                            <CardTitle className="text-md">{subdiv.name}</CardTitle>
                            {subdiv.description && (
                              <p className="text-xs text-gray-600">{subdiv.description}</p>
                            )}
                          </div>
                          {canEditEvent(eventId, event) && !subdiv.is_auto_assigned && (
                            <Button
                              onClick={() => handleDeleteSubdivision(subdiv.id, subdiv.name)}
                              size="sm"
                              variant="outline"
                              className="border-red-300 text-red-600 hover:bg-red-50"
                            >
                              Delete
                            </Button>
                          )}
                        </div>
                      </CardHeader>
                      <CardContent className="pt-2">
                        <div className="space-y-1 text-xs">
                          {subdiv.is_auto_assigned && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Type:</span>
                              <span className="font-medium text-purple-600">Auto-Assigned</span>
                            </div>
                          )}
                          {subdiv.handicap_min !== null && subdiv.handicap_max !== null && (
                            <div className="flex justify-between">
                              <span className="text-gray-600">Handicap Range:</span>
                              <span className="font-medium">{subdiv.handicap_min} - {subdiv.handicap_max}</span>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          ))
        ) : (
          // Flat view fallback
          divisions.map((division) => (
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
                  {canEditEvent(eventId, event) && (
                    <>
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
                    </>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                {division.division_type && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Type:</span>
                    <span className="font-medium capitalize">{division.division_type}</span>
                  </div>
                )}
                {division.participant_count !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Participants:</span>
                    <span className="font-medium">{division.participant_count}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))
        )}
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
            {canEditEvent(eventId, event) && (
              <Button
                onClick={() => setShowForm(true)}
                className="bg-blue-500 hover:bg-blue-600 text-white"
              >
                Create First Division
              </Button>
            )}
          </CardContent>
        </Card>
      )}
      </>
      )}
    </div>
  );
};

export default EventDivisionManager;
