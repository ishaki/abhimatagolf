import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Event, createEvent, updateEvent } from '@/services/eventService';
import { Course, getCourses } from '@/services/courseService';
import { toast } from 'sonner';

interface EventFormProps {
  event?: Event;
  onSuccess: () => void;
  onCancel: () => void;
}

const EventForm: React.FC<EventFormProps> = ({ event, onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    event_date: '',
    course_id: '',
    scoring_type: 'stroke' as 'stroke' | 'net_stroke' | 'system_36' | 'stableford',
    system36_variant: 'standard' as 'standard' | 'modified',
    is_active: true
  });
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingCourses, setLoadingCourses] = useState(true);

  useEffect(() => {
    loadCourses();
    if (event) {
      setFormData({
        name: event.name,
        description: event.description || '',
        event_date: event.event_date,
        course_id: event.course_id.toString(),
        scoring_type: event.scoring_type,
        system36_variant: event.system36_variant || 'standard',
        is_active: event.is_active
      });
    }
  }, [event]);

  const loadCourses = async () => {
    try {
      setLoadingCourses(true);
      const response = await getCourses(1, 100);
      setCourses(response.courses);
    } catch (error) {
      console.error('Error loading courses:', error);
      toast.error('Failed to load courses');
    } finally {
      setLoadingCourses(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error('Event name is required');
      return;
    }
    
    if (!formData.event_date) {
      toast.error('Event date is required');
      return;
    }
    
    if (!formData.course_id) {
      toast.error('Course selection is required');
      return;
    }

    try {
      setLoading(true);
      
      const eventData = {
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        event_date: formData.event_date,
        course_id: parseInt(formData.course_id),
        scoring_type: formData.scoring_type,
        system36_variant: formData.scoring_type === 'system_36' ? formData.system36_variant : undefined,
        is_active: formData.is_active
      };

      if (event) {
        await updateEvent(event.id, eventData);
        toast.success('Event updated successfully');
      } else {
        await createEvent(eventData);
        toast.success('Event created successfully');
      }
      
      onSuccess();
    } catch (error: any) {
      console.error('Error saving event:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to save event';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const scoringTypes = [
    { value: 'stroke', label: 'Stroke Play' },
    { value: 'net_stroke', label: 'Net Stroke' },
    { value: 'system_36', label: 'System 36' },
    { value: 'stableford', label: 'Stableford' }
  ];

  return (
    <div className="max-w-4xl mx-auto">
      <Card className="min-h-fit">
        <CardHeader className="border-b">
          <CardTitle>
            {event ? 'Edit Event' : 'Create New Event'}
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column */}
              <div className="space-y-6">
                {/* Event Name */}
                <div>
                  <Label htmlFor="name">Event Name *</Label>
                  <Input
                    id="name"
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Enter event name"
                    required
                  />
                </div>

                {/* Event Date */}
                <div>
                  <Label htmlFor="event_date">Event Date *</Label>
                  <Input
                    id="event_date"
                    type="date"
                    value={formData.event_date}
                    onChange={(e) => handleInputChange('event_date', e.target.value)}
                    required
                  />
                </div>

                {/* Course Selection */}
                <div>
                  <Label htmlFor="course_id">Golf Course *</Label>
                  {loadingCourses ? (
                    <div className="text-sm text-gray-600">Loading courses...</div>
                  ) : (
                    <select
                      id="course_id"
                      value={formData.course_id}
                      onChange={(e) => handleInputChange('course_id', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    >
                      <option value="">Select a course</option>
                      {courses.map((course) => (
                        <option key={course.id} value={course.id}>
                          {course.name} ({course.location})
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {/* Scoring Type */}
                <div>
                  <Label htmlFor="scoring_type">Scoring Type *</Label>
                  <select
                    id="scoring_type"
                    value={formData.scoring_type}
                    onChange={(e) => handleInputChange('scoring_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    {scoringTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* System 36 Variant - Only show for System 36 */}
                {formData.scoring_type === 'system_36' && (
                  <div>
                    <Label htmlFor="system36_variant">System 36 Variant *</Label>
                    <select
                      id="system36_variant"
                      value={formData.system36_variant}
                      onChange={(e) => handleInputChange('system36_variant', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      required
                    >
                      <option value="standard">Standard (Course Handicap for Men)</option>
                      <option value="modified">Modified (Declared Handicap for Men)</option>
                    </select>
                    <p className="text-sm text-gray-600 mt-1">
                      Standard: Men divisions assigned by course handicap after teebox assignment.<br/>
                      Modified: Men divisions assigned by declared handicap at the beginning.
                    </p>
                  </div>
                )}
              </div>

              {/* Right Column */}
              <div className="space-y-6">
                {/* Event Description */}
                <div>
                  <Label htmlFor="description">Event Description</Label>
                  <textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    placeholder="Enter event description (optional)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 h-48 resize-none"
                  />
                  <p className="text-xs text-gray-600 mt-1">
                    Optional: Provide details about the event, format, prizes, etc.
                  </p>
                </div>

                {/* Active Status */}
                <div className="flex items-center space-x-2">
                  <input
                    id="is_active"
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => handleInputChange('is_active', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <Label htmlFor="is_active">Event is active</Label>
                </div>
              </div>
            </div>

            {/* Form Actions */}
            <div className="pt-6 border-t mt-8">
              <div className="flex space-x-4">
                <Button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-500 hover:bg-blue-600 text-white py-3"
                >
                  {loading ? 'Saving...' : (event ? 'Update Event' : 'Create Event')}
                </Button>
                <Button
                  type="button"
                  onClick={onCancel}
                  variant="outline"
                  className="flex-1 py-3 border-gray-400 text-gray-700 bg-gray-100 hover:bg-gray-200 hover:border-gray-500"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default EventForm;

