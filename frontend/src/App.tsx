import { useState, useCallback } from 'react';
import FileUpload from './components/FileUpload';
import BatchFileUpload from './components/BatchFileUpload';
import TranscriptionStatus from './components/TranscriptionStatus';
import BatchTranscriptionStatus from './components/BatchTranscriptionStatus';
import ResultsDisplay from './components/ResultsDisplay';
import BatchResultsDisplay from './components/BatchResultsDisplay';
import APIStatus from './components/APIStatus';
import { ModelsResponse, BatchResultSummary } from './services/api';

// Define types for tasks and results
interface TranscriptionTask {
  taskId: string;
  fileId: string;
  filename: string;
  model: string;
  status: string; // e.g., PENDING, PROGRESS, SUCCESS, FAILURE
  progressMessage?: string;
  result?: TaskResultData; 
  error?: string;
}

interface TaskResultData {
  message: string;
  original_filename: string;
  file_id: string;
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

// 批量任务相关类型
interface BatchTask {
  batchId: string;
  totalFiles: number;
  status: string;
}

interface Notification {
  message: string;
  type: 'success' | 'error' | '';
}

function App() {
  const [activeTasks, setActiveTasks] = useState<TranscriptionTask[]>([]);
  const [completedTaskResults, setCompletedTaskResults] = useState<TaskResultData[]>([]);
  
  // 批量处理状态
  const [activeBatchTasks, setActiveBatchTasks] = useState<BatchTask[]>([]);
  const [completedBatchResults, setCompletedBatchResults] = useState<BatchResultSummary[]>([]);
  const [isBatchMode, setIsBatchMode] = useState(false);
  
  const [notification, setNotification] = useState<Notification>({ message: '', type: '' });
  const [modelsData, setModelsData] = useState<ModelsResponse | null>(null);
  const [apiHealthy, setApiHealthy] = useState(false);

  const handleSetNotification = useCallback((message: string, type: 'success' | 'error') => {
    setNotification({ message, type });
    // Auto-hide notification after 5 seconds
    setTimeout(() => setNotification({ message: '', type: '' }), 5000);
  }, []);

  const handleModelsLoaded = useCallback((models: ModelsResponse) => {
    setModelsData(models);
  }, []);

  const handleHealthStatus = useCallback((isHealthy: boolean) => {
    setApiHealthy(isHealthy);
  }, []);

  const handleUploadSuccess = useCallback((taskId: string, fileId: string, filename: string, model: string) => {
    setActiveTasks(prevTasks => [
      ...prevTasks,
      { 
        taskId, 
        fileId, 
        filename, 
        model,
        status: 'PENDING', 
        progressMessage: '等待处理...' 
      },
    ]);
  }, []);

  const handleTaskCompletion = useCallback((completedTask: TranscriptionTask) => {
    setActiveTasks(prevTasks => prevTasks.filter(task => task.taskId !== completedTask.taskId));
    if (completedTask.status === 'SUCCESS' && completedTask.result) {
      setCompletedTaskResults(prevResults => [
        ...prevResults,
        completedTask.result as TaskResultData
      ]);
    }
    // Notification for completion/failure is handled within TranscriptionStatus component
  }, []);

  // 批量处理相关的处理函数
  const handleBatchUploadSuccess = useCallback((batchId: string, totalFiles: number) => {
    setActiveBatchTasks(prevTasks => [
      ...prevTasks,
      { 
        batchId, 
        totalFiles,
        status: 'PROCESSING'
      },
    ]);
  }, []);

  const handleBatchTaskCompletion = useCallback((batchId: string, results: BatchResultSummary) => {
    setActiveBatchTasks(prevTasks => prevTasks.filter(task => task.batchId !== batchId));
    setCompletedBatchResults(prevResults => [
      results,
      ...prevResults
    ]);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-700 text-white p-4 flex flex-col items-center font-sans">
      <header className="w-full max-w-6xl py-8">
        <h1 className="text-5xl font-bold text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-teal-300 to-green-300">
          Audio2Sub
        </h1>
        <p className="text-center text-slate-300 mt-2 text-lg">
          智能音频转录平台 - 支持多种模型动态选择
        </p>
      </header>

      <main className="w-full max-w-6xl">
        {/* API 状态检查 */}
        <APIStatus 
          onModelsLoaded={handleModelsLoaded}
          onHealthStatus={handleHealthStatus}
        />

        {/* 通知信息 */}
        {notification.message && (
          <div 
            className={`w-full p-4 mb-6 rounded-md text-center font-medium 
              ${notification.type === 'success' ? 'bg-green-500 text-white' : ''}
              ${notification.type === 'error' ? 'bg-red-500 text-white' : ''}
            `}
          >
            {notification.message}
          </div>
        )}

        {/* 主要内容区域 */}
        <div className="bg-slate-800 shadow-2xl rounded-lg p-6 md:p-10 mb-6">
          {/* 模式切换 */}
          {modelsData && (
            <div className="mb-6 flex justify-center">
              <div className="bg-slate-700 p-1 rounded-lg flex">
                <button
                  onClick={() => setIsBatchMode(false)}
                  className={`px-4 py-2 rounded-md font-medium transition-colors ${
                    !isBatchMode 
                      ? 'bg-teal-500 text-white' 
                      : 'text-slate-300 hover:text-white'
                  }`}
                >
                  📄 单文件模式
                </button>
                <button
                  onClick={() => setIsBatchMode(true)}
                  className={`px-4 py-2 rounded-md font-medium transition-colors ${
                    isBatchMode 
                      ? 'bg-teal-500 text-white' 
                      : 'text-slate-300 hover:text-white'
                  }`}
                >
                  📁 批量模式
                </button>
              </div>
            </div>
          )}

          {/* 文件上传组件 */}
          {modelsData && (
            <>
              {!isBatchMode ? (
                <FileUpload
                  models={modelsData.models}
                  defaultModel={modelsData.default_model}
                  apiHealthy={apiHealthy}
                  onUploadSuccess={handleUploadSuccess}
                  setNotification={handleSetNotification}
                />
              ) : (
                <BatchFileUpload
                  models={modelsData.models}
                  defaultModel={modelsData.default_model}
                  apiHealthy={apiHealthy}
                  onBatchUploadSuccess={handleBatchUploadSuccess}
                  setNotification={handleSetNotification}
                />
              )}
            </>
          )}

          {/* 处理中的任务监控 */}
          {!isBatchMode ? (
            /* 单文件任务监控 */
            activeTasks.length > 0 && (
              <div className="mt-8">
                <h3 className="text-xl font-semibold text-teal-300 mb-4">
                  处理中的任务 ({activeTasks.length})
                </h3>
                <TranscriptionStatus 
                  tasks={activeTasks} 
                  onTaskCompletion={handleTaskCompletion} 
                  setNotification={handleSetNotification} 
                />
              </div>
            )
          ) : (
            /* 批量任务监控 */
            activeBatchTasks.length > 0 && (
              <div className="mt-8">
                <h3 className="text-xl font-semibold text-teal-300 mb-4">
                  批量任务监控 ({activeBatchTasks.length})
                </h3>
                <div className="space-y-4">
                  {activeBatchTasks.map((batchTask) => (
                    <BatchTranscriptionStatus
                      key={batchTask.batchId}
                      batchId={batchTask.batchId}
                      onBatchComplete={handleBatchTaskCompletion}
                      setNotification={handleSetNotification}
                    />
                  ))}
                </div>
              </div>
            )
          )}

          {/* 转录结果展示 */}
          {!isBatchMode ? (
            /* 单文件结果 */
            completedTaskResults.length > 0 && (
              <div className="mt-8">
                <h3 className="text-xl font-semibold text-teal-300 mb-4">
                  转录结果 ({completedTaskResults.length})
                </h3>
                <ResultsDisplay completedTasksData={completedTaskResults} />
              </div>
            )
          ) : (
            /* 批量结果 */
            completedBatchResults.length > 0 && (
              <div className="mt-8">
                <BatchResultsDisplay 
                  batchResults={completedBatchResults}
                  setNotification={handleSetNotification}
                />
              </div>
            )
          )}

          {/* 空状态提示 */}
          {!apiHealthy && (
            <div className="text-center py-12 text-slate-400">
              <p className="text-lg mb-2">⚠️ API 服务连接失败</p>
              <p>请确保后端服务正在运行</p>
            </div>
          )}

          {apiHealthy && 
           activeTasks.length === 0 && 
           completedTaskResults.length === 0 &&
           activeBatchTasks.length === 0 && 
           completedBatchResults.length === 0 && (
            <div className="text-center py-12 text-slate-400">
              <p className="text-lg mb-2">🎵 准备开始转录</p>
              <p>选择{isBatchMode ? '多个' : ''}音频或视频文件，配置转录选项，然后开始处理</p>
            </div>
          )}
        </div>

        {/* 功能特点说明 */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-slate-800 p-6 rounded-lg text-center">
            <div className="text-3xl mb-3">🚀</div>
            <h3 className="text-lg font-semibold text-teal-300 mb-2">多模型支持</h3>
            <p className="text-slate-400 text-sm">
              从快速的 tiny 模型到高精度的 large-v3-turbo，根据需求选择最合适的模型
            </p>
          </div>
          <div className="bg-slate-800 p-6 rounded-lg text-center">
            <div className="text-3xl mb-3">📁</div>
            <h3 className="text-lg font-semibold text-teal-300 mb-2">批量处理</h3>
            <p className="text-slate-400 text-sm">
              支持同时上传多个文件进行批量转录，可配置并发数量，提高工作效率
            </p>
          </div>
          <div className="bg-slate-800 p-6 rounded-lg text-center">
            <div className="text-3xl mb-3">🌍</div>
            <h3 className="text-lg font-semibold text-teal-300 mb-2">多语言识别</h3>
            <p className="text-slate-400 text-sm">
              支持中文、英文、日文等多种语言的自动识别和转录
            </p>
          </div>
          <div className="bg-slate-800 p-6 rounded-lg text-center">
            <div className="text-3xl mb-3">📄</div>
            <h3 className="text-lg font-semibold text-teal-300 mb-2">多格式输出</h3>
            <p className="text-slate-400 text-sm">
              支持 SRT 和 VTT 字幕格式，可按需选择或同时生成
            </p>
          </div>
        </div>
      </main>

      <footer className="w-full max-w-6xl text-center py-8 text-slate-400">
        <p>&copy; {new Date().getFullYear()} Audio2Sub. 基于 React + FastAPI + Whisper 构建</p>
      </footer>
    </div>
  );
}

export default App;
