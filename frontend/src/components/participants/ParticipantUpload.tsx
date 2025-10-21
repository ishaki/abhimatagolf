import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { uploadParticipants, ParticipantImportResult } from '@/services/participantService';
import { downloadParticipantTemplate } from '@/services/excelService';
import { toast } from 'sonner';

interface ParticipantUploadProps {
  eventId: number;
  onUploadSuccess: () => void;
  onCancel: () => void;
}

const ParticipantUpload: React.FC<ParticipantUploadProps> = ({ eventId, onUploadSuccess, onCancel }) => {
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<ParticipantImportResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      const fileExt = file.name.split('.').pop()?.toLowerCase();
      if (!['xlsx', 'xls', 'csv'].includes(fileExt || '')) {
        toast.error('Invalid file type. Please upload Excel or CSV file');
        return;
      }
      setSelectedFile(file);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }

    try {
      setUploading(true);
      const result = await uploadParticipants(eventId, selectedFile);
      setUploadResult(result);

      if (result.success) {
        toast.success(`Successfully imported ${result.successful} participants`);
        onUploadSuccess();
      } else {
        toast.warning(`Imported ${result.successful} participants with ${result.failed} errors`);
      }
    } catch (error: any) {
      console.error('Error uploading participants:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to upload participants';
      toast.error(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      await downloadParticipantTemplate();
      toast.success('Excel template downloaded successfully!');
    } catch (error) {
      console.error('Error downloading template:', error);
      toast.error('Failed to download template. Please try again.');
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Upload Participants</CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
            {/* Left Column - Instructions */}
            <div className="lg:col-span-2">
              <div className="bg-blue-50 p-4 rounded-lg h-fit">
                <h3 className="font-semibold text-blue-900 mb-3">File Format Requirements:</h3>
                <ul className="list-disc list-inside text-sm text-blue-800 space-y-2">
                  <li>Excel (.xlsx, .xls) or CSV (.csv) file</li>
                  <li>Required column: <strong>name</strong></li>
                  <li>Optional columns: <strong>declared_handicap</strong>, <strong>division</strong>, <strong>division_id</strong></li>
                  <li>Handicap values must be between 0 and 54</li>
                  <li>Division ID should reference an existing event division</li>
                </ul>
                
                <div className="mt-4 pt-4 border-t border-blue-200">
                  <Button
                    type="button"
                    onClick={handleDownloadTemplate}
                    variant="outline"
                    size="sm"
                    className="w-full border-blue-300 text-blue-600 hover:bg-blue-50"
                  >
                    Download Excel Template
                  </Button>
                </div>
              </div>
            </div>

            {/* Right Column - Upload Area */}
            <div className="lg:col-span-3 space-y-4">
              {/* File Upload */}
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                {!selectedFile ? (
                  <div className="text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                      />
                    </svg>
                    <p className="mt-2 text-sm text-gray-600">
                      Click to upload or drag and drop
                    </p>
                    <p className="text-xs text-gray-500">Excel or CSV file</p>
                    <Button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="mt-4"
                    >
                      Select File
                    </Button>
                  </div>
                ) : (
                  <div className="text-center">
                    <div className="flex items-center justify-center space-x-2 mb-4">
                      <svg
                        className="h-8 w-8 text-green-500"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      <span className="font-medium text-gray-900">{selectedFile.name}</span>
                    </div>
                    <p className="text-sm text-gray-600">
                      Size: {(selectedFile.size / 1024).toFixed(2)} KB
                    </p>
                    <Button
                      type="button"
                      onClick={() => {
                        setSelectedFile(null);
                        setUploadResult(null);
                        if (fileInputRef.current) {
                          fileInputRef.current.value = '';
                        }
                      }}
                      variant="outline"
                      className="mt-4"
                    >
                      Choose Different File
                    </Button>
                  </div>
                )}
              </div>

              {/* Upload Result */}
              {uploadResult && (
                <div className={`p-4 rounded-lg ${uploadResult.success ? 'bg-green-50' : 'bg-yellow-50'}`}>
                  <h3 className={`font-semibold mb-2 ${uploadResult.success ? 'text-green-900' : 'text-yellow-900'}`}>
                    Upload Results
                  </h3>
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Total Rows</p>
                      <p className="text-2xl font-bold">{uploadResult.total_rows}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Successful</p>
                      <p className="text-2xl font-bold text-green-600">{uploadResult.successful}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Failed</p>
                      <p className="text-2xl font-bold text-red-600">{uploadResult.failed}</p>
                    </div>
                  </div>

                  {/* Errors */}
                  {uploadResult.errors.length > 0 && (
                    <div className="mt-4">
                      <h4 className="font-semibold text-red-900 mb-2">Errors:</h4>
                      <div className="max-h-40 overflow-y-auto bg-white rounded p-2">
                        {uploadResult.errors.map((error, idx) => (
                          <div key={idx} className="text-sm text-red-800 mb-1">
                            Row {error.row}: {error.name} - {error.error}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="flex space-x-4">
                <Button
                  type="button"
                  onClick={handleUpload}
                  disabled={!selectedFile || uploading}
                  className="flex-1 bg-blue-500 hover:bg-blue-600 text-white"
                >
                  {uploading ? 'Uploading...' : 'Upload Participants'}
                </Button>
                <Button
                  type="button"
                  onClick={onCancel}
                  variant="outline"
                  className="flex-1 border-gray-400 text-gray-700 bg-gray-100 hover:bg-gray-200 hover:border-gray-500"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ParticipantUpload;
