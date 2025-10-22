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

// Common countries list for dropdown
const COUNTRIES = [
  "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia", 
  "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
  "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina",
  "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia",
  "Cameroon", "Canada", "Cape Verde", "Central African Republic", "Chad", "Chile", "China",
  "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
  "Denmark", "Djibouti", "Dominica", "Dominican Republic", "East Timor", "Ecuador", "Egypt",
  "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland",
  "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala",
  "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India",
  "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Ivory Coast", "Jamaica", "Japan",
  "Jordan", "Kazakhstan", "Kenya", "Kiribati", "North Korea", "South Korea", "Kosovo", "Kuwait",
  "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein",
  "Lithuania", "Luxembourg", "Macedonia", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali",
  "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova",
  "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru",
  "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Norway", "Oman",
  "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines",
  "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
  "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Saudi Arabia",
  "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
  "Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan",
  "Suriname", "Swaziland", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania",
  "Thailand", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan",
  "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States",
  "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia",
  "Zimbabwe"
];

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
    country: '',
    sex: '',
    phone_no: '',
    event_status: 'Ok',
    event_description: '',
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
        country: participant.country || '',
        sex: participant.sex || '',
        phone_no: participant.phone_no || '',
        event_status: participant.event_status || 'Ok',
        event_description: participant.event_description || '',
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
          country: formData.country.trim() || undefined,
          sex: (formData.sex as 'Male' | 'Female') || undefined,
          phone_no: formData.phone_no.trim() || undefined,
          event_status: (formData.event_status as 'Ok' | 'No Show' | 'Disqualified') || 'Ok',
          event_description: formData.event_description.trim() || undefined,
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
          country: formData.country.trim() || undefined,
          sex: (formData.sex as 'Male' | 'Female') || undefined,
          phone_no: formData.phone_no.trim() || undefined,
          event_status: (formData.event_status as 'Ok' | 'No Show' | 'Disqualified') || 'Ok',
          event_description: formData.event_description.trim() || undefined,
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
    <div className="max-w-7xl mx-auto p-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-4">
          <CardTitle className="text-2xl font-bold">
            {participant ? 'Edit Participant' : 'Add New Participant'}
          </CardTitle>
          {/* Action Buttons - Top Right */}
          <div className="flex gap-3">
            <Button
              type="button"
              onClick={onCancel}
              variant="outline"
              className="border-gray-400 text-gray-700 bg-gray-100 hover:bg-gray-200 hover:border-gray-500"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              form="participant-form"
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-600 text-white"
            >
              {loading ? 'Saving...' : participant ? 'Update Participant' : 'Add Participant'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <form id="participant-form" onSubmit={handleSubmit}>
            {/* Basic Information Section */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-700 mb-4 border-b pb-2">Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Participant Name */}
                <div>
                  <Label htmlFor="name" className="text-sm font-medium">Name *</Label>
                  <Input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Enter participant name"
                    className="mt-1"
                    required
                  />
                </div>

                {/* Declared Handicap */}
                <div>
                  <Label htmlFor="declared_handicap" className="text-sm font-medium">Declared Handicap *</Label>
                  <Input
                    id="declared_handicap"
                    type="number"
                    step="0.1"
                    min="0"
                    max="54"
                    value={formData.declared_handicap}
                    onChange={(e) => handleInputChange('declared_handicap', e.target.value)}
                    placeholder="0 - 54"
                    className="mt-1"
                    required
                  />
                </div>

                {/* Division */}
                <div>
                  <Label htmlFor="division" className="text-sm font-medium">Division</Label>
                  {loadingDivisions ? (
                    <div className="mt-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 text-sm">
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
                      className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">No Division</option>
                      {divisions.map((division) => (
                        <option key={division.id} value={division.id}>
                          {division.name}
                          {division.handicap_min !== null && division.handicap_max !== null && 
                            ` (${division.handicap_min}-${division.handicap_max})`}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>
            </div>

            {/* Personal Information Section */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-700 mb-4 border-b pb-2">Personal Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* Country */}
                <div>
                  <Label htmlFor="country" className="text-sm font-medium">Country</Label>
                  <select
                    id="country"
                    value={formData.country}
                    onChange={(e) => handleInputChange('country', e.target.value)}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select Country</option>
                    {COUNTRIES.map((country) => (
                      <option key={country} value={country}>
                        {country}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Sex */}
                <div>
                  <Label htmlFor="sex" className="text-sm font-medium">Sex</Label>
                  <select
                    id="sex"
                    value={formData.sex}
                    onChange={(e) => handleInputChange('sex', e.target.value)}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select Sex</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                  </select>
                </div>

                {/* Phone Number */}
                <div>
                  <Label htmlFor="phone_no" className="text-sm font-medium">Phone Number</Label>
                  <Input
                    id="phone_no"
                    type="tel"
                    value={formData.phone_no}
                    onChange={(e) => handleInputChange('phone_no', e.target.value)}
                    placeholder="+1234567890"
                    className="mt-1"
                  />
                </div>
              </div>
            </div>

            {/* Event Information Section */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-700 mb-4 border-b pb-2">Event Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Event Status */}
                <div>
                  <Label htmlFor="event_status" className="text-sm font-medium">Event Status</Label>
                  <select
                    id="event_status"
                    value={formData.event_status}
                    onChange={(e) => handleInputChange('event_status', e.target.value)}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="Ok">Ok</option>
                    <option value="No Show">No Show</option>
                    <option value="Disqualified">Disqualified</option>
                  </select>
                </div>

                {/* Event Description */}
                <div className="md:col-span-1">
                  <Label htmlFor="event_description" className="text-sm font-medium">Event Description</Label>
                  <textarea
                    id="event_description"
                    value={formData.event_description}
                    onChange={(e) => handleInputChange('event_description', e.target.value)}
                    placeholder="Additional notes about participant..."
                    rows={3}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  />
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
