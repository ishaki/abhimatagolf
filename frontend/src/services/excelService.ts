import api from './api';

export interface ExcelExportOptions {
  eventId: number;
  format?: 'excel' | 'csv';
  includeScores?: boolean;
}

export const downloadParticipantsExcel = async (eventId: number): Promise<void> => {
  try {
    const response = await api.get(`/excel/participants/event/${eventId}/export`, {
      responseType: 'blob',
    });
    
    // Create blob URL and trigger download
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `participants_event_${eventId}_${new Date().toISOString().slice(0, 10)}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error downloading participants Excel:', error);
    throw error;
  }
};

export const downloadScorecardsExcel = async (eventId: number): Promise<void> => {
  try {
    const response = await api.get(`/excel/scorecards/event/${eventId}/export`, {
      responseType: 'blob',
    });
    
    // Create blob URL and trigger download
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scorecards_event_${eventId}_${new Date().toISOString().slice(0, 10)}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error downloading scorecards Excel:', error);
    throw error;
  }
};

export const downloadParticipantTemplate = async (): Promise<void> => {
  try {
    const response = await api.get('/excel/template/participants', {
      responseType: 'blob',
    });
    
    // Create blob URL and trigger download
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `participant_upload_template_${new Date().toISOString().slice(0, 10)}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error downloading participant template:', error);
    throw error;
  }
};
