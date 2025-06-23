import { useState, useCallback } from 'react';
import FileUpload from './components/FileUpload';
import BatchFileUpload from './components/BatchFileUpload';
import TranscriptionStatus from './components/TranscriptionStatus';
import BatchTranscriptionStatus from './components/BatchTranscriptionStatus';
import ResultsDisplay from './components/ResultsDisplay';
import BatchResultsDisplay from './components/BatchResultsDisplay';
import APIStatus from './components/APIStatus';
import ThemeToggle from './components/ThemeToggle';
import { ThemeProvider } from './contexts/ThemeContext';
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
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors duration-300 p-4">
      <div className="container mx-auto max-w-6xl">
        {/* 头部区域 */}
        <div className="text-center mb-8 relative">
          {/* 主题切换按钮 - 右上角 */}
          <div className="absolute top-0 right-0">
            <ThemeToggle />
          </div>
          
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-2 drop-shadow-lg">
            Audio<span className="text-yellow-500 dark:text-yellow-300">2</span>Sub
          </h1>
          <p className="text-xl text-gray-700 dark:text-purple-100 font-medium">
            AI驱动的音频转字幕工具
          </p>
          <div className="mt-4 flex justify-center">
            <div className="h-1 w-24 bg-gradient-to-r from-yellow-400 to-pink-400 rounded-full"></div>
          </div>
        </div>

        {/* API状态组件 */}
        <div className="mb-6">
          <APIStatus 
            onModelsLoaded={handleModelsLoaded}
            onHealthStatus={handleHealthStatus}
          />
        </div>

        {/* 通知显示 */}
        {notification.message && (
          <div
            className={`w-full p-4 mb-6 rounded-xl text-center font-medium transition-all duration-300 transform
              ${notification.type === 'success' 
                ? 'bg-gradient-to-r from-green-400 to-blue-500 text-white shadow-lg' 
                : ''
              }
              ${notification.type === 'error' 
                ? 'bg-gradient-to-r from-red-400 to-pink-500 text-white shadow-lg' 
                : ''
              }
            `}
          >
            <div className="flex items-center justify-center">
              <span className="mr-2">
                {notification.type === 'success' ? '✅' : '❌'}
              </span>
              {notification.message}
            </div>
          </div>
        )}

        {/* 主要内容区域 */}
        <div className="bg-white dark:bg-gray-800 p-8 mb-6 shadow-2xl rounded-2xl border border-gray-200 dark:border-gray-700 transition-colors duration-300">
          {/* 模式切换 */}
          {modelsData && (
            <div className="mb-8 flex justify-center">
              <div className="bg-gray-200 dark:bg-gray-700 p-1 rounded-2xl flex shadow-lg border border-gray-300 dark:border-gray-600 transition-colors duration-300">
                <button
                  onClick={() => setIsBatchMode(false)}
                  className={`px-6 py-3 rounded-xl font-medium transition-all duration-300 flex items-center ${
                    !isBatchMode 
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg transform scale-105' 
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  <span className="mr-2">📄</span>
                  单文件模式
                </button>
                <button
                  onClick={() => setIsBatchMode(true)}
                  className={`px-6 py-3 rounded-xl font-medium transition-all duration-300 flex items-center ${
                    isBatchMode 
                      ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white shadow-lg transform scale-105' 
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  <span className="mr-2">📁</span>
                  批量模式
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
              <div className="mt-8 p-6 bg-gray-100 dark:bg-gray-700/50 rounded-xl border border-blue-300 dark:border-blue-500/30 transition-colors duration-300">
                <h3 className="text-xl font-semibold text-blue-600 dark:text-blue-400 mb-4 flex items-center">
                  <span className="mr-2">⚡</span>
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
              <div className="mt-8 p-6 bg-gray-100 dark:bg-gray-700/50 rounded-xl border border-purple-300 dark:border-purple-500/30 transition-colors duration-300">
                <h3 className="text-xl font-semibold text-purple-600 dark:text-purple-400 mb-4 flex items-center">
                  <span className="mr-2">🔄</span>
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
              <div className="mt-8 p-6 bg-gray-50 dark:bg-gray-700/50 rounded-xl border border-green-400 dark:border-green-500/30 transition-colors duration-300">
                <h3 className="text-xl font-semibold text-green-600 dark:text-green-400 mb-4 flex items-center">
                  <span className="mr-2">✨</span>
                  转录结果 ({completedTaskResults.length})
                </h3>
                <ResultsDisplay completedTasksData={completedTaskResults} />
              </div>
            )
          ) : (
            /* 批量结果 */
            completedBatchResults.length > 0 && (
              <div className="mt-8 p-6 bg-gray-50 dark:bg-gray-700/50 rounded-xl border border-emerald-400 dark:border-emerald-500/30 transition-colors duration-300">
                <h3 className="text-xl font-semibold text-emerald-600 dark:text-emerald-400 mb-4 flex items-center">
                  <span className="mr-2">🎯</span>
                  批量处理结果
                </h3>
                <BatchResultsDisplay 
                  batchResults={completedBatchResults}
                  setNotification={handleSetNotification}
                />
              </div>
            )
          )}

          {/* 空状态提示 */}
          {!apiHealthy && (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <div className="text-4xl mb-4">⚠️</div>
              <p className="text-lg mb-2 font-medium">API 服务连接失败</p>
              <p className="text-sm">请确保后端服务正在运行</p>
            </div>
          )}

          {apiHealthy && 
           activeTasks.length === 0 && 
           completedTaskResults.length === 0 &&
           activeBatchTasks.length === 0 && 
           completedBatchResults.length === 0 && (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <div className="text-4xl mb-4">🎵</div>
              <p className="text-lg mb-2 font-medium text-gray-800 dark:text-white">准备开始转录</p>
              <p className="text-sm">选择{isBatchMode ? '多个' : ''}音频或视频文件，配置转录选项，然后开始处理</p>
            </div>
          )}
        </div>

        {/* 功能特点说明 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-6 text-center group hover:transform hover:scale-105 transition-all duration-300 rounded-2xl shadow-xl">
            <div className="text-4xl mb-4 transform group-hover:scale-110 transition-transform duration-300">🚀</div>
            <h3 className="text-lg font-semibold text-blue-600 dark:text-blue-400 mb-3">多模型支持</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              从快速的 tiny 模型到高精度的 large-v3-turbo，根据需求选择最合适的模型
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-6 text-center group hover:transform hover:scale-105 transition-all duration-300 rounded-2xl shadow-xl">
            <div className="text-4xl mb-4 transform group-hover:scale-110 transition-transform duration-300">📁</div>
            <h3 className="text-lg font-semibold text-purple-600 dark:text-purple-400 mb-3">批量处理</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              支持同时上传多个文件进行批量转录，可配置并发数量，提高工作效率
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-6 text-center group hover:transform hover:scale-105 transition-all duration-300 rounded-2xl shadow-xl">
            <div className="text-4xl mb-4 transform group-hover:scale-110 transition-transform duration-300">🌍</div>
            <h3 className="text-lg font-semibold text-green-600 dark:text-green-400 mb-3">多语言识别</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              支持中文、英文、日文等多种语言的自动识别和转录
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-6 text-center group hover:transform hover:scale-105 transition-all duration-300 rounded-2xl shadow-xl">
            <div className="text-4xl mb-4 transform group-hover:scale-110 transition-transform duration-300">📄</div>
            <h3 className="text-lg font-semibold text-pink-600 dark:text-pink-400 mb-3">多格式输出</h3>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              支持 SRT 和 VTT 字幕格式，可按需选择或同时生成
            </p>
          </div>
        </div>

        {/* 底部装饰 */}
        <div className="text-center py-8">
          <div className="inline-flex items-center px-6 py-3 rounded-full bg-gray-800 dark:bg-gray-200 border border-gray-600 dark:border-gray-400 text-gray-300 dark:text-gray-700 transition-colors duration-300">
            <span className="mr-2">⚡</span>
            基于 React + FastAPI + Whisper 构建
            <span className="ml-2">⚡</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// 包装App组件以提供主题功能
const AppWithTheme: React.FC = () => {
  return (
    <ThemeProvider>
      <App />
    </ThemeProvider>
  );
};

export default AppWithTheme;
