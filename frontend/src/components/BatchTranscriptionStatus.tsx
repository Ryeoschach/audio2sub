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
      <div className="glass-effect p-6 rounded-xl shadow-xl border border-white/20">
        <div className="text-center">
          <div className="text-6xl mb-4">🚨</div>
          <h3 className="text-xl font-semibold mb-4 text-red-300">
            批量任务状态监控错误
          </h3>
          <p className="text-red-300 mb-4 bg-red-500/20 p-3 rounded-lg border border-red-400/30">
            错误: {error}
          </p>
          <button
            onClick={() => {
              setError(null);
              setIsPolling(true);
            }}
            className="btn-gradient-primary py-3 px-6 rounded-xl font-bold transition-all duration-300 hover:scale-105"
          >
            🔄 重试
          </button>
        </div>
      </div>
    );
  }

  if (!batchStatus) {
    return (
      <div className="glass-effect p-6 rounded-xl shadow-xl border border-white/20 text-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="text-6xl">⏳</div>
          <h3 className="text-xl font-semibold text-yellow-300">
            加载批量任务状态...
          </h3>
          <div className="flex items-center space-x-3">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-yellow-400"></div>
            <span className="text-white/80">正在获取任务信息...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-effect p-6 rounded-xl shadow-xl border border-white/20">
      <h3 className="text-xl font-semibold mb-6 text-blue-300 flex items-center gap-2">
        📊 批量转录状态监控
      </h3>

      {/* 整体进度 */}
      <div className="mb-6 p-5 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl border border-blue-400/30">
        <div className="flex justify-between items-center mb-3">
          <span className="text-sm font-medium text-white/90 flex items-center gap-2">
            🎯 整体进度
          </span>
          <span className={`text-sm font-bold px-3 py-1 rounded-full ${getOverallStatusColor(batchStatus.overall_status)} bg-gray-600/50`}>
            {batchStatus.overall_status}
          </span>
        </div>
        
        <div className="w-full bg-gray-600/50 rounded-full h-3 mb-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500 shadow-lg"
            style={{ width: `${batchStatus.progress_percentage}%` }}
          >
            <div className="h-full bg-gradient-to-r from-white/20 to-transparent rounded-full"></div>
          </div>
        </div>
        
        <div className="flex justify-between text-sm text-gray-300">
          <span className="flex items-center gap-1">
            ⚡ {batchStatus.progress_percentage.toFixed(1)}% 完成
          </span>
          <span className="flex items-center gap-1">
            📁 {batchStatus.completed_files + batchStatus.failed_files} / {batchStatus.total_files} 文件
          </span>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 p-4 rounded-xl text-center border border-green-400/30 hover:scale-105 transition-all duration-300">
          <div className="text-2xl mb-1">✅</div>
          <div className="text-2xl font-bold text-green-400">{batchStatus.completed_files}</div>
          <div className="text-xs text-green-300">已完成</div>
        </div>
        <div className="bg-gradient-to-r from-red-500/20 to-pink-500/20 p-4 rounded-xl text-center border border-red-400/30 hover:scale-105 transition-all duration-300">
          <div className="text-2xl mb-1">❌</div>
          <div className="text-2xl font-bold text-red-400">{batchStatus.failed_files}</div>
          <div className="text-xs text-red-300">失败</div>
        </div>
        <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 p-4 rounded-xl text-center border border-yellow-400/30 hover:scale-105 transition-all duration-300">
          <div className="text-2xl mb-1">🔄</div>
          <div className="text-2xl font-bold text-yellow-400">
            {batchStatus.total_files - batchStatus.completed_files - batchStatus.failed_files}
          </div>
          <div className="text-xs text-yellow-300">处理中</div>
        </div>
      </div>

      {/* 文件详细状态 */}
      <div className="mb-6">
        <h4 className="text-lg font-semibold mb-4 text-purple-300 flex items-center gap-2">
          📝 文件处理状态
        </h4>
        <div className="max-h-80 overflow-y-auto space-y-3 pr-2">
          {batchStatus.tasks.map((task: BatchTaskInfo) => (
            <div key={task.file_id} className="bg-gray-700/50 p-4 rounded-xl border border-gray-600 hover:bg-gray-600/50 transition-all duration-300">
              <div className="flex justify-between items-center">
                <div className="flex-1 mr-4">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-xl">{getStatusIcon(task.status)}</span>
                    <span className="text-sm font-medium text-white/90 truncate">
                      📄 {task.filename}
                    </span>
                  </div>
                  {task.status === 'PROGRESS' && (
                    <div className="mt-2">
                      <div className="w-full bg-gray-600/50 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-yellow-400 to-orange-400 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-gray-300 mt-1 flex items-center gap-1">
                        ⚡ 处理中... {task.progress}%
                      </p>
                    </div>
                  )}
                  {task.error && (
                    <div className="mt-2 p-2 bg-red-500/20 rounded border border-red-400/30">
                      <p className="text-xs text-red-300 flex items-center gap-1">
                        ⚠️ 错误: {task.error}
                      </p>
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <div className={`text-sm font-bold px-2 py-1 rounded ${getStatusColor(task.status)} bg-gray-600/50`}>
                    {task.status}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 时间信息 */}
      {batchStatus.start_time && (
        <div className="mb-6 p-4 bg-gradient-to-r from-gray-500/10 to-slate-500/10 rounded-xl border border-gray-400/20">
          <h4 className="text-sm font-medium text-white/90 mb-2 flex items-center gap-2">
            🕒 时间信息
          </h4>
          <div className="space-y-1 text-xs text-white/70">
            <p className="flex items-center gap-2">
              🚀 <span>开始时间: {new Date(batchStatus.start_time).toLocaleString()}</span>
            </p>
            {batchStatus.estimated_completion_time && (
              <p className="flex items-center gap-2">
                🏁 <span>预计完成: {new Date(batchStatus.estimated_completion_time).toLocaleString()}</span>
              </p>
            )}
          </div>
        </div>
      )}

      {/* 控制按钮 */}
      <div className="flex space-x-3">
        <button
          onClick={() => setIsPolling(!isPolling)}
          className={`flex-1 px-4 py-3 rounded-xl font-bold transition-all duration-300 hover:scale-105 flex items-center justify-center gap-2 ${
            isPolling 
              ? 'bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white' 
              : 'bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white'
          }`}
        >
          {isPolling ? (
            <>⏸️ <span>暂停监控</span></>
          ) : (
            <>▶️ <span>恢复监控</span></>
          )}
        </button>
        
        <button
          onClick={fetchBatchStatus}
          disabled={isPolling}
          className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-500/20 to-purple-500/20 hover:from-blue-500/30 hover:to-purple-500/30 text-white font-bold rounded-xl border border-blue-400/30 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          🔄 <span>手动刷新</span>
        </button>
      </div>
    </div>
  );
};

export default BatchTranscriptionStatus;
