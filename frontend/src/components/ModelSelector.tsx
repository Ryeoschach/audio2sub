import React, { useState } from 'react';
import { ModelInfo } from '../services/api';

interface ModelSelectorProps {
  models: ModelInfo[];
  selectedModel: string;
  onModelChange: (model: string) => void;
  disabled?: boolean;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({
  models,
  selectedModel,
  onModelChange,
  disabled = false
}) => {
  const [showDetails, setShowDetails] = useState(false);

  const selectedModelInfo = models.find(m => m.name === selectedModel);

  return (
    <div className="mb-6">
      <label className="block text-sm font-medium text-theme-primary mb-3 flex items-center gap-2">
        🤖 选择AI模型
        <button
          type="button"
          onClick={() => setShowDetails(!showDetails)}
          className="ml-2 bg-gradient-to-r from-blue-500/20 to-purple-500/20 hover:from-blue-500/30 hover:to-purple-500/30 text-blue-300 px-2 py-1 rounded border border-blue-400/30 text-xs transition-all duration-300"
        >
          {showDetails ? '🔽 隐藏详情' : '🔍 查看详情'}
        </button>
      </label>
      
      <select
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value)}
        disabled={disabled}
        className="w-full px-4 py-3 bg-theme-card border border-theme-border rounded-xl text-theme-primary focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400/50 disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-sm transition-all duration-300 hover:bg-theme-hover"
      >
        {models.map((model) => (
          <option key={model.name} value={model.name} className="bg-gray-800 dark:bg-slate-800 text-gray-900 dark:text-white">
            {model.name} - {model.use_case} ({model.size})
          </option>
        ))}
      </select>

      {selectedModelInfo && (
        <div className="mt-4 p-4 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-xl border border-purple-400/20 backdrop-blur-sm">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-2xl">🎯</span>
            <span className="text-purple-300 font-medium">当前选择: {selectedModelInfo.name}</span>
          </div>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div className="bg-theme-card p-2 rounded border border-theme-border text-center">
              <div className="text-theme-secondary text-xs">📏 大小</div>
              <div className="text-theme-primary font-bold">{selectedModelInfo.size}</div>
            </div>
            <div className="bg-theme-card p-2 rounded border border-theme-border text-center">
              <div className="text-theme-secondary text-xs">⚡ 速度</div>
              <div className="text-theme-primary font-bold">{selectedModelInfo.speed}</div>
            </div>
            <div className="bg-theme-card p-2 rounded border border-theme-border text-center">
              <div className="text-theme-secondary text-xs">🎯 准确度</div>
              <div className="text-theme-primary font-bold">{selectedModelInfo.accuracy}</div>
            </div>
          </div>
          <p className="text-theme-secondary text-sm mt-3 italic flex items-center gap-2">
            💡 {selectedModelInfo.use_case}
          </p>
        </div>
      )}

      {showDetails && (
        <div className="mt-6 bg-theme-card rounded-xl p-6 border border-theme-border">
          <h4 className="text-blue-300 font-bold mb-4 flex items-center gap-2">
            🔬 所有可用模型对比
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {models.map((model) => (
              <div
                key={model.name}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all duration-300 hover:scale-105 ${
                  model.name === selectedModel
                    ? 'border-purple-400/50 bg-gradient-to-r from-purple-500/20 to-pink-500/20 shadow-lg'
                    : 'border-theme-border bg-theme-card hover:border-gray-400 dark:hover:border-gray-500 hover:bg-theme-hover'
                }`}
                onClick={() => !disabled && onModelChange(model.name)}
              >
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">
                      {model.name === selectedModel ? '🎯' : '🤖'}
                    </span>
                    <span className="font-bold text-theme-primary">{model.name}</span>
                  </div>
                  <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-white text-xs px-2 py-1 rounded-full">
                    {model.size}
                  </span>
                </div>
                
                <div className="space-y-2 mb-3">
                  <div className="flex justify-between text-xs">
                    <span className="text-theme-secondary">⚡ 速度:</span>
                    <span className="text-theme-primary font-medium">{model.speed}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-theme-secondary">🎯 准确度:</span>
                    <span className="text-theme-primary font-medium">{model.accuracy}</span>
                  </div>
                </div>
                
                <div className="text-xs text-theme-secondary bg-theme-card p-2 rounded border border-theme-border">
                  💡 {model.use_case}
                </div>
                
                {model.name === selectedModel && (
                  <div className="mt-2 text-center">
                    <span className="bg-gradient-to-r from-green-400 to-emerald-400 text-gray-900 text-xs px-3 py-1 rounded-full font-bold">
                      ✅ 当前选择
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelSelector;
