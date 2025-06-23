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
    <div className="glass-effect p-8 rounded-2xl shadow-xl border border-white/20 dark:border-gray-700">
      <div className="flex items-center mb-6">
        <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center mr-4">
          <span className="text-white text-xl">📁</span>
        </div>
        <h2 className="text-2xl font-bold text-theme-primary">
          上传音频/视频文件
        </h2>
      </div>

      {/* 文件拖拽上传区域 */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-theme-secondary mb-3">
          选择文件
        </label>
        <div className="relative">
          <input
            type="file"
            onChange={handleFileChange}
            accept="audio/*,video/*"
            disabled={isDisabled}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          />
          <div className={`
            border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300
            ${selectedFile 
              ? 'border-green-400 bg-green-500/10 dark:bg-green-900/30' 
              : 'border-gray-300 dark:border-gray-500 bg-theme-card hover:border-blue-400 hover:bg-blue-500/10 dark:hover:bg-blue-900/30'
            }
            ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          `}>
            {selectedFile ? (
              <div className="flex items-center justify-center space-x-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-xl">✓</span>
                  </div>
                </div>
                <div className="flex-1 text-left">
                  <p className="font-medium text-theme-primary">{selectedFile.name}</p>
                  <p className="text-sm text-theme-secondary">
                    大小: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                  }}
                  className="text-red-400 hover:text-red-300 p-2 rounded-full hover:bg-red-500/20 dark:hover:bg-red-900/30 transition-colors"
                >
                  ✕
                </button>
              </div>
            ) : (
              <div>
                <div className="text-4xl mb-3">📁</div>
                <p className="text-lg font-medium text-theme-primary mb-2">
                  点击选择文件或拖拽文件到此处
                </p>
                <p className="text-sm text-theme-secondary">
                  支持音频和视频文件格式
                </p>
                <div className="mt-4">
                  <div className="inline-flex px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 transition-all duration-300 shadow-lg">
                    📁 选择文件
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
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
        <div className="mb-6 p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 dark:from-blue-900/30 dark:to-purple-900/30 rounded-xl border border-blue-500/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-2xl mr-3">⏱️</span>
              <div>
                <p className="text-sm font-medium text-theme-primary">预计处理时间</p>
                <p className="text-xs text-theme-secondary">实际时间可能因文件大小和内容复杂度而异</p>
              </div>
            </div>
            <span className="text-lg font-bold text-blue-400">{getEstimatedTime(selectedModel)}</span>
          </div>
        </div>
      )}

      {/* 上传按钮 */}
      <button
        onClick={handleUpload}
        disabled={!selectedFile || isDisabled}
        className="w-full btn-gradient-primary py-4 px-6 rounded-xl font-bold text-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-800"
      >
        {isUploading ? (
          <div className="flex items-center justify-center space-x-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            <span>🚀 上传中...</span>
          </div>
        ) : !apiHealthy ? (
          '❌ API 服务不可用'
        ) : !selectedFile ? (
          '📁 请选择文件'
        ) : (
          `🎯 使用 ${selectedModel} 模型开始转录`
        )}
      </button>

      {/* 帮助信息 */}
      <div className="mt-6 p-4 bg-theme-card rounded-lg border border-theme-border">
        <div className="flex items-start">
          <span className="text-lg mr-2">💡</span>
          <div className="text-xs text-theme-secondary">
            <p className="font-medium mb-1 text-theme-primary">支持格式:</p>
            <p className="mb-2">MP3, WAV, FLAC, MP4, AVI, MOV 等音频和视频文件</p>
            <p className="font-medium mb-1 text-theme-primary">建议规范:</p>
            <p>文件大小不超过 500MB，时长不超过 2 小时</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
