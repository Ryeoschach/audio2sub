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
      <div className="glass-effect p-6 rounded-xl shadow-xl border border-white/20 text-center">
        <div className="flex flex-col items-center space-y-3">
          <div className="text-4xl">😴</div>
          <p className="text-white/80">暂无转录任务</p>
          <p className="text-white/60 text-sm">上传文件开始转录吧！</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-effect p-6 rounded-xl shadow-xl border border-white/20">
      <h2 className="text-2xl font-semibold mb-6 text-blue-300 flex items-center gap-2">
        ⚡ 转录进度监控
      </h2>
      <div className="space-y-4">
        {internalTasks.map((task) => {
          const getStatusConfig = (status: string) => {
            switch (status) {
              case 'SUCCESS':
                return { 
                  icon: '✅', 
                  color: 'from-green-400 to-emerald-400',
                  bgColor: 'from-green-500/20 to-emerald-500/20',
                  borderColor: 'border-green-400/30'
                };
              case 'FAILURE':
                return { 
                  icon: '❌', 
                  color: 'from-red-400 to-pink-400',
                  bgColor: 'from-red-500/20 to-pink-500/20',
                  borderColor: 'border-red-400/30'
                };
              case 'PROGRESS':
                return { 
                  icon: '🔄', 
                  color: 'from-blue-400 to-cyan-400',
                  bgColor: 'from-blue-500/20 to-cyan-500/20',
                  borderColor: 'border-blue-400/30'
                };
              case 'PENDING':
                return { 
                  icon: '⏳', 
                  color: 'from-yellow-400 to-orange-400',
                  bgColor: 'from-yellow-500/20 to-orange-500/20',
                  borderColor: 'border-yellow-400/30'
                };
              default:
                return { 
                  icon: '🔄', 
                  color: 'from-gray-400 to-slate-400',
                  bgColor: 'from-gray-500/20 to-slate-500/20',
                  borderColor: 'border-gray-400/30'
                };
            }
          };

          const statusConfig = getStatusConfig(task.status);

          return (
            <div key={task.taskId} className={`p-4 bg-gradient-to-r ${statusConfig.bgColor} rounded-xl shadow-lg border ${statusConfig.borderColor} backdrop-blur-sm hover:scale-105 transition-all duration-300`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-white/90 truncate mb-2 flex items-center gap-2" title={task.filename}>
                    📄 {task.filename}
                  </h3>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{statusConfig.icon}</span>
                    <span className="text-blue-300 font-medium">
                      状态: {task.progressMessage || task.status}
                    </span>
                  </div>
                  <div className="text-sm text-white/70">
                    <span className="bg-gray-600/50 px-2 py-1 rounded text-xs">
                      🤖 模型: {task.model}
                    </span>
                  </div>
                </div>
              </div>
              
              {task.status === 'PROGRESS' && (
                <div className="mt-3">
                  <div className="w-full bg-gray-600/50 rounded-full h-3 overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full animate-pulse shadow-lg" style={{ width: '50%' }}>
                      <div className="h-full bg-gradient-to-r from-white/20 to-transparent rounded-full"></div>
                    </div>
                  </div>
                  <p className="text-xs text-white/60 mt-2 flex items-center gap-1">
                    ⚡ 正在处理中...
                  </p>
                </div>
              )}
              
              {task.error && (
                <div className="mt-3 p-2 bg-red-500/20 rounded-lg border border-red-400/30">
                  <p className="text-xs text-red-300 flex items-center gap-2">
                    ⚠️ 错误: {task.error}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TranscriptionStatus;
