import React, { useState } from 'react';

interface ResultFile {
  file_id: string;
  original_filename: string;
  files: Array<{
    type: string;
    filename: string;
    path: string;
  }>;
  full_text: string;
  transcription_params: {
    model: string;
    language: string;
    output_format: string;
    task_type: string;
  };
  timing: {
    total_time: number;
    total_time_formatted: string;
    transcription_time: number;
  };
}

interface ResultsDisplayProps {
  completedTasksData: ResultFile[];
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ completedTasksData }) => {
  const [expandedResults, setExpandedResults] = useState<Set<string>>(new Set());

  if (completedTasksData.length === 0) {
    return (
      <div className="glass-effect p-8 rounded-xl shadow-xl border border-white/20 text-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="text-6xl">📊</div>
          <h3 className="text-xl font-semibold text-blue-300">
            暂无转录结果
          </h3>
          <p className="text-theme-secondary">完成的任务将显示在这里</p>
        </div>
      </div>
    );
  }

  const handleDownload = (fileId: string, filePath: string) => {
    // Use /api prefix for Vite proxy
    window.open(`/api/results/${fileId}/${filePath}`, '_blank');
  };

  const toggleExpanded = (fileId: string) => {
    const newExpanded = new Set(expandedResults);
    if (newExpanded.has(fileId)) {
      newExpanded.delete(fileId);
    } else {
      newExpanded.add(fileId);
    }
    setExpandedResults(newExpanded);
  };

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(1)}秒`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}分${remainingSeconds.toFixed(1)}秒`;
  };

  return (
    <div className="space-y-6">
      {completedTasksData.map((taskResult) => {
        const isExpanded = expandedResults.has(taskResult.file_id);
        const srtFile = taskResult.files.find(f => f.type === 'srt');
        const vttFile = taskResult.files.find(f => f.type === 'vtt');
        
        return (
          <div key={taskResult.file_id} className="glass-effect border border-white/20 p-6 rounded-xl shadow-xl hover:scale-105 transition-all duration-300">
            {/* 文件信息头部 */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-medium text-theme-primary truncate flex items-center gap-2" title={taskResult.original_filename}>
                  🎵 {taskResult.original_filename}
                </h3>
                <div className="flex flex-wrap gap-4 mt-3 text-sm">
                  <span className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 px-3 py-1 rounded-full border border-purple-400/30">
                    🤖 <span className="text-purple-300">{taskResult.transcription_params.model}</span>
                  </span>
                  <span className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 px-3 py-1 rounded-full border border-blue-400/30">
                    🌍 <span className="text-blue-300">{taskResult.transcription_params.language}</span>
                  </span>
                  <span className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 px-3 py-1 rounded-full border border-green-400/30">
                    ⏱️ <span className="text-green-300">{formatTime(taskResult.timing.total_time)}</span>
                  </span>
                  <span className="bg-gradient-to-r from-orange-500/20 to-yellow-500/20 px-3 py-1 rounded-full border border-orange-400/30">
                    📁 <span className="text-orange-300">{taskResult.files.length} 个文件</span>
                  </span>
                </div>
              </div>
              <button
                onClick={() => toggleExpanded(taskResult.file_id)}
                className="ml-4 px-4 py-2 bg-theme-card hover:bg-theme-hover text-theme-primary border border-theme-border rounded-lg transition-all duration-300 hover:scale-105"
              >
                {isExpanded ? '🔽 收起' : '🔍 详情'}
              </button>
            </div>

            {/* 下载按钮 */}
            <div className="flex flex-wrap gap-3 mb-4">
              {srtFile && (
                <button
                  onClick={() => handleDownload(taskResult.file_id, srtFile.filename)}
                  className="flex-1 min-w-[140px] bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold py-3 px-4 rounded-xl transition-all duration-300 hover:scale-105 shadow-xl border border-green-500/50 flex items-center justify-center space-x-2"
                >
                  <span>📄</span>
                  <span>下载 SRT</span>
                </button>
              )}
              {vttFile && (
                <button
                  onClick={() => handleDownload(taskResult.file_id, vttFile.filename)}
                  className="flex-1 min-w-[140px] bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white font-semibold py-3 px-4 rounded-xl transition-all duration-300 hover:scale-105 shadow-xl border border-orange-500/50 flex items-center justify-center space-x-2"
                >
                  <span>📹</span>
                  <span>下载 VTT</span>
                </button>
              )}
              {taskResult.files.length === 0 && (
                <div className="text-theme-secondary text-sm py-3 px-4 bg-theme-card rounded-xl border border-theme-border flex items-center gap-2">
                  ⚠️ 暂无可下载文件
                </div>
              )}
            </div>

            {/* 展开的详细信息 */}
            {isExpanded && (
              <div className="border-t border-theme-border pt-6 space-y-6">
                {/* 转录参数 */}
                <div className="bg-theme-card p-4 rounded-xl border border-purple-500/30">
                  <h4 className="text-purple-300 font-medium mb-3 flex items-center gap-2">
                    ⚙️ 转录参数
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div className="bg-theme-card p-2 rounded border border-theme-border">
                      <span className="text-theme-secondary block">🤖 模型:</span>
                      <span className="text-theme-primary font-medium">{taskResult.transcription_params.model}</span>
                    </div>
                    <div className="bg-theme-card p-2 rounded border border-theme-border">
                      <span className="text-theme-secondary block">🌍 语言:</span>
                      <span className="text-theme-primary font-medium">{taskResult.transcription_params.language}</span>
                    </div>
                    <div className="bg-theme-card p-2 rounded border border-theme-border">
                      <span className="text-theme-secondary block">📋 格式:</span>
                      <span className="text-theme-primary font-medium">{taskResult.transcription_params.output_format}</span>
                    </div>
                    <div className="bg-theme-card p-2 rounded border border-theme-border">
                      <span className="text-theme-secondary block">🔧 类型:</span>
                      <span className="text-theme-primary font-medium">{taskResult.transcription_params.task_type}</span>
                    </div>
                  </div>
                </div>

                {/* 处理时间 */}
                <div className="bg-theme-card p-4 rounded-xl border border-blue-500/30">
                  <h4 className="text-blue-300 font-medium mb-3 flex items-center gap-2">
                    ⏱️ 处理时间
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div className="bg-theme-card p-3 rounded border border-theme-border">
                      <span className="text-theme-secondary block">🕐 总耗时:</span>
                      <span className="text-theme-primary font-medium text-lg">{formatTime(taskResult.timing.total_time)}</span>
                    </div>
                    <div className="bg-theme-card p-3 rounded border border-theme-border">
                      <span className="text-theme-secondary block">⚡ 转录耗时:</span>
                      <span className="text-theme-primary font-medium text-lg">{formatTime(taskResult.timing.transcription_time)}</span>
                    </div>
                  </div>
                </div>

                {/* 生成文件列表 */}
                {taskResult.files.length > 0 && (
                  <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 p-4 rounded-xl border border-green-400/20">
                    <h4 className="text-green-300 font-medium mb-3 flex items-center gap-2">
                      📁 生成文件
                    </h4>
                    <div className="space-y-2">
                      {taskResult.files.map((file, index) => (
                        <div key={index} className="flex items-center justify-between bg-theme-card p-3 rounded-lg border border-theme-border hover:bg-theme-hover transition-all duration-200">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">
                              {file.type === 'srt' ? '📄' : file.type === 'vtt' ? '📹' : '📋'}
                            </span>
                            <div>
                              <span className="text-theme-primary text-sm font-medium block">{file.filename}</span>
                              <span className="text-theme-secondary text-xs">{file.type.toUpperCase()} 格式</span>
                            </div>
                          </div>
                          <button
                            onClick={() => handleDownload(taskResult.file_id, file.filename)}
                            className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white px-3 py-1 rounded-lg text-sm transition-all duration-300 hover:scale-105"
                          >
                            💾 下载
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 转录文本预览 */}
                {taskResult.full_text && (
                  <div className="bg-gradient-to-r from-orange-500/10 to-yellow-500/10 p-4 rounded-xl border border-orange-400/20">
                    <h4 className="text-orange-300 font-medium mb-3 flex items-center gap-2">
                      📝 转录文本预览
                    </h4>
                    <div className="bg-black/30 p-4 rounded-lg border border-white/20 max-h-40 overflow-y-auto">
                      <pre className="text-theme-primary text-sm whitespace-pre-wrap leading-relaxed">
                        {taskResult.full_text.length > 500 
                          ? taskResult.full_text.substring(0, 500) + '...' 
                          : taskResult.full_text}
                      </pre>
                    </div>
                    {taskResult.full_text.length > 500 && (
                      <p className="text-theme-secondary text-xs mt-2 flex items-center gap-1">
                        💡 显示前500字符，完整内容请下载字幕文件查看
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ResultsDisplay;
