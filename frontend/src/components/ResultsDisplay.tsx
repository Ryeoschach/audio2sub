import React from 'react';

interface ResultFile {
  file_id: string;
  original_filename: string;
  srt_path: string;
  vtt_path: string;
}

interface ResultsDisplayProps {
  completedTasksData: ResultFile[];
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ completedTasksData }) => {
  if (completedTasksData.length === 0) {
    return (
      <div className="bg-slate-700 p-6 rounded-lg shadow-md text-center">
        <p className="text-slate-300">No transcription results yet. Completed tasks will appear here.</p>
      </div>
    );
  }

  const handleDownload = (fileId: string, filePath: string) => {
    // Use /api prefix for Vite proxy
    window.open(`/api/results/${fileId}/${filePath}`, '_blank');
  };

  return (
    <div className="bg-slate-700 p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-6 text-teal-300">Download Subtitles</h2>
      <div className="space-y-4">
        {completedTasksData.map((taskResult) => (
          <div key={taskResult.file_id} className="p-4 bg-slate-600 rounded-md shadow">
            <h3 className="text-lg font-medium text-slate-100 truncate" title={taskResult.original_filename}>{taskResult.original_filename}</h3>
            <div className="mt-3 flex space-x-3">
              <button
                onClick={() => handleDownload(taskResult.file_id, taskResult.srt_path)}
                className="flex-1 bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-150 ease-in-out text-sm"
              >
                Download .srt
              </button>
              <button
                onClick={() => handleDownload(taskResult.file_id, taskResult.vtt_path)}
                className="flex-1 bg-orange-500 hover:bg-orange-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-150 ease-in-out text-sm"
              >
                Download .vtt
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ResultsDisplay;
