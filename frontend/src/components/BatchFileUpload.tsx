import React, { useState, useCallback } from 'react';
import { audio2subAPI, ModelInfo, BatchUploadRequest } from '../services/api';
import ModelSelector from './ModelSelector';
import TranscriptionOptionsComponent, { TranscriptionOptions } from './TranscriptionOptions';

interface BatchFileUploadProps {
  models: ModelInfo[];
  defaultModel: string;
  apiHealthy: boolean;
  onBatchUploadSuccess: (batchId: string, totalFiles: number) => void;
  setNotification: (message: string, type: 'success' | 'error') => void;
}

const BatchFileUpload: React.FC<BatchFileUploadProps> = ({ 
  models, 
  defaultModel, 
  apiHealthy,
  onBatchUploadSuccess, 
  setNotification 
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedModel, setSelectedModel] = useState(defaultModel);
  const [concurrentLimit, setConcurrentLimit] = useState(3);

  // 智能默认语言检测
  const getDefaultLanguage = () => {
    const browserLang = navigator.language.toLowerCase();
    if (browserLang.includes('zh')) {
      return 'zh';
    } else if (browserLang.includes('en')) {
      return 'en';
    }
    return 'auto';
  };

  const [options, setOptions] = useState<TranscriptionOptions>({
    language: getDefaultLanguage(),
    output_format: 'both',
    task: 'transcribe'
  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      const files = Array.from(event.target.files);
      setSelectedFiles(files);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const getEstimatedTime = (modelName: string, fileCount: number): string => {
    const timeMap: Record<string, number> = {
      'tiny': 30,
      'base': 60,
      'small': 120,
      'medium': 180,
      'large-v1': 300,
      'large-v2': 300,
      'large-v3': 300,
      'large-v3-turbo': 150
    };
    const singleFileTime = timeMap[modelName] || 120;
    const totalTime = Math.ceil(fileCount / concurrentLimit) * singleFileTime;
    return `~${Math.ceil(totalTime / 60)}分钟`;
  };

  const handleBatchUpload = useCallback(async () => {
    if (!selectedFiles.length) {
      setNotification('请选择至少一个文件', 'error');
      return;
    }

    if (selectedFiles.length > 50) {
      setNotification('最多只能同时上传50个文件', 'error');
      return;
    }

    if (!apiHealthy) {
      setNotification('API 服务不可用，请稍后重试', 'error');
      return;
    }

    setIsUploading(true);
    setNotification('', 'success'); // Clear previous notifications

    try {
      const batchOptions: BatchUploadRequest = {
        model: selectedModel,
        language: options.language,
        output_format: options.output_format,
        task: options.task,
        concurrent_limit: concurrentLimit
      };

      const response = await audio2subAPI.uploadFiles(selectedFiles, batchOptions);

      onBatchUploadSuccess(response.batch_id, response.total_files);

      setNotification(
        `批量任务创建成功！共 ${response.total_files} 个文件，使用 ${response.model_used} 模型，预计耗时 ${getEstimatedTime(response.model_used, response.total_files)}`, 
        'success'
      );
      
      // Reset form
      setSelectedFiles([]);
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
    } catch (error) {
      console.error('Error uploading files:', error);
      if (error instanceof Error) {
        setNotification(`批量上传失败: ${error.message}`, 'error');
      } else {
        setNotification('批量上传失败，请重试', 'error');
      }
    } finally {
      setIsUploading(false);
    }
  }, [selectedFiles, selectedModel, options, concurrentLimit, apiHealthy, onBatchUploadSuccess, setNotification]);

  const isDisabled = !apiHealthy || isUploading || models.length === 0;

  return (
    <div className="bg-slate-700 p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-6 text-teal-300">
        批量上传音频/视频文件
      </h2>

      {/* 文件选择 */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          选择多个文件 (最多50个)
        </label>
        <input
          type="file"
          onChange={handleFileChange}
          accept="audio/*,video/*"
          multiple
          disabled={isDisabled}
          className="w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100 disabled:opacity-50 disabled:cursor-not-allowed"
        />
        
        {/* 显示选中的文件列表 */}
        {selectedFiles.length > 0 && (
          <div className="mt-4 p-4 bg-slate-600 rounded-lg">
            <p className="text-sm text-slate-300 mb-2">已选择 {selectedFiles.length} 个文件:</p>
            <div className="max-h-32 overflow-y-auto space-y-1">
              {selectedFiles.map((file, index) => (
                <div key={index} className="flex justify-between items-center text-xs bg-slate-500 p-2 rounded">
                  <span className="text-slate-200 truncate flex-1 mr-2">{file.name}</span>
                  <span className="text-slate-400 mr-2">({(file.size / 1024 / 1024).toFixed(1)}MB)</span>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-red-400 hover:text-red-300 ml-2"
                    disabled={isUploading}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 模型选择 */}
      {models.length > 0 && (
        <ModelSelector
          models={models}
          selectedModel={selectedModel}
          onModelChange={setSelectedModel}
          disabled={isDisabled}
        />
      )}

      {/* 转录选项 */}
      <TranscriptionOptionsComponent
        options={options}
        onOptionsChange={setOptions}
        disabled={isDisabled}
      />

      {/* 并发限制设置 */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          并发处理数量: {concurrentLimit}
        </label>
        <input
          type="range"
          min="1"
          max="10"
          value={concurrentLimit}
          onChange={(e) => setConcurrentLimit(parseInt(e.target.value))}
          disabled={isDisabled}
          className="w-full h-2 bg-slate-600 rounded-lg appearance-none cursor-pointer disabled:opacity-50"
        />
        <div className="flex justify-between text-xs text-slate-400 mt-1">
          <span>1 (慢但稳定)</span>
          <span>10 (快但占用资源多)</span>
        </div>
      </div>

      {/* 预计处理时间 */}
      {selectedModel && selectedFiles.length > 0 && (
        <div className="mb-4 p-3 bg-slate-600 rounded">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-300">预计总处理时间:</span>
            <span className="text-teal-300 font-medium">{getEstimatedTime(selectedModel, selectedFiles.length)}</span>
          </div>
          <div className="flex items-center justify-between text-sm mt-1">
            <span className="text-slate-400">并发数量:</span>
            <span className="text-slate-400">{concurrentLimit} 个文件同时处理</span>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            实际时间可能因文件大小和内容复杂度而异
          </p>
        </div>
      )}

      {/* 上传按钮 */}
      <button
        onClick={handleBatchUpload}
        disabled={!selectedFiles.length || isDisabled}
        className="w-full bg-gradient-to-r from-blue-500 to-teal-500 hover:from-blue-600 hover:to-teal-600 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isUploading ? (
          <div className="flex items-center justify-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>批量上传中...</span>
          </div>
        ) : !apiHealthy ? (
          'API 服务不可用'
        ) : !selectedFiles.length ? (
          '请选择文件'
        ) : (
          `批量转录 ${selectedFiles.length} 个文件`
        )}
      </button>

      {/* 帮助信息 */}
      <div className="mt-4 text-xs text-slate-400">
        <p>支持的格式: MP3, WAV, MP4, AVI, MOV 等音频和视频文件</p>
        <p>建议单个文件大小不超过 500MB，时长不超过 2 小时</p>
        <p>批量处理会按设定的并发数量同时处理多个文件，提高整体效率</p>
      </div>
    </div>
  );
};

export default BatchFileUpload;
