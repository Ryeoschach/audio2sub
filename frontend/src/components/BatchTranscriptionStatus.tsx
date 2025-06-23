import React, { useState, useEffect, useCallback } from 'react';
import { audio2subAPI, BatchTaskStatus, BatchTaskInfo } from '../services/api';

interface BatchTranscriptionStatusProps {
  batchId: string;
  onBatchComplete: (batchId: string, results: any) => void;
  setNotification: (message: string, type: 'success' | 'error') => void;
}

const BatchTranscriptionStatus: React.FC<BatchTranscriptionStatusProps> = ({
  batchId,
  onBatchComplete,
  setNotification
}) => {
  const [batchStatus, setBatchStatus] = useState<BatchTaskStatus | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBatchStatus = useCallback(async () => {
    try {
      const status = await audio2subAPI.getBatchTaskStatus(batchId);
      setBatchStatus(status);
      setError(null);

      // 检查是否完成
      if (status.overall_status === 'COMPLETED' || status.overall_status === 'FAILED') {
        setIsPolling(false);
        
        if (status.overall_status === 'COMPLETED') {
          // 获取批量结果
          try {
            const results = await audio2subAPI.getBatchResultSummary(batchId);
            onBatchComplete(batchId, results);
            setNotification(
              `批量任务完成！成功: ${results.successful_files}, 失败: ${results.failed_files}`, 
              'success'
            );
          } catch (err) {
            console.error('Failed to get batch results:', err);
            setNotification('批量任务完成，但获取结果失败', 'error');
          }
        } else {
          setNotification('批量任务失败', 'error');
        }
      }
    } catch (err) {
      console.error('Failed to fetch batch status:', err);
      setError(err instanceof Error ? err.message : '获取批量任务状态失败');
    }
  }, [batchId, onBatchComplete, setNotification]);

  useEffect(() => {
    let intervalId: number;

    if (isPolling) {
      // 立即执行一次
      fetchBatchStatus();
      
      // 每3秒轮询一次
      intervalId = window.setInterval(fetchBatchStatus, 3000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [isPolling, fetchBatchStatus]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SUCCESS': return 'text-green-400';
      case 'FAILURE': return 'text-red-400';
      case 'PROGRESS': return 'text-yellow-400';
      case 'PENDING': return 'text-slate-400';
      default: return 'text-slate-400';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS': return '✅';
      case 'FAILURE': return '❌';
      case 'PROGRESS': return '🔄';
      case 'PENDING': return '⏳';
      default: return '❓';
    }
  };

  const getOverallStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'text-green-400';
      case 'FAILED': return 'text-red-400';
      case 'PROCESSING': return 'text-yellow-400';
      case 'PENDING': return 'text-slate-400';
      default: return 'text-slate-400';
    }
  };

  if (error) {
    return (
      <div className="bg-slate-700 p-6 rounded-lg shadow-md">
        <h3 className="text-xl font-semibold mb-4 text-red-400">批量任务状态监控错误</h3>
        <p className="text-red-300">错误: {error}</p>
        <button
          onClick={() => {
            setError(null);
            setIsPolling(true);
          }}
          className="mt-4 bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
        >
          重试
        </button>
      </div>
    );
  }

  if (!batchStatus) {
    return (
      <div className="bg-slate-700 p-6 rounded-lg shadow-md">
        <h3 className="text-xl font-semibold mb-4 text-yellow-400">加载批量任务状态...</h3>
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400"></div>
          <span className="text-slate-300">正在获取任务信息...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-700 p-6 rounded-lg shadow-md">
      <h3 className="text-xl font-semibold mb-4 text-teal-300">
        批量转录状态监控
      </h3>

      {/* 整体进度 */}
      <div className="mb-6 p-4 bg-slate-600 rounded-lg">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-slate-300">整体进度</span>
          <span className={`text-sm font-semibold ${getOverallStatusColor(batchStatus.overall_status)}`}>
            {batchStatus.overall_status}
          </span>
        </div>
        
        <div className="w-full bg-slate-500 rounded-full h-2 mb-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-teal-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${batchStatus.progress_percentage}%` }}
          />
        </div>
        
        <div className="flex justify-between text-sm text-slate-400">
          <span>{batchStatus.progress_percentage.toFixed(1)}% 完成</span>
          <span>
            {batchStatus.completed_files + batchStatus.failed_files} / {batchStatus.total_files} 文件
          </span>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-slate-600 p-3 rounded text-center">
          <div className="text-lg font-bold text-green-400">{batchStatus.completed_files}</div>
          <div className="text-xs text-slate-400">已完成</div>
        </div>
        <div className="bg-slate-600 p-3 rounded text-center">
          <div className="text-lg font-bold text-red-400">{batchStatus.failed_files}</div>
          <div className="text-xs text-slate-400">失败</div>
        </div>
        <div className="bg-slate-600 p-3 rounded text-center">
          <div className="text-lg font-bold text-yellow-400">
            {batchStatus.total_files - batchStatus.completed_files - batchStatus.failed_files}
          </div>
          <div className="text-xs text-slate-400">处理中</div>
        </div>
      </div>

      {/* 文件详细状态 */}
      <div className="mb-4">
        <h4 className="text-lg font-semibold mb-3 text-slate-300">文件处理状态</h4>
        <div className="max-h-64 overflow-y-auto space-y-2">
          {batchStatus.tasks.map((task: BatchTaskInfo) => (
            <div key={task.file_id} className="bg-slate-600 p-3 rounded-lg">
              <div className="flex justify-between items-center">
                <div className="flex-1 mr-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm">{getStatusIcon(task.status)}</span>
                    <span className="text-sm font-medium text-slate-200 truncate">
                      {task.filename}
                    </span>
                  </div>
                  {task.status === 'PROGRESS' && (
                    <div className="mt-1">
                      <div className="w-full bg-slate-500 rounded-full h-1">
                        <div
                          className="bg-yellow-400 h-1 rounded-full transition-all duration-300"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                    </div>
                  )}
                  {task.error && (
                    <div className="mt-1 text-xs text-red-400">
                      错误: {task.error}
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <div className={`text-sm font-semibold ${getStatusColor(task.status)}`}>
                    {task.status}
                  </div>
                  {task.status === 'PROGRESS' && (
                    <div className="text-xs text-slate-400">
                      {task.progress}%
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 时间信息 */}
      {batchStatus.start_time && (
        <div className="text-xs text-slate-400 border-t border-slate-600 pt-3">
          <p>开始时间: {new Date(batchStatus.start_time).toLocaleString()}</p>
          {batchStatus.estimated_completion_time && (
            <p>预计完成: {new Date(batchStatus.estimated_completion_time).toLocaleString()}</p>
          )}
        </div>
      )}

      {/* 控制按钮 */}
      <div className="mt-4 flex space-x-2">
        <button
          onClick={() => setIsPolling(!isPolling)}
          className={`px-4 py-2 rounded font-medium ${
            isPolling 
              ? 'bg-red-500 hover:bg-red-600 text-white' 
              : 'bg-green-500 hover:bg-green-600 text-white'
          }`}
        >
          {isPolling ? '暂停监控' : '恢复监控'}
        </button>
        
        <button
          onClick={fetchBatchStatus}
          disabled={isPolling}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded disabled:opacity-50"
        >
          手动刷新
        </button>
      </div>
    </div>
  );
};

export default BatchTranscriptionStatus;
