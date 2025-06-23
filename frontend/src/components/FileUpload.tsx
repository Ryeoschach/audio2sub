import React, { useState, useCallback } from 'react';
import { audio2subAPI, ModelInfo } from '../services/api';
import ModelSelector from './ModelSelector';
import TranscriptionOptionsComponent, { TranscriptionOptions } from './TranscriptionOptions';

interface FileUploadProps {
  models: ModelInfo[];
  defaultModel: string;
  apiHealthy: boolean;
  onUploadSuccess: (taskId: string, fileId: string, filename: string, model: string) => void;
  setNotification: (message: string, type: 'success' | 'error') => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ 
  models, 
  defaultModel, 
  apiHealthy,
  onUploadSuccess, 
  setNotification 
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedModel, setSelectedModel] = useState(defaultModel);
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
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const getEstimatedTime = (modelName: string): string => {
    const timeMap: Record<string, string> = {
      'tiny': '~30秒',
      'base': '~60秒',
      'small': '~120秒',
      'medium': '~180秒',
      'large-v1': '~300秒',
      'large-v2': '~300秒',
      'large-v3': '~300秒',
      'large-v3-turbo': '~150秒'
    };
    return timeMap[modelName] || '~120秒';
  };

  const handleUpload = useCallback(async () => {
    if (!selectedFile) {
      setNotification('请选择一个文件', 'error');
      return;
    }

    if (!apiHealthy) {
      setNotification('API 服务不可用，请稍后重试', 'error');
      return;
    }

    setIsUploading(true);
    setNotification('', 'success'); // Clear previous notifications

    try {
      const response = await audio2subAPI.uploadFile(selectedFile, {
        model: selectedModel,
        language: options.language,
        output_format: options.output_format,
        task: options.task
      });

      onUploadSuccess(
        response.task_id, 
        response.file_id, 
        selectedFile.name,
        response.model_used
      );

      setNotification(
        `文件 '${selectedFile.name}' 上传成功！使用 ${response.model_used} 模型，预计耗时 ${getEstimatedTime(response.model_used)}`, 
        'success'
      );
      
      // Reset form
      setSelectedFile(null);
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
    } catch (error) {
      console.error('Error uploading file:', error);
      if (error instanceof Error) {
        setNotification(`上传失败: ${error.message}`, 'error');
      } else {
        setNotification('上传失败，请重试', 'error');
      }
    } finally {
      setIsUploading(false);
    }
  }, [selectedFile, selectedModel, options, apiHealthy, onUploadSuccess, setNotification]);

  const isDisabled = !apiHealthy || isUploading || models.length === 0;

  return (
    <div className="bg-slate-700 p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-6 text-teal-300">
        上传音频/视频文件
      </h2>

      {/* 文件选择 */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-300 mb-2">
          选择文件
        </label>
        <input
          type="file"
          onChange={handleFileChange}
          accept="audio/*,video/*"
          disabled={isDisabled}
          className="block w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-teal-500 file:text-white hover:file:bg-teal-600 disabled:opacity-50 disabled:cursor-not-allowed"
        />
        {selectedFile && (
          <div className="mt-2 p-3 bg-slate-600 rounded flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-300 font-medium">{selectedFile.name}</p>
              <p className="text-xs text-slate-400">
                大小: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <button
              onClick={() => setSelectedFile(null)}
              className="text-red-400 hover:text-red-300 text-sm"
            >
              移除
            </button>
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

      {/* 预计处理时间 */}
      {selectedModel && (
        <div className="mb-4 p-3 bg-slate-600 rounded">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-300">预计处理时间:</span>
            <span className="text-teal-300 font-medium">{getEstimatedTime(selectedModel)}</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            实际时间可能因文件大小和内容复杂度而异
          </p>
        </div>
      )}

      {/* 上传按钮 */}
      <button
        onClick={handleUpload}
        disabled={!selectedFile || isDisabled}
        className="w-full bg-gradient-to-r from-blue-500 to-teal-500 hover:from-blue-600 hover:to-teal-600 text-white font-bold py-3 px-4 rounded-lg focus:outline-none focus:shadow-outline transition duration-150 ease-in-out disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isUploading ? (
          <div className="flex items-center justify-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>上传中...</span>
          </div>
        ) : !apiHealthy ? (
          'API 服务不可用'
        ) : !selectedFile ? (
          '请选择文件'
        ) : (
          `使用 ${selectedModel} 模型开始转录`
        )}
      </button>

      {/* 帮助信息 */}
      <div className="mt-4 text-xs text-slate-400">
        <p>支持的格式: MP3, WAV, MP4, AVI, MOV 等音频和视频文件</p>
        <p>建议文件大小不超过 500MB，时长不超过 2 小时</p>
      </div>
    </div>
  );
};

export default FileUpload;
