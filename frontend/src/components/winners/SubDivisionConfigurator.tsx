/**
 * SubDivisionConfigurator Component
 *
 * Allows event admins to configure handicap ranges for auto-assigned sub-divisions
 * (System 36 Standard & Stableford events only).
 *
 * Features:
 * - Configure Men A/B/C handicap ranges
 * - Optional Ladies A/B configuration
 * - Preview winners grouped by sub-divisions
 * - Save configuration to WinnerConfiguration
 */

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { toast } from 'sonner';
import { Loader2, Save, Settings2, Info, Plus, Trash2, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import {
  updateSubdivisionRanges,
  getSubdivisionRanges,
} from '@/services/winnerConfigurationService';
import { eventDivisionService } from '@/services/eventDivisionService';

interface SubDivisionConfiguratorProps {
  eventId: number;
  scoringType: string;
  onConfigSaved?: () => void;
}

interface SubDivisionRange {
  name: string;
  min: number;
  max: number;
}

interface DivisionConfig {
  enabled: boolean;
  subdivisions: SubDivisionRange[];
}

const SubDivisionConfigurator: React.FC<SubDivisionConfiguratorProps> = ({
  eventId,
  scoringType,
  onConfigSaved,
}) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [infoExpanded, setInfoExpanded] = useState(true);
  const [divisionsExist, setDivisionsExist] = useState(false);
  const [loadingDivisions, setLoadingDivisions] = useState(true);

  // Default configuration
  const [menConfig, setMenConfig] = useState<DivisionConfig>({
    enabled: true,
    subdivisions: [
      { name: 'Men A', min: 0, max: 12 },
      { name: 'Men B', min: 13, max: 20 },
      { name: 'Men C', min: 21, max: 36 },
    ],
  });

  const [ladiesConfig, setLadiesConfig] = useState<DivisionConfig>({
    enabled: false,
    subdivisions: [
      { name: 'Ladies A', min: 0, max: 18 },
      { name: 'Ladies B', min: 19, max: 36 },
    ],
  });

  // Check if event type supports auto-subdivisions
  const supportsAutoSubdivisions =
    scoringType === 'system_36' || scoringType === 'stableford';

  // Check if divisions exist
  useEffect(() => {
    checkDivisionsExist();
  }, [eventId]);

  // Load existing configuration
  useEffect(() => {
    const loadConfig = async () => {
      if (!supportsAutoSubdivisions) {
        setLoading(false);
        return;
      }

      if (!divisionsExist) {
        setLoading(false);
        return;
      }

      await loadConfiguration();
    };

    loadConfig();
  }, [eventId, supportsAutoSubdivisions, divisionsExist]);

  const checkDivisionsExist = async () => {
    try {
      setLoadingDivisions(true);
      const divisions = await eventDivisionService.getDivisionsForEvent(eventId);
      // Check if there are any parent divisions (divisions without parent_division_id)
      const hasParentDivisions = divisions.some(div => !div.parent_division_id);
      setDivisionsExist(hasParentDivisions);
    } catch (error) {
      console.error('Error checking divisions:', error);
      setDivisionsExist(false);
    } finally {
      setLoadingDivisions(false);
    }
  };

  const loadConfiguration = async () => {
    try {
      setLoading(true);
      const ranges = await getSubdivisionRanges(eventId);

      if (ranges) {
        // Parse existing configuration
        if (ranges.Men) {
          const menSubs: SubDivisionRange[] = [];
          Object.entries(ranges.Men).forEach(([name, [min, max]]) => {
            menSubs.push({ name: `Men ${name}`, min, max });
          });
          if (menSubs.length > 0) {
            setMenConfig({ enabled: true, subdivisions: menSubs });
          }
        }

        if (ranges.Ladies) {
          const ladiesSubs: SubDivisionRange[] = [];
          Object.entries(ranges.Ladies).forEach(([name, [min, max]]) => {
            ladiesSubs.push({ name: `Ladies ${name}`, min, max });
          });
          if (ladiesSubs.length > 0) {
            setLadiesConfig({ enabled: true, subdivisions: ladiesSubs });
          }
        }
      }
    } catch (error: any) {
      console.error('Error loading subdivision configuration:', error);
      // Use defaults if no configuration exists
    } finally {
      setLoading(false);
    }
  };

  const validateRanges = (): boolean => {
    // Validate Men subdivisions if enabled
    if (menConfig.enabled) {
      for (let i = 0; i < menConfig.subdivisions.length; i++) {
        const current = menConfig.subdivisions[i];

        if (current.min > current.max) {
          toast.error(`${current.name}: Minimum must be less than or equal to maximum`);
          return false;
        }

        // Check for overlaps with other subdivisions
        for (let j = i + 1; j < menConfig.subdivisions.length; j++) {
          const next = menConfig.subdivisions[j];
          if (
            (current.min <= next.max && current.max >= next.min) ||
            (next.min <= current.max && next.max >= current.min)
          ) {
            toast.error(`Overlapping ranges detected: ${current.name} and ${next.name}`);
            return false;
          }
        }
      }
    }

    // Validate Ladies subdivisions if enabled
    if (ladiesConfig.enabled) {
      for (let i = 0; i < ladiesConfig.subdivisions.length; i++) {
        const current = ladiesConfig.subdivisions[i];

        if (current.min > current.max) {
          toast.error(`${current.name}: Minimum must be less than or equal to maximum`);
          return false;
        }

        // Check for overlaps
        for (let j = i + 1; j < ladiesConfig.subdivisions.length; j++) {
          const next = ladiesConfig.subdivisions[j];
          if (
            (current.min <= next.max && current.max >= next.min) ||
            (next.min <= current.max && next.max >= current.min)
          ) {
            toast.error(`Overlapping ranges detected: ${current.name} and ${next.name}`);
            return false;
          }
        }
      }
    }

    return true;
  };


  const handleSave = async () => {
    if (!validateRanges()) return;

    try {
      setSaving(true);

      // Build subdivision_ranges object
      const ranges: Record<string, Record<string, [number, number]>> = {};

      if (menConfig.enabled && menConfig.subdivisions.length > 0) {
        ranges.Men = {};
        menConfig.subdivisions.forEach((sub) => {
          const key = sub.name.replace('Men ', ''); // Extract A, B, C
          ranges.Men[key] = [sub.min, sub.max];
        });
      }

      if (ladiesConfig.enabled && ladiesConfig.subdivisions.length > 0) {
        ranges.Ladies = {};
        ladiesConfig.subdivisions.forEach((sub) => {
          const key = sub.name.replace('Ladies ', ''); // Extract A, B
          ranges.Ladies[key] = [sub.min, sub.max];
        });
      }

      await updateSubdivisionRanges(eventId, ranges);

      toast.success('Sub-Division Configuration Saved!', {
        description: 'Configuration has been saved. You can now calculate winners to apply these sub-divisions.',
        duration: 5000,
      });

      if (onConfigSaved) {
        onConfigSaved();
      }
    } catch (error: any) {
      console.error('Error saving subdivision configuration:', error);
      const errorMessage =
        error.response?.data?.detail || 'Failed to save subdivision configuration';
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const updateMenSubdivision = (index: number, field: 'min' | 'max', value: number) => {
    const updated = [...menConfig.subdivisions];
    updated[index][field] = value;
    setMenConfig({ ...menConfig, subdivisions: updated });
  };

  const updateLadiesSubdivision = (index: number, field: 'min' | 'max', value: number) => {
    const updated = [...ladiesConfig.subdivisions];
    updated[index][field] = value;
    setLadiesConfig({ ...ladiesConfig, subdivisions: updated });
  };

  const addMenSubdivision = () => {
    const nextLetter = String.fromCharCode(65 + menConfig.subdivisions.length); // A=65, B=66, etc.
    const newSub: SubDivisionRange = {
      name: `Men ${nextLetter}`,
      min: 0,
      max: 36,
    };
    setMenConfig({
      ...menConfig,
      subdivisions: [...menConfig.subdivisions, newSub],
    });
    toast.success(`Added Men ${nextLetter} sub-division`);
  };

  const removeMenSubdivision = (index: number) => {
    if (menConfig.subdivisions.length <= 1) {
      toast.error('Must have at least one sub-division');
      return;
    }

    const updated = menConfig.subdivisions.filter((_, i) => i !== index);
    // Re-letter: A, B, C, D -> A, B, C after removing B
    const relabeled = updated.map((sub, idx) => ({
      ...sub,
      name: `Men ${String.fromCharCode(65 + idx)}`,
    }));

    setMenConfig({ ...menConfig, subdivisions: relabeled });
    toast.success('Sub-division removed');
  };

  const addLadiesSubdivision = () => {
    const nextLetter = String.fromCharCode(65 + ladiesConfig.subdivisions.length);
    const newSub: SubDivisionRange = {
      name: `Ladies ${nextLetter}`,
      min: 0,
      max: 36,
    };
    setLadiesConfig({
      ...ladiesConfig,
      subdivisions: [...ladiesConfig.subdivisions, newSub],
    });
    toast.success(`Added Ladies ${nextLetter} sub-division`);
  };

  const removeLadiesSubdivision = (index: number) => {
    if (ladiesConfig.subdivisions.length <= 1) {
      toast.error('Must have at least one sub-division');
      return;
    }

    const updated = ladiesConfig.subdivisions.filter((_, i) => i !== index);
    // Re-letter
    const relabeled = updated.map((sub, idx) => ({
      ...sub,
      name: `Ladies ${String.fromCharCode(65 + idx)}`,
    }));

    setLadiesConfig({ ...ladiesConfig, subdivisions: relabeled });
    toast.success('Sub-division removed');
  };


  if (!supportsAutoSubdivisions) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-blue-900 mb-1">
              Auto Sub-Divisions Not Available
            </p>
            <p className="text-sm text-blue-700">
              Auto-assigned sub-divisions are only available for System 36 Standard and Stableford scoring types.
              This event uses <strong>{scoringType}</strong> scoring.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (loading || loadingDivisions) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
      </div>
    );
  }

  // Check if divisions exist - show warning if not
  if (!divisionsExist) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg shadow-lg">
              <Settings2 className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-1">
                Configure Sub-Divisions
              </h2>
              <p className="text-gray-600 max-w-3xl">
                Define handicap ranges for auto-assigned sub-divisions. These will be applied when winners are calculated,
                grouping participants by their System 36 handicap.
              </p>
            </div>
          </div>
        </div>

        {/* Warning Message */}
        <Card className="border-2 border-orange-300 bg-orange-50 shadow-lg">
          <CardContent className="p-6">
            <div className="flex items-start space-x-4">
              <AlertCircle className="h-8 w-8 text-orange-600 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-orange-900 mb-2">
                  No Divisions Configured
                </h3>
                <p className="text-orange-800 mb-4">
                  You must configure divisions before setting up sub-divisions. Sub-divisions can only be configured for existing divisions.
                </p>
                <div className="bg-white rounded-lg p-4 border border-orange-200">
                  <p className="text-sm font-medium text-orange-900 mb-2">Next Steps:</p>
                  <ol className="list-decimal list-inside space-y-1 text-sm text-orange-800">
                    <li>Go to the <strong>"Divisions"</strong> tab</li>
                    <li>Create at least one division (e.g., Men, Ladies, Senior, etc.)</li>
                    <li>Return to this tab to configure sub-divisions</li>
                  </ol>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-lg shadow-lg">
            <Settings2 className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-1">
              Configure Sub-Divisions
            </h2>
            <p className="text-gray-600 max-w-3xl">
              Define handicap ranges for auto-assigned sub-divisions. These will be applied when winners are calculated,
              grouping participants by their System 36 handicap.
            </p>
          </div>
        </div>
        <Button
          onClick={handleSave}
          disabled={saving}
          size="lg"
          className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-lg"
        >
          {saving ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 h-5 w-5" />
              Save Configuration
            </>
          )}
        </Button>
      </div>

      {/* Info Banner */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-indigo-500 rounded-lg overflow-hidden">
        <button
          onClick={() => setInfoExpanded(!infoExpanded)}
          className="w-full p-4 flex items-start justify-between space-x-3 hover:bg-indigo-50 transition-colors"
        >
          <Info className="h-5 w-5 text-indigo-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-sm text-indigo-900 text-left">
            <p className="font-semibold">How Auto Sub-Divisions Work</p>
          </div>
          {infoExpanded ? (
            <ChevronUp className="h-5 w-5 text-indigo-600 flex-shrink-0" />
          ) : (
            <ChevronDown className="h-5 w-5 text-indigo-600 flex-shrink-0" />
          )}
        </button>
        {infoExpanded && (
          <div className="px-4 pb-4 text-sm text-indigo-900 pl-12">
            <ul className="space-y-1.5 text-indigo-800">
              <li className="flex items-start">
                <span className="text-indigo-600 mr-2">•</span>
                <span>Participants remain in their base division (e.g., "Men")</span>
              </li>
              <li className="flex items-start">
                <span className="text-indigo-600 mr-2">•</span>
                <span>Sub-divisions are created only for winner display based on calculated handicap</span>
              </li>
              <li className="flex items-start">
                <span className="text-indigo-600 mr-2">•</span>
                <span>Configure ranges below, then calculate winners to see results</span>
              </li>
            </ul>
          </div>
        )}
      </div>

      {/* Men Division Configuration */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="pb-4 bg-gradient-to-r from-blue-50 to-cyan-50 border-b border-cyan-100">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg font-semibold text-cyan-900 flex items-center">
                <div className="w-2 h-2 bg-cyan-600 rounded-full mr-2"></div>
                Men Division Sub-Divisions
              </CardTitle>
              <CardDescription className="text-cyan-700 mt-1">
                Configure handicap ranges for Men sub-divisions (A, B, C, D, etc.)
              </CardDescription>
            </div>
            <Button
              onClick={addMenSubdivision}
              variant="outline"
              size="sm"
              className="border-cyan-500 text-cyan-600 hover:bg-cyan-50"
            >
              <Plus className="h-4 w-4 mr-1" />
              Add Sub-Division
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          {menConfig.subdivisions.map((sub, index) => (
            <div key={index} className="flex items-center gap-4 bg-gray-50 p-3 rounded-lg">
              <div className="w-24">
                <Label className="text-sm font-semibold text-gray-700">{sub.name}</Label>
              </div>
              <div className="flex items-center gap-2">
                <Label htmlFor={`men-${index}-min`} className="text-sm text-gray-600 w-20">
                  Min HCP:
                </Label>
                <Input
                  id={`men-${index}-min`}
                  type="number"
                  min="0"
                  max="36"
                  value={sub.min}
                  onChange={(e) => updateMenSubdivision(index, 'min', parseInt(e.target.value))}
                  className="w-24 border-gray-300 bg-white"
                />
              </div>
              <div className="flex items-center gap-2">
                <Label htmlFor={`men-${index}-max`} className="text-sm text-gray-600 w-20">
                  Max HCP:
                </Label>
                <Input
                  id={`men-${index}-max`}
                  type="number"
                  min="0"
                  max="36"
                  value={sub.max}
                  onChange={(e) => updateMenSubdivision(index, 'max', parseInt(e.target.value))}
                  className="w-24 border-gray-300 bg-white"
                />
              </div>
              <div className="flex-1 text-sm text-gray-500">
                Range: {sub.min} - {sub.max} handicap
              </div>
              {menConfig.subdivisions.length > 1 && (
                <Button
                  onClick={() => removeMenSubdivision(index)}
                  variant="ghost"
                  size="sm"
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Ladies Division Configuration */}
      <Card className="border-0 shadow-lg">
        <CardHeader className="pb-4 bg-gradient-to-r from-pink-50 to-rose-50 border-b border-rose-100">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg font-semibold text-rose-900 flex items-center">
                <div className="w-2 h-2 bg-rose-600 rounded-full mr-2"></div>
                Ladies Division Sub-Divisions
              </CardTitle>
              <CardDescription className="text-rose-700 mt-1">
                Optional: Configure handicap ranges for Ladies sub-divisions (A, B, C, etc.)
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {ladiesConfig.enabled && (
                <Button
                  onClick={addLadiesSubdivision}
                  variant="outline"
                  size="sm"
                  className="border-rose-500 text-rose-600 hover:bg-rose-50"
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Sub-Division
                </Button>
              )}
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={ladiesConfig.enabled}
                  onChange={(e) => setLadiesConfig({ ...ladiesConfig, enabled: e.target.checked })}
                  className="w-4 h-4 text-rose-600 border-gray-300 rounded focus:ring-rose-500"
                />
                <span className="text-sm font-medium text-gray-700">Enable</span>
              </label>
            </div>
          </div>
        </CardHeader>
        {ladiesConfig.enabled && (
          <CardContent className="space-y-4 pt-6">
            {ladiesConfig.subdivisions.map((sub, index) => (
              <div key={index} className="flex items-center gap-4 bg-gray-50 p-3 rounded-lg">
                <div className="w-24">
                  <Label className="text-sm font-semibold text-gray-700">{sub.name}</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Label htmlFor={`ladies-${index}-min`} className="text-sm text-gray-600 w-20">
                    Min HCP:
                  </Label>
                  <Input
                    id={`ladies-${index}-min`}
                    type="number"
                    min="0"
                    max="36"
                    value={sub.min}
                    onChange={(e) => updateLadiesSubdivision(index, 'min', parseInt(e.target.value))}
                    className="w-24 border-gray-300 bg-white"
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Label htmlFor={`ladies-${index}-max`} className="text-sm text-gray-600 w-20">
                    Max HCP:
                  </Label>
                  <Input
                    id={`ladies-${index}-max`}
                    type="number"
                    min="0"
                    max="36"
                    value={sub.max}
                    onChange={(e) => updateLadiesSubdivision(index, 'max', parseInt(e.target.value))}
                    className="w-24 border-gray-300 bg-white"
                  />
                </div>
                <div className="flex-1 text-sm text-gray-500">
                  Range: {sub.min} - {sub.max} handicap
                </div>
                {ladiesConfig.subdivisions.length > 1 && (
                  <Button
                    onClick={() => removeLadiesSubdivision(index)}
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
          </CardContent>
        )}
      </Card>

    </div>
  );
};

export default SubDivisionConfigurator;
