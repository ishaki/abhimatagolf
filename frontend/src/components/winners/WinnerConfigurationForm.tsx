import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  winnerConfigurationService,
  WinnerConfigurationUpdate,
  TieBreakingMethod,
  CalculationTrigger,
  getTieBreakingMethodLabel,
  getCalculationTriggerLabel,
} from '@/services/winnerConfigurationService';
import { toast } from 'sonner';
import { Loader2, Save, Info, Settings } from 'lucide-react';

interface WinnerConfigurationFormProps {
  eventId: number;
  onSuccess?: () => void;
}

const WinnerConfigurationForm: React.FC<WinnerConfigurationFormProps> = ({
  eventId,
  onSuccess,
}) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    tie_breaking_method: TieBreakingMethod.STANDARD_GOLF,
    winners_per_division: 3,
    top_overall_count: 3,
    calculation_trigger: CalculationTrigger.MANUAL_ONLY,
    allow_manual_override: true,
    include_best_gross: false,
    include_best_net: false,
    exclude_incomplete_rounds: true,
    minimum_holes_for_ranking: 18,
  });

  useEffect(() => {
    loadConfiguration();
  }, [eventId]);

  const loadConfiguration = async () => {
    try {
      setLoading(true);
      const data = await winnerConfigurationService.getConfig(eventId);
      setFormData({
        tie_breaking_method: data.tie_breaking_method,
        winners_per_division: data.winners_per_division,
        top_overall_count: data.top_overall_count,
        calculation_trigger: data.calculation_trigger,
        allow_manual_override: data.allow_manual_override,
        include_best_gross: data.include_best_gross,
        include_best_net: data.include_best_net,
        exclude_incomplete_rounds: data.exclude_incomplete_rounds,
        minimum_holes_for_ranking: data.minimum_holes_for_ranking,
      });
    } catch (error: any) {
      console.error('Error loading configuration:', error);
      toast.error('Failed to load winner configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (formData.winners_per_division < 1 || formData.winners_per_division > 10) {
      toast.error('Winners per division must be between 1 and 10');
      return;
    }

    if (formData.top_overall_count < 0 || formData.top_overall_count > 10) {
      toast.error('Top overall count must be between 0 and 10 (use 0 for division-based winners only)');
      return;
    }

    if (formData.minimum_holes_for_ranking < 9 || formData.minimum_holes_for_ranking > 18) {
      toast.error('Minimum holes for ranking must be between 9 and 18');
      return;
    }

    try {
      setSaving(true);

      const updateData: WinnerConfigurationUpdate = {
        tie_breaking_method: formData.tie_breaking_method,
        winners_per_division: formData.winners_per_division,
        top_overall_count: formData.top_overall_count,
        calculation_trigger: formData.calculation_trigger,
        allow_manual_override: formData.allow_manual_override,
        include_best_gross: formData.include_best_gross,
        include_best_net: formData.include_best_net,
        exclude_incomplete_rounds: formData.exclude_incomplete_rounds,
        minimum_holes_for_ranking: formData.minimum_holes_for_ranking,
      };

      await winnerConfigurationService.updateConfig(eventId, updateData);
      toast.success('Winner Configuration Saved Successfully!', {
        description: 'Your settings have been saved. You can now recalculate winners from the Winners tab to apply these changes.',
        duration: 5000,
      });

      // Reload configuration
      await loadConfiguration();

      if (onSuccess) {
        onSuccess();
      }
    } catch (error: any) {
      console.error('Error saving configuration:', error);
      const errorMessage =
        error.response?.data?.detail || 'Failed to save winner configuration';
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
      </div>
    );
  }

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="space-y-3 w-full">
      {/* Header with Save Button */}
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-3 mb-3">
        <div className="flex items-start space-x-4">
          <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-lg">
            <Settings className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-1">
              Winner Configuration
            </h2>
            <p className="text-gray-600 max-w-2xl">
              Customize how winners are calculated, including tie-breaking rules, award categories, and eligibility requirements
            </p>
          </div>
        </div>
        <Button
          type="submit"
          disabled={saving}
          size="lg"
          className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 w-full lg:w-auto"
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

      {/* Main Settings Grid - 2 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 w-full">
        {/* Left Column: Core Settings */}
        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
          <CardHeader className="pb-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-indigo-100">
            <CardTitle className="text-lg font-semibold text-indigo-900 flex items-center">
              <div className="w-2 h-2 bg-indigo-600 rounded-full mr-2"></div>
              Core Settings
            </CardTitle>
            <CardDescription className="text-indigo-700">Configure tie-breaking rules and calculation timing</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 pt-3">
            {/* Tie-Breaking Method */}
            <div className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-6">
              <div className="sm:w-1/3 pt-2">
                <Label htmlFor="tie_breaking_method" className="text-sm font-semibold text-gray-700">Tie-Breaking Method</Label>
                <p className="text-xs text-gray-500 mt-1 flex items-start">
                  <Info className="h-3 w-3 mr-1 mt-0.5 flex-shrink-0" />
                  Standard Golf uses back 9, last 6, last 3, last hole
                </p>
              </div>
              <div className="flex-1">
                <Select
                  value={formData.tie_breaking_method}
                  onValueChange={(value) =>
                    handleInputChange('tie_breaking_method', value as TieBreakingMethod)
                  }
                >
                  <SelectTrigger id="tie_breaking_method" className="border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 h-11">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white border-2 border-gray-300 shadow-xl max-w-md">
                    {Object.values(TieBreakingMethod).map((method) => (
                      <SelectItem
                        key={method}
                        value={method}
                        className="py-3 px-4 text-sm font-medium hover:bg-indigo-50 focus:bg-indigo-100 cursor-pointer data-[state=checked]:bg-indigo-50 data-[state=checked]:text-indigo-900"
                      >
                        {getTieBreakingMethodLabel(method)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Calculation Trigger */}
            <div className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-6">
              <div className="sm:w-1/3 pt-2">
                <Label htmlFor="calculation_trigger" className="text-sm font-semibold text-gray-700">Calculation Trigger</Label>
                <p className="text-xs text-gray-500 mt-1 flex items-start">
                  <Info className="h-3 w-3 mr-1 mt-0.5 flex-shrink-0" />
                  When to auto-calculate
                </p>
              </div>
              <div className="flex-1">
                <Select
                  value={formData.calculation_trigger}
                  onValueChange={(value) =>
                    handleInputChange('calculation_trigger', value as CalculationTrigger)
                  }
                >
                  <SelectTrigger id="calculation_trigger" className="border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 h-11">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white border-2 border-gray-300 shadow-xl max-w-md">
                    {Object.values(CalculationTrigger).map((trigger) => (
                      <SelectItem
                        key={trigger}
                        value={trigger}
                        className="py-3 px-4 text-sm font-medium hover:bg-indigo-50 focus:bg-indigo-100 cursor-pointer data-[state=checked]:bg-indigo-50 data-[state=checked]:text-indigo-900"
                      >
                        {getCalculationTriggerLabel(trigger)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Right Column: Winner Counts */}
        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
          <CardHeader className="pb-4 bg-gradient-to-r from-emerald-50 to-teal-50 border-b border-teal-100">
            <CardTitle className="text-lg font-semibold text-teal-900 flex items-center">
              <div className="w-2 h-2 bg-teal-600 rounded-full mr-2"></div>
              Winner Recognition
            </CardTitle>
            <CardDescription className="text-teal-700">Set how many winners to recognize</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 pt-3">
            {/* Top Overall Winners */}
            <div className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-6">
              <div className="sm:w-1/3 pt-2">
                <Label htmlFor="top_overall_count" className="text-sm font-semibold text-gray-700">Top Overall Winners</Label>
                <p className="text-xs text-gray-500 mt-1">Number of overall winners (0-10). Use 0 for division-based winners only</p>
              </div>
              <div className="flex-1">
                <Input
                  id="top_overall_count"
                  type="number"
                  min="0"
                  max="10"
                  value={formData.top_overall_count}
                  onChange={(e) =>
                    handleInputChange('top_overall_count', parseInt(e.target.value))
                  }
                  required
                  className="max-w-xs border-gray-300 focus:border-teal-500 focus:ring-teal-500"
                />
              </div>
            </div>

            {/* Winners Per Division */}
            <div className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-6">
              <div className="sm:w-1/3 pt-2">
                <Label htmlFor="winners_per_division" className="text-sm font-semibold text-gray-700">Winners Per Division</Label>
                <p className="text-xs text-gray-500 mt-1">Winners to recognize per division (1-10)</p>
              </div>
              <div className="flex-1">
                <Input
                  id="winners_per_division"
                  type="number"
                  min="1"
                  max="10"
                  value={formData.winners_per_division}
                  onChange={(e) =>
                    handleInputChange('winners_per_division', parseInt(e.target.value))
                  }
                  required
                  className="max-w-xs border-gray-300 focus:border-teal-500 focus:ring-teal-500"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Secondary Settings Grid - 3 Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 w-full">
        {/* Eligibility Rules */}
        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
          <CardHeader className="pb-4 bg-gradient-to-r from-orange-50 to-amber-50 border-b border-amber-100">
            <CardTitle className="text-lg font-semibold text-amber-900 flex items-center">
              <div className="w-2 h-2 bg-amber-600 rounded-full mr-2"></div>
              Eligibility Rules
            </CardTitle>
            <CardDescription className="text-xs text-amber-700">Participant eligibility criteria</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 pt-3">
            <div className="flex items-start justify-between p-3 bg-amber-50/50 rounded-lg">
              <div className="flex-1">
                <Label className="text-sm font-semibold text-gray-700">
                  Exclude Incomplete Rounds
                </Label>
                <p className="text-xs text-gray-500 mt-1">
                  Require minimum holes to be played
                </p>
              </div>
              <div className="flex gap-4 items-center">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="exclude_incomplete_rounds"
                    checked={formData.exclude_incomplete_rounds === true}
                    onChange={() => handleInputChange('exclude_incomplete_rounds', true)}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">Yes</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="exclude_incomplete_rounds"
                    checked={formData.exclude_incomplete_rounds === false}
                    onChange={() => handleInputChange('exclude_incomplete_rounds', false)}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">No</span>
                </label>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-4">
              <div className="sm:w-2/5 pt-2">
                <Label htmlFor="minimum_holes_for_ranking" className="text-sm font-semibold text-gray-700">
                  Minimum Holes
                </Label>
                <p className="text-xs text-gray-500 mt-1">9-18 holes</p>
              </div>
              <div className="flex-1">
                <Input
                  id="minimum_holes_for_ranking"
                  type="number"
                  min="9"
                  max="18"
                  value={formData.minimum_holes_for_ranking}
                  onChange={(e) =>
                    handleInputChange('minimum_holes_for_ranking', parseInt(e.target.value))
                  }
                  required
                  disabled={!formData.exclude_incomplete_rounds}
                  className="max-w-[120px] border-gray-300 focus:border-amber-500 focus:ring-amber-500"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Special Awards */}
        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
          <CardHeader className="pb-4 bg-gradient-to-r from-rose-50 to-pink-50 border-b border-pink-100">
            <CardTitle className="text-lg font-semibold text-pink-900 flex items-center">
              <div className="w-2 h-2 bg-pink-600 rounded-full mr-2"></div>
              Special Awards
            </CardTitle>
            <CardDescription className="text-xs text-pink-700">Additional award categories</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 pt-3">
            <div className="flex items-start justify-between p-3 bg-pink-50/50 rounded-lg">
              <div className="flex-1">
                <Label className="text-sm font-semibold text-gray-700">
                  Best Gross Score Award
                </Label>
                <p className="text-xs text-gray-500 mt-1">
                  Award for lowest gross score
                </p>
              </div>
              <div className="flex gap-4 items-center">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="include_best_gross"
                    checked={formData.include_best_gross === true}
                    onChange={() => handleInputChange('include_best_gross', true)}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">Yes</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="include_best_gross"
                    checked={formData.include_best_gross === false}
                    onChange={() => handleInputChange('include_best_gross', false)}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">No</span>
                </label>
              </div>
            </div>

            <div className="flex items-start justify-between p-3 bg-pink-50/50 rounded-lg">
              <div className="flex-1">
                <Label className="text-sm font-semibold text-gray-700">
                  Best Net Score Award
                </Label>
                <p className="text-xs text-gray-500 mt-1">
                  Award for lowest net score
                </p>
              </div>
              <div className="flex gap-4 items-center">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="include_best_net"
                    checked={formData.include_best_net === true}
                    onChange={() => handleInputChange('include_best_net', true)}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">Yes</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="include_best_net"
                    checked={formData.include_best_net === false}
                    onChange={() => handleInputChange('include_best_net', false)}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">No</span>
                </label>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Manual Override */}
        <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow duration-300">
          <CardHeader className="pb-4 bg-gradient-to-r from-violet-50 to-purple-50 border-b border-purple-100">
            <CardTitle className="text-lg font-semibold text-purple-900 flex items-center">
              <div className="w-2 h-2 bg-purple-600 rounded-full mr-2"></div>
              Manual Override
            </CardTitle>
            <CardDescription className="text-xs text-purple-700">Admin result editing control</CardDescription>
          </CardHeader>
          <CardContent className="pt-3">
            <div className="flex items-start justify-between p-3 bg-purple-50/50 rounded-lg">
              <div className="flex-1">
                <Label className="text-sm font-semibold text-gray-700">
                  Allow Manual Override
                </Label>
                <p className="text-xs text-gray-500 mt-1">
                  Enable manual editing of ranks and awards
                </p>
              </div>
              <div className="flex gap-4 items-center">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="allow_manual_override"
                    checked={formData.allow_manual_override === true}
                    onChange={() => handleInputChange('allow_manual_override', true)}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">Yes</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="allow_manual_override"
                    checked={formData.allow_manual_override === false}
                    onChange={() => handleInputChange('allow_manual_override', false)}
                    className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-gray-700">No</span>
                </label>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Info Banner */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-indigo-500 rounded-lg p-3 flex items-start space-x-3 shadow-md w-full">
        <div className="p-2 bg-indigo-100 rounded-lg">
          <Info className="h-5 w-5 text-indigo-600 flex-shrink-0" />
        </div>
        <div className="flex-1 text-sm text-indigo-900">
          <p className="font-semibold mb-2">Configuration Notes</p>
          <ul className="space-y-1.5 text-indigo-800">
            <li className="flex items-start">
              <span className="text-indigo-600 mr-2">•</span>
              <span>Changes apply to future winner calculations</span>
            </li>
            <li className="flex items-start">
              <span className="text-indigo-600 mr-2">•</span>
              <span>Existing winner results are not automatically recalculated</span>
            </li>
            <li className="flex items-start">
              <span className="text-indigo-600 mr-2">•</span>
              <span>You can recalculate winners from the Winners tab after saving</span>
            </li>
          </ul>
        </div>
      </div>
    </form>
    </div>
  );
};

export default WinnerConfigurationForm;
