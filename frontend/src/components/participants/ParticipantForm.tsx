import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Participant,
  ParticipantCreate,
  ParticipantUpdate,
  createParticipant,
  updateParticipant,
} from '@/services/participantService';
import { eventDivisionService, EventDivision } from '@/services/eventDivisionService';
import { toast } from 'sonner';

interface ParticipantFormProps {
  participant?: Participant;
  eventId?: number;
  onSuccess: () => void;
  onCancel: () => void;
}

const ParticipantForm: React.FC<ParticipantFormProps> = ({
  participant,
  eventId,
  onSuccess,
  onCancel,
}) => {
  const [formData, setFormData] = useState({
    name: '',
    declared_handicap: '0',
    division: '',
    division_id: '',
  });
  const [loading, setLoading] = useState(false);
  const [divisions, setDivisions] = useState<EventDivision[]>([]);
  const [loadingDivisions, setLoadingDivisions] = useState(false);

  useEffect(() => {
    if (participant) {
      setFormData({
        name: participant.name,
        declared_handicap: participant.declared_handicap.toString(),
        division: participant.division || '',
        division_id: participant.division_id?.toString() || '',
      });
    }
  }, [participant]);

  useEffect(() => {
    if (eventId) {
      loadDivisions();
    }
  }, [eventId]);

  const loadDivisions = async () => {
    if (!eventId) return;
    
    try {
      setLoadingDivisions(true);
      const data = await eventDivisionService.getDivisionsForEvent(eventId);
      setDivisions(data);
    } catch (error) {
      console.error('Error loading divisions:', error);
      // Don't show error toast as this is not critical for form functionality
    } finally {
      setLoadingDivisions(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      toast.error('Participant name is required');
      return;
    }

    const handicap = parseFloat(formData.declared_handicap);
    if (isNaN(handicap) || handicap < 0 || handicap > 54) {
      toast.error('Handicap must be between 0 and 54');
      return;
    }

    if (!participant && !eventId) {
      toast.error('Event ID is required for new participants');
      return;
    }

    try {
      setLoading(true);

      if (participant) {
        // Update existing participant
        const updateData: ParticipantUpdate = {
          name: formData.name.trim(),
          declared_handicap: handicap,
          division: formData.division.trim() || undefined,
          division_id: formData.division_id ? parseInt(formData.division_id) : undefined,
        };
        await updateParticipant(participant.id, updateData);
        toast.success('Participant updated successfully');
      } else {
        // Create new participant
        const createData: ParticipantCreate = {
          event_id: eventId!,
          name: formData.name.trim(),
          declared_handicap: handicap,
          division: formData.division.trim() || undefined,
          division_id: formData.division_id ? parseInt(formData.division_id) : undefined,
        };
        await createParticipant(createData);
        toast.success('Participant created successfully');
      }

      onSuccess();
    } catch (error: any) {
      console.error('Error saving participant:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to save participant';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>
            {participant ? 'Edit Participant' : 'Add New Participant'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column - Form Fields */}
              <div className="lg:col-span-2 space-y-6">
                {/* Participant Name */}
                <div>
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Enter participant name"
                    required
                  />
                </div>

                {/* Declared Handicap */}
                <div>
                  <Label htmlFor="declared_handicap">Declared Handicap *</Label>
                  <Input
                    id="declared_handicap"
                    type="number"
                    step="0.1"
                    min="0"
                    max="54"
                    value={formData.declared_handicap}
                    onChange={(e) => handleInputChange('declared_handicap', e.target.value)}
                    placeholder="0"
                    required
                  />
                  <p className="text-xs text-gray-600 mt-1">
                    Enter value between 0 and 54
                  </p>
                </div>

                {/* Division */}
                <div>
                  <Label htmlFor="division">Division</Label>
                  {loadingDivisions ? (
                    <div className="px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500">
                      Loading divisions...
                    </div>
                  ) : (
                    <select
                      id="division"
                      value={formData.division_id}
                      onChange={(e) => {
                        const selectedDivisionId = e.target.value;
                        const selectedDivision = divisions.find(d => d.id.toString() === selectedDivisionId);
                        handleInputChange('division_id', selectedDivisionId);
                        handleInputChange('division', selectedDivision?.name || '');
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">No Division</option>
                      {divisions.map((division) => (
                        <option key={division.id} value={division.id}>
                          {division.name}
                          {division.description && ` - ${division.description}`}
                          {division.handicap_min !== null && division.handicap_max !== null && 
                            ` (${division.handicap_min}-${division.handicap_max})`}
                          {division.handicap_min !== null && division.handicap_max === null && 
                            ` (${division.handicap_min}+)`}
                          {division.handicap_min === null && division.handicap_max !== null && 
                            ` (${division.handicap_max} and below)`}
                        </option>
                      ))}
                    </select>
                  )}
                  <p className="text-xs text-gray-600 mt-1">
                    Optional: Assign participant to a division
                  </p>
                </div>
              </div>

              {/* Right Column - Help & Actions */}
              <div className="lg:col-span-1">
                {/* Form Actions */}
                <div className="mt-6 space-y-3">
                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white"
                  >
                    {loading ? 'Saving...' : participant ? 'Update Participant' : 'Add Participant'}
                  </Button>
                  <Button
                    type="button"
                    onClick={onCancel}
                    variant="outline"
                    className="w-full border-gray-400 text-gray-700 bg-gray-100 hover:bg-gray-200 hover:border-gray-500"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default ParticipantForm;
