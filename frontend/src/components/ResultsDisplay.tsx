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
      <div className="bg-slate-700 p-6 rounded-lg shadow-md text-center">
        <p className="text-slate-300">暂无转录结果，完成的任务将显示在这里</p>
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
          <div key={taskResult.file_id} className="bg-slate-700 p-6 rounded-lg shadow-md">
            {/* 文件信息头部 */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex-1">
                <h3 className="text-lg font-medium text-slate-100 truncate" title={taskResult.original_filename}>
                  {taskResult.original_filename}
                </h3>
                <div className="flex flex-wrap gap-4 mt-2 text-sm text-slate-400">
                  <span>模型: <span className="text-teal-300">{taskResult.transcription_params.model}</span></span>
                  <span>语言: <span className="text-teal-300">{taskResult.transcription_params.language}</span></span>
                  <span>耗时: <span className="text-teal-300">{formatTime(taskResult.timing.total_time)}</span></span>
                  <span>文件: <span className="text-teal-300">{taskResult.files.length} 个</span></span>
                </div>
              </div>
              <button
                onClick={() => toggleExpanded(taskResult.file_id)}
                className="ml-4 px-3 py-1 bg-slate-600 hover:bg-slate-500 text-slate-300 text-sm rounded transition-colors"
              >
                {isExpanded ? '收起' : '详情'}
              </button>
            </div>

            {/* 下载按钮 */}
            <div className="flex flex-wrap gap-3 mb-4">
              {srtFile && (
                <button
                  onClick={() => handleDownload(taskResult.file_id, srtFile.filename)}
                  className="flex-1 min-w-[120px] bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-150 ease-in-out text-sm flex items-center justify-center space-x-2"
                >
                  <span>📄</span>
                  <span>下载 SRT</span>
                </button>
              )}
              {vttFile && (
                <button
                  onClick={() => handleDownload(taskResult.file_id, vttFile.filename)}
                  className="flex-1 min-w-[120px] bg-orange-500 hover:bg-orange-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-150 ease-in-out text-sm flex items-center justify-center space-x-2"
                >
                  <span>📄</span>
                  <span>下载 VTT</span>
                </button>
              )}
              {taskResult.files.length === 0 && (
                <div className="text-slate-400 text-sm py-2">
                  暂无可下载文件
                </div>
              )}
            </div>

            {/* 展开的详细信息 */}
            {isExpanded && (
              <div className="border-t border-slate-600 pt-4 space-y-4">
                {/* 转录参数 */}
                <div className="bg-slate-600 p-4 rounded">
                  <h4 className="text-teal-300 font-medium mb-2">转录参数</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    <div>
                      <span className="text-slate-400">模型:</span>
                      <span className="text-white ml-2">{taskResult.transcription_params.model}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">语言:</span>
                      <span className="text-white ml-2">{taskResult.transcription_params.language}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">格式:</span>
                      <span className="text-white ml-2">{taskResult.transcription_params.output_format}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">类型:</span>
                      <span className="text-white ml-2">{taskResult.transcription_params.task_type}</span>
                    </div>
                  </div>
                </div>

                {/* 处理时间 */}
                <div className="bg-slate-600 p-4 rounded">
                  <h4 className="text-teal-300 font-medium mb-2">处理时间</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-slate-400">总耗时:</span>
                      <span className="text-white ml-2">{formatTime(taskResult.timing.total_time)}</span>
                    </div>
                    <div>
                      <span className="text-slate-400">转录耗时:</span>
                      <span className="text-white ml-2">{formatTime(taskResult.timing.transcription_time)}</span>
                    </div>
                  </div>
                </div>

                {/* 生成文件列表 */}
                {taskResult.files.length > 0 && (
                  <div className="bg-slate-600 p-4 rounded">
                    <h4 className="text-teal-300 font-medium mb-2">生成文件</h4>
                    <div className="space-y-2">
                      {taskResult.files.map((file, index) => (
                        <div key={index} className="flex items-center justify-between bg-slate-700 p-2 rounded">
                          <div>
                            <span className="text-white text-sm">{file.filename}</span>
                            <span className="text-slate-400 text-xs ml-2">({file.type.toUpperCase()})</span>
                          </div>
                          <button
                            onClick={() => handleDownload(taskResult.file_id, file.filename)}
                            className="text-teal-400 hover:text-teal-300 text-sm underline"
                          >
                            下载
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 转录文本预览 */}
                {taskResult.full_text && (
                  <div className="bg-slate-600 p-4 rounded">
                    <h4 className="text-teal-300 font-medium mb-2">转录文本预览</h4>
                    <div className="bg-slate-800 p-3 rounded max-h-32 overflow-y-auto">
                      <pre className="text-slate-300 text-sm whitespace-pre-wrap">
                        {taskResult.full_text.length > 500 
                          ? taskResult.full_text.substring(0, 500) + '...' 
                          : taskResult.full_text}
                      </pre>
                    </div>
                    {taskResult.full_text.length > 500 && (
                      <p className="text-slate-400 text-xs mt-2">
                        显示前500字符，完整内容请下载字幕文件查看
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
