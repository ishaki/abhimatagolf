import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Download, FileSpreadsheet, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { downloadParticipantsExcel, downloadScorecardsExcel, downloadParticipantTemplate } from '@/services/excelService';

interface ExcelExportProps {
  eventId: number;
  hasParticipants?: boolean;
  hasScorecards?: boolean;
  className?: string;
}

const ExcelExport: React.FC<ExcelExportProps> = ({
  eventId,
  hasParticipants = false,
  hasScorecards = false,
  className = ''
}) => {
  const [isExporting, setIsExporting] = useState<string | null>(null);

  const handleExport = async (type: 'participants' | 'scorecards' | 'template') => {
    setIsExporting(type);
    try {
      switch (type) {
        case 'participants':
          await downloadParticipantsExcel(eventId);
          toast.success('Participants exported successfully!');
          break;
        case 'scorecards':
          await downloadScorecardsExcel(eventId);
          toast.success('Scorecards exported successfully!');
          break;
        case 'template':
          await downloadParticipantTemplate();
          toast.success('Participant template downloaded!');
          break;
      }
    } catch (error) {
      console.error(`Error exporting ${type}:`, error);
      toast.error(`Failed to export ${type}. Please try again.`);
    } finally {
      setIsExporting(null);
    }
  };

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {hasParticipants && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleExport('participants')}
          disabled={isExporting === 'participants'}
          className="flex items-center gap-2"
        >
          {isExporting === 'participants' ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <FileSpreadsheet className="h-4 w-4" />
          )}
          Export Participants
        </Button>
      )}
      
      {hasScorecards && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleExport('scorecards')}
          disabled={isExporting === 'scorecards'}
          className="flex items-center gap-2"
        >
          {isExporting === 'scorecards' ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <FileSpreadsheet className="h-4 w-4" />
          )}
          Export Scorecards
        </Button>
      )}
      
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport('template')}
        disabled={isExporting === 'template'}
        className="flex items-center gap-2"
      >
        {isExporting === 'template' ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Download className="h-4 w-4" />
        )}
        Download Template
      </Button>
    </div>
  );
};

export default ExcelExport;
