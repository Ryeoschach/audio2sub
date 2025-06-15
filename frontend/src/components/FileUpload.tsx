import React, { useState, useCallback } from 'react';
import axios from 'axios';

interface FileUploadProps {
  onUploadSuccess: (taskId: string, fileId: string, filename: string) => void;
  setNotification: (message: string, type: 'success' | 'error') => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess, setNotification }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleUpload = useCallback(async () => {
    if (!selectedFile) {
      setNotification('Please select a file first.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    setIsUploading(true);
    setNotification('', 'success'); // Clear previous notifications

    try {
      // Using /api prefix which will be proxied by Vite dev server
      const response = await axios.post('/api/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      onUploadSuccess(response.data.task_id, response.data.file_id, selectedFile.name);
      setNotification(`'${selectedFile.name}' uploaded successfully. Transcription started.`, 'success');
      setSelectedFile(null); // Reset file input
    } catch (error) {
      console.error('Error uploading file:', error);
      if (axios.isAxiosError(error) && error.response) {
        setNotification(`Error uploading file: ${error.response.data.detail || error.message}`, 'error');
      } else {
        setNotification('Error uploading file. Please try again.', 'error');
      }
    }
    setIsUploading(false);
  }, [selectedFile, onUploadSuccess, setNotification]);

  return (
    <div className="bg-slate-700 p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-4 text-teal-300">Upload Audio/Video</h2>
      <div className="mb-4">
        <input
          type="file"
          onChange={handleFileChange}
          accept="audio/*,video/*"
          className="block w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-teal-500 file:text-white hover:file:bg-teal-600 disabled:opacity-50"
          disabled={isUploading}
        />
      </div>
      {selectedFile && (
        <p className="text-sm text-slate-400 mb-4">Selected file: {selectedFile.name}</p>
      )}
      <button
        onClick={handleUpload}
        disabled={!selectedFile || isUploading}
        className="w-full bg-gradient-to-r from-blue-500 to-teal-500 hover:from-blue-600 hover:to-teal-600 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isUploading ? 'Uploading...' : 'Upload and Transcribe'}
      </button>
    </div>
  );
};

export default FileUpload;
