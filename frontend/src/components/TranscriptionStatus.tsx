import React, { useEffect, useState, useCallback } from 'react';
import { audio2subAPI } from '../services/api';

interface TranscriptionTask {
  taskId: string;
  fileId: string;
  filename: string;
  model: string;
  status: string;
  progressMessage?: string;
  result?: any;
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
      const response = await audio2subAPI.getTaskStatus(task.taskId);
      
      let progressMessage = '';
      if (response.state === 'PROGRESS' && response.result && typeof response.result === 'object' && 'status' in response.result) {
        progressMessage = response.result.status;
      } else if (response.status) {
        progressMessage = response.status;
      }

      const updatedTask = { 
        ...task, 
        status: response.state, 
        progressMessage,
        result: response.result, 
        error: response.state === 'FAILURE' ? (response.status || '转录失败') : undefined 
      };
      
      setInternalTasks(prevTasks => 
        prevTasks.map(t => t.taskId === task.taskId ? updatedTask : t)
      );

      if (response.state === 'SUCCESS' || response.state === 'FAILURE') {
        onTaskCompletion(updatedTask);
        if(response.state === 'SUCCESS') {
          setNotification(`文件 '${task.filename}' 转录完成`, 'success');
        } else {
          setNotification(`文件 '${task.filename}' 转录失败: ${response.status || '未知错误'}`, 'error');
        }
      }
    } catch (error) {
      console.error(`Error fetching status for task ${task.taskId}:`, error);
      const errorMsg = error instanceof Error ? error.message : '状态查询失败';
      setInternalTasks(prevTasks => 
        prevTasks.map(t => t.taskId === task.taskId ? { ...t, error: errorMsg } : t)
      );
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
