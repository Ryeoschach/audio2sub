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
      <div className="glass-effect p-8 rounded-xl shadow-xl border border-white/20 text-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="text-6xl">🎵</div>
          <h3 className="text-xl font-semibold text-purple-300">
            还没有批量转录结果
          </h3>
          <p className="text-white/70">
            使用批量上传功能开始转录多个文件
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-green-300 mb-6 flex items-center gap-2">
        📊 批量转录结果
      </h2>
      
      {batchResults.map((batchResult) => (
        <div key={batchResult.batch_id} className="glass-effect rounded-xl shadow-xl border border-white/20 overflow-hidden hover:scale-105 transition-all duration-300">
          {/* 批量任务头部 */}
          <div 
            className="p-6 cursor-pointer hover:bg-white/10 transition-all duration-300"
            onClick={() => toggleBatchExpansion(batchResult.batch_id)}
          >
            <div className="flex justify-between items-center">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">
                    {expandedBatch === batchResult.batch_id ? '📂' : '📁'}
                  </span>
                  <div>
                    <h3 className="text-lg font-semibold text-white/90">
                      批量任务 #{batchResult.batch_id.slice(0, 8)}
                    </h3>
                    <div className="flex flex-wrap gap-4 mt-2">
                      <span className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 px-3 py-1 rounded-full border border-blue-400/30 text-blue-300 text-sm">
                        📁 总计 {batchResult.total_files} 个文件
                      </span>
                      <span className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 px-3 py-1 rounded-full border border-green-400/30 text-green-300 text-sm">
                        ✅ 成功 {batchResult.successful_files} 个
                      </span>
                      {batchResult.failed_files > 0 && (
                        <span className="bg-gradient-to-r from-red-500/20 to-pink-500/20 px-3 py-1 rounded-full border border-red-400/30 text-red-300 text-sm">
                          ❌ 失败 {batchResult.failed_files} 个
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-sm text-white/90 bg-gradient-to-r from-purple-500/20 to-pink-500/20 px-3 py-2 rounded-lg border border-purple-400/30">
                  ⏱️ 总用时: <span className="font-semibold text-purple-300">{formatDuration(batchResult.total_processing_time)}</span>
                </div>
                <div className="text-xs text-white/60 mt-1">
                  平均每文件: {formatDuration(batchResult.total_processing_time / batchResult.total_files)}
                </div>
              </div>
            </div>

            {/* 进度条 */}
            <div className="mt-4">
              <div className="w-full bg-gray-600/50 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-green-500 to-emerald-500 h-3 rounded-full shadow-lg transition-all duration-1000"
                  style={{ 
                    width: `${(batchResult.successful_files / batchResult.total_files) * 100}%` 
                  }}
                >
                  <div className="h-full bg-gradient-to-r from-white/20 to-transparent rounded-full"></div>
                </div>
              </div>
              <div className="flex justify-between text-xs text-gray-300 mt-2">
                <span className="flex items-center gap-1">
                  📈 成功率: <span className="text-green-300 font-semibold">{((batchResult.successful_files / batchResult.total_files) * 100).toFixed(1)}%</span>
                </span>
                <span className="italic">点击展开详情 👆</span>
              </div>
            </div>
          </div>

          {/* 批量任务详情 */}
          {expandedBatch === batchResult.batch_id && (
            <div className="border-t border-gray-600">
              {/* 成功的文件 */}
              {batchResult.results.length > 0 && (
                <div className="p-6">
                  <h4 className="text-lg font-semibold text-green-300 mb-4 flex items-center gap-2">
                    ✅ 成功转录的文件 ({batchResult.results.length})
                  </h4>
                  <div className="space-y-4">
                    {batchResult.results.map((result) => (
                      <div key={result.file_id} className="bg-gray-700/50 rounded-xl border border-gray-600 overflow-hidden backdrop-blur-sm hover:bg-gray-600/50 transition-all duration-300">
                        <div 
                          className="p-4 cursor-pointer"
                          onClick={() => toggleFileExpansion(result.file_id)}
                        >
                          <div className="flex justify-between items-center">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <span className="text-sm">
                                  {expandedFile === result.file_id ? '🔽' : '▶️'}
                                </span>
                                <span className="font-medium text-white/90">
                                  🎵 {result.original_filename}
                                </span>
                              </div>
                              <div className="flex flex-wrap gap-3 mt-2 text-xs">
                                <span className="bg-blue-500/20 px-2 py-1 rounded border border-blue-400/30 text-blue-300">
                                  ⏱️ {result.timing.total_time_formatted}
                                </span>
                                <span className="bg-purple-500/20 px-2 py-1 rounded border border-purple-400/30 text-purple-300">
                                  🤖 {result.transcription_params.model}
                                </span>
                                <span className="bg-green-500/20 px-2 py-1 rounded border border-green-400/30 text-green-300">
                                  🌍 {result.transcription_params.language}
                                </span>
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
                                  className="px-3 py-2 bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-600 hover:to-cyan-600 text-white text-xs rounded-lg transition-all duration-300 hover:scale-105 shadow-lg flex items-center gap-1"
                                >
                                  💾 下载 {file.type.toUpperCase()}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* 文件详情 */}
                        {expandedFile === result.file_id && (
                          <div className="p-4 bg-gray-600/50 border-t border-gray-500 backdrop-blur-sm">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                              <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 p-4 rounded-lg border border-purple-400/20">
                                <h5 className="font-semibold text-purple-300 mb-3 flex items-center gap-2">
                                  ⚙️ 转录信息
                                </h5>
                                <div className="text-sm text-white/90 space-y-2">
                                  <div className="bg-gray-600/50 p-2 rounded border border-gray-500">
                                    <span className="text-gray-300">🤖 模型:</span> <span className="font-medium">{result.transcription_params.model}</span>
                                  </div>
                                  <div className="bg-gray-600/50 p-2 rounded border border-gray-500">
                                    <span className="text-gray-300">🌍 语言:</span> <span className="font-medium">{result.transcription_params.language}</span>
                                  </div>
                                  <div className="bg-gray-600/50 p-2 rounded border border-gray-500">
                                    <span className="text-gray-300">📋 输出格式:</span> <span className="font-medium">{result.transcription_params.output_format}</span>
                                  </div>
                                  <div className="bg-gray-600/50 p-2 rounded border border-gray-500">
                                    <span className="text-gray-300">🔧 任务类型:</span> <span className="font-medium">{result.transcription_params.task_type}</span>
                                  </div>
                                </div>
                              </div>
                              <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 p-4 rounded-lg border border-blue-400/20">
                                <h5 className="font-semibold text-blue-300 mb-3 flex items-center gap-2">
                                  ⏱️ 时间统计
                                </h5>
                                <div className="text-sm text-white/90 space-y-2">
                                  <div className="bg-gray-600/50 p-2 rounded border border-gray-500">
                                    <span className="text-gray-300">🕐 总时间:</span> <span className="font-medium text-lg">{result.timing.total_time_formatted}</span>
                                  </div>
                                  <div className="bg-gray-600/50 p-2 rounded border border-gray-500">
                                    <span className="text-gray-300">⚡ 转录时间:</span> <span className="font-medium">{result.timing.transcription_time}秒</span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* 生成的文件 */}
                            <div className="mb-6">
                              <h5 className="font-semibold text-green-300 mb-3 flex items-center gap-2">
                                📁 生成文件
                              </h5>
                              <div className="flex flex-wrap gap-3">
                                {result.files.map((file) => (
                                  <div key={file.filename} className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 p-3 rounded-lg border border-green-400/20 hover:bg-green-500/20 transition-all duration-200">
                                    <div className="flex items-center gap-3">
                                      <span className="text-2xl">
                                        {file.type === 'srt' ? '📄' : file.type === 'vtt' ? '📹' : '📋'}
                                      </span>
                                      <div>
                                        <div className="text-white font-medium text-sm">{file.filename}</div>
                                        <div className="text-green-300 text-xs">{file.type.toUpperCase()} 格式</div>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* 转录内容预览 */}
                            {result.full_text && (
                              <div>
                                <h5 className="font-semibold text-orange-300 mb-3 flex items-center gap-2">
                                  📝 转录内容预览
                                </h5>
                                <div className="bg-black/30 p-4 rounded-lg border border-white/20 max-h-40 overflow-y-auto">
                                  <pre className="text-white/90 text-sm whitespace-pre-wrap leading-relaxed">
                                    {result.full_text.length > 200 
                                      ? `${result.full_text.substring(0, 200)}...` 
                                      : result.full_text
                                    }
                                  </pre>
                                </div>
                                {result.full_text.length > 200 && (
                                  <p className="text-white/60 text-xs mt-2 flex items-center gap-1">
                                    💡 显示前200字符，完整内容请下载字幕文件查看
                                  </p>
                                )}
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
                <div className="p-6 border-t border-gray-600">
                                  <h4 className="text-lg font-semibold text-red-300 mb-4 flex items-center gap-2">
                    ❌ 转录失败的文件 ({batchResult.errors.length})
                  </h4>
                  <div className="space-y-3">
                    {batchResult.errors.map((error) => (
                      <div key={error.file_id} className="bg-gradient-to-r from-red-500/10 to-pink-500/10 border border-red-400/30 rounded-xl p-4 backdrop-blur-sm hover:bg-red-500/20 transition-all duration-300">
                        <div className="flex items-start gap-3">
                          <span className="text-2xl flex-shrink-0">⚠️</span>
                          <div className="flex-1">
                            <span className="font-medium text-red-300 flex items-center gap-2">
                              🎵 {error.filename}
                            </span>
                            <div className="bg-red-500/20 p-3 rounded-lg mt-2 border border-red-400/30">
                              <p className="text-sm text-red-200 flex items-center gap-2">
                                🐛 <span className="font-medium">错误原因:</span> {error.error}
                              </p>
                            </div>
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
