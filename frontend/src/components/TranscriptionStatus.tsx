import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';

interface TranscriptionTask {
  taskId: string;
  fileId: string;
  filename: string;
  status: string;
  progressMessage?: string;
  result?: any; // Define more specific type based on actual API response
  error?: string;
}

interface TranscriptionStatusProps {
  tasks: TranscriptionTask[];
  onTaskCompletion: (completedTask: TranscriptionTask) => void;
  setNotification: (message: string, type: 'success' | 'error') => void;
}

const TranscriptionStatus: React.FC<TranscriptionStatusProps> = ({ tasks, onTaskCompletion, setNotification }) => {
  const [internalTasks, setInternalTasks] = useState<TranscriptionTask[]>(tasks);

  const pollStatus = useCallback(async (task: TranscriptionTask) => {
    try {
      const response = await axios.get(`/api/status/${task.taskId}`);
      const updatedTask = { ...task, status: response.data.state, progressMessage: response.data.status, result: response.data.result, error: response.data.state === 'FAILURE' ? response.data.status : undefined };
      
      setInternalTasks(prevTasks => 
        prevTasks.map(t => t.taskId === task.taskId ? updatedTask : t)
      );

      if (response.data.state === 'SUCCESS' || response.data.state === 'FAILURE') {
        onTaskCompletion(updatedTask);
        if(response.data.state === 'SUCCESS') {
            setNotification(`Transcription for '${task.filename}' completed.`, 'success');
        } else {
            setNotification(`Transcription for '${task.filename}' failed: ${response.data.status}`, 'error');
        }
      }
    } catch (error) {
      console.error(`Error fetching status for task ${task.taskId}:`, error);
      const errorMsg = axios.isAxiosError(error) && error.response ? error.response.data.detail : 'Failed to fetch status';
      setInternalTasks(prevTasks => 
        prevTasks.map(t => t.taskId === task.taskId ? { ...t, error: errorMsg } : t)
      );
      // Optionally, notify user about polling error for a specific task
    }
  }, [onTaskCompletion, setNotification]);

  useEffect(() => {
    setInternalTasks(tasks); // Sync with parent tasks
    const activeTasks = tasks.filter(task => task.status !== 'SUCCESS' && task.status !== 'FAILURE');
    if (activeTasks.length === 0) return;

    const intervalId = setInterval(() => {
      activeTasks.forEach(task => pollStatus(task));
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(intervalId);
  }, [tasks, pollStatus]);

  if (internalTasks.length === 0) {
    return (
      <div className="bg-slate-700 p-6 rounded-lg shadow-md text-center">
        <p className="text-slate-300">No active transcription tasks.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-700 p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-6 text-teal-300">Transcription Progress</h2>
      <div className="space-y-4">
        {internalTasks.map((task) => (
          <div key={task.taskId} className="p-4 bg-slate-600 rounded-md shadow">
            <h3 className="text-lg font-medium text-slate-100 truncate" title={task.filename}>{task.filename}</h3>
            <p className={`text-sm ${task.status === 'SUCCESS' ? 'text-green-400' : task.status === 'FAILURE' ? 'text-red-400' : 'text-yellow-400'}`}>
              Status: {task.progressMessage || task.status}
            </p>
            {task.status === 'PROGRESS' && (
                <div className="w-full bg-slate-500 rounded-full h-2.5 mt-2">
                    <div className="bg-blue-500 h-2.5 rounded-full animate-pulse" style={{ width: '50%' }}></div> {/* Basic indeterminate progress */}
                </div>
            )}
            {task.error && <p className="text-xs text-red-400 mt-1">Error: {task.error}</p>}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TranscriptionStatus;
