import React, { useState } from 'react';
import { BatchResultSummary } from '../services/api';

interface BatchResultsDisplayProps {
  batchResults: BatchResultSummary[];
  setNotification: (message: string, type: 'success' | 'error') => void;
}

const BatchResultsDisplay: React.FC<BatchResultsDisplayProps> = ({
  batchResults,
  setNotification
}) => {
  const [expandedBatch, setExpandedBatch] = useState<string | null>(null);
  const [expandedFile, setExpandedFile] = useState<string | null>(null);

  const downloadFile = async (fileId: string, filename: string) => {
    try {
      const baseURL = '/api';
      const url = `${baseURL}/results/${fileId}/${filename}`;
      
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      setNotification(`开始下载 ${filename}`, 'success');
    } catch (error) {
      console.error('Download failed:', error);
      setNotification(`下载 ${filename} 失败`, 'error');
    }
  };

  const toggleBatchExpansion = (batchId: string) => {
    setExpandedBatch(expandedBatch === batchId ? null : batchId);
  };

  const toggleFileExpansion = (fileId: string) => {
    setExpandedFile(expandedFile === fileId ? null : fileId);
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}分${secs}秒`;
  };

  if (batchResults.length === 0) {
    return (
      <div className="bg-slate-700 p-6 rounded-lg shadow-md text-center">
        <div className="text-slate-400 text-lg">
          🎵 还没有批量转录结果
        </div>
        <p className="text-slate-500 mt-2">
          使用批量上传功能开始转录多个文件
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold text-teal-300 mb-4">
        批量转录结果
      </h2>
      
      {batchResults.map((batchResult) => (
        <div key={batchResult.batch_id} className="bg-slate-700 rounded-lg shadow-md overflow-hidden">
          {/* 批量任务头部 */}
          <div 
            className="p-4 cursor-pointer hover:bg-slate-600 transition-colors"
            onClick={() => toggleBatchExpansion(batchResult.batch_id)}
          >
            <div className="flex justify-between items-center">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <span className="text-lg">
                    {expandedBatch === batchResult.batch_id ? '📂' : '📁'}
                  </span>
                  <div>
                    <h3 className="text-lg font-semibold text-slate-200">
                      批量任务 #{batchResult.batch_id.slice(0, 8)}
                    </h3>
                    <p className="text-sm text-slate-400">
                      总计 {batchResult.total_files} 个文件，
                      成功 {batchResult.successful_files} 个，
                      失败 {batchResult.failed_files} 个
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-sm text-slate-300">
                  总用时: {formatDuration(batchResult.total_processing_time)}
                </div>
                <div className="text-xs text-slate-400">
                  平均每文件: {formatDuration(batchResult.total_processing_time / batchResult.total_files)}
                </div>
              </div>
            </div>

            {/* 进度条 */}
            <div className="mt-3">
              <div className="w-full bg-slate-600 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-green-500 to-teal-500 h-2 rounded-full"
                  style={{ 
                    width: `${(batchResult.successful_files / batchResult.total_files) * 100}%` 
                  }}
                />
              </div>
              <div className="flex justify-between text-xs text-slate-400 mt-1">
                <span>成功率: {((batchResult.successful_files / batchResult.total_files) * 100).toFixed(1)}%</span>
                <span>点击展开详情</span>
              </div>
            </div>
          </div>

          {/* 批量任务详情 */}
          {expandedBatch === batchResult.batch_id && (
            <div className="border-t border-slate-600">
              {/* 成功的文件 */}
              {batchResult.results.length > 0 && (
                <div className="p-4">
                  <h4 className="text-lg font-semibold text-green-400 mb-3">
                    ✅ 成功转录的文件 ({batchResult.results.length})
                  </h4>
                  <div className="space-y-3">
                    {batchResult.results.map((result) => (
                      <div key={result.file_id} className="bg-slate-600 rounded-lg overflow-hidden">
                        <div 
                          className="p-3 cursor-pointer hover:bg-slate-500 transition-colors"
                          onClick={() => toggleFileExpansion(result.file_id)}
                        >
                          <div className="flex justify-between items-center">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <span className="text-sm">
                                  {expandedFile === result.file_id ? '🔽' : '▶️'}
                                </span>
                                <span className="font-medium text-slate-200">
                                  {result.original_filename}
                                </span>
                              </div>
                              <div className="text-xs text-slate-400 mt-1">
                                用时: {result.timing.total_time_formatted} | 
                                模型: {result.transcription_params.model} | 
                                语言: {result.transcription_params.language}
                              </div>
                            </div>
                            <div className="flex space-x-2">
                              {result.files.map((file) => (
                                <button
                                  key={file.filename}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    downloadFile(result.file_id, file.filename);
                                  }}
                                  className="px-3 py-1 bg-teal-500 hover:bg-teal-600 text-white text-xs rounded transition-colors"
                                >
                                  下载 {file.type.toUpperCase()}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* 文件详情 */}
                        {expandedFile === result.file_id && (
                          <div className="p-3 bg-slate-500 border-t border-slate-400">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                              <div>
                                <h5 className="font-semibold text-slate-200 mb-2">转录信息</h5>
                                <div className="text-sm text-slate-300 space-y-1">
                                  <p><span className="text-slate-400">模型:</span> {result.transcription_params.model}</p>
                                  <p><span className="text-slate-400">语言:</span> {result.transcription_params.language}</p>
                                  <p><span className="text-slate-400">输出格式:</span> {result.transcription_params.output_format}</p>
                                  <p><span className="text-slate-400">任务类型:</span> {result.transcription_params.task_type}</p>
                                </div>
                              </div>
                              <div>
                                <h5 className="font-semibold text-slate-200 mb-2">时间统计</h5>
                                <div className="text-sm text-slate-300 space-y-1">
                                  <p><span className="text-slate-400">总时间:</span> {result.timing.total_time_formatted}</p>
                                  <p><span className="text-slate-400">转录时间:</span> {result.timing.transcription_time}秒</p>
                                </div>
                              </div>
                            </div>

                            {/* 生成的文件 */}
                            <div className="mb-4">
                              <h5 className="font-semibold text-slate-200 mb-2">生成文件</h5>
                              <div className="flex flex-wrap gap-2">
                                {result.files.map((file) => (
                                  <div key={file.filename} className="bg-slate-600 p-2 rounded text-xs">
                                    <div className="text-slate-200">{file.filename}</div>
                                    <div className="text-slate-400">{file.type}</div>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* 转录内容预览 */}
                            {result.full_text && (
                              <div>
                                <h5 className="font-semibold text-slate-200 mb-2">转录内容预览</h5>
                                <div className="bg-slate-600 p-3 rounded text-sm text-slate-300 max-h-32 overflow-y-auto">
                                  {result.full_text.length > 200 
                                    ? `${result.full_text.substring(0, 200)}...` 
                                    : result.full_text
                                  }
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 失败的文件 */}
              {batchResult.errors.length > 0 && (
                <div className="p-4 border-t border-slate-600">
                  <h4 className="text-lg font-semibold text-red-400 mb-3">
                    ❌ 转录失败的文件 ({batchResult.errors.length})
                  </h4>
                  <div className="space-y-2">
                    {batchResult.errors.map((error) => (
                      <div key={error.file_id} className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <span className="font-medium text-red-300">{error.filename}</span>
                            <p className="text-sm text-red-200 mt-1">
                              错误: {error.error}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default BatchResultsDisplay;
