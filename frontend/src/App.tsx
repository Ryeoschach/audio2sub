import { useState, useCallback } from 'react';
import FileUpload from './components/FileUpload';
import TranscriptionStatus from './components/TranscriptionStatus';
import ResultsDisplay from './components/ResultsDisplay';

// Define types for tasks and results
interface TranscriptionTask {
  taskId: string;
  fileId: string;
  filename: string;
  status: string; // e.g., PENDING, PROGRESS, SUCCESS, FAILURE
  progressMessage?: string;
  result?: TaskResultData; 
  error?: string;
}

interface TaskResultData {
  message: string;
  original_filename: string;
  file_id: string;
  srt_path: string; // Filename of the srt, e.g., "myvideo.srt"
  vtt_path: string; // Filename of the vtt, e.g., "myvideo.vtt"
}

interface Notification {
  message: string;
  type: 'success' | 'error' | '';
}

function App() {
  const [activeTasks, setActiveTasks] = useState<TranscriptionTask[]>([]);
  const [completedTaskResults, setCompletedTaskResults] = useState<TaskResultData[]>([]);
  const [notification, setNotification] = useState<Notification>({ message: '', type: '' });

  const handleSetNotification = useCallback((message: string, type: 'success' | 'error') => {
    setNotification({ message, type });
    // Auto-hide notification after 5 seconds
    setTimeout(() => setNotification({ message: '', type: '' }), 5000);
  }, []);

  const handleUploadSuccess = useCallback((taskId: string, fileId: string, filename: string) => {
    setActiveTasks(prevTasks => [
      ...prevTasks,
      { taskId, fileId, filename, status: 'PENDING', progressMessage: 'Waiting for worker...' },
    ]);
  }, []);

  const handleTaskCompletion = useCallback((completedTask: TranscriptionTask) => {
    setActiveTasks(prevTasks => prevTasks.filter(task => task.taskId !== completedTask.taskId));
    if (completedTask.status === 'SUCCESS' && completedTask.result) {
      setCompletedTaskResults(prevResults => [
        ...prevResults,
        completedTask.result as TaskResultData // Cast here, ensure backend sends this structure
      ]);
    }
    // Notification for completion/failure is handled within TranscriptionStatus component
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-700 text-white p-4 flex flex-col items-center font-sans">
      <header className="w-full max-w-4xl py-8">
        <h1 className="text-5xl font-bold text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-teal-300 to-green-300">
          Audio2Sub
        </h1>
        <p className="text-center text-slate-300 mt-2 text-lg">
          Upload your audio or video files and get subtitles in minutes.
        </p>
      </header>

      {notification.message && (
        <div 
          className={`w-full max-w-4xl p-4 mb-6 rounded-md text-center font-medium 
            ${notification.type === 'success' ? 'bg-green-500 text-white' : ''}
            ${notification.type === 'error' ? 'bg-red-500 text-white' : ''}
          `}
        >
          {notification.message}
        </div>
      )}

      <main className="w-full max-w-4xl bg-slate-800 shadow-2xl rounded-lg p-6 md:p-10 mt-2">
        <FileUpload onUploadSuccess={handleUploadSuccess} setNotification={handleSetNotification} />

        {activeTasks.length > 0 && (
          <div className="my-8">
            <TranscriptionStatus tasks={activeTasks} onTaskCompletion={handleTaskCompletion} setNotification={handleSetNotification} />
          </div>
        )}

        {completedTaskResults.length > 0 && (
          <div className="my-8">
            <ResultsDisplay completedTasksData={completedTaskResults} />
          </div>
        )}
      </main>

      <footer className="w-full max-w-4xl text-center py-12 text-slate-400">
        <p>&copy; {new Date().getFullYear()} Audio2Sub. Built with React, FastAPI, and ❤️.</p>
      </footer>
    </div>
  );
}

export default App;
