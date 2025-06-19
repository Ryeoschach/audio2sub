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
    <div className="mb-4">
      <label className="block text-sm font-medium text-slate-300 mb-2">
        选择模型 
        <button
          type="button"
          onClick={() => setShowDetails(!showDetails)}
          className="ml-2 text-teal-400 hover:text-teal-300 text-xs underline"
        >
          {showDetails ? '隐藏详情' : '查看详情'}
        </button>
      </label>
      
      <select
        value={selectedModel}
        onChange={(e) => onModelChange(e.target.value)}
        disabled={disabled}
        className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {models.map((model) => (
          <option key={model.name} value={model.name}>
            {model.name} - {model.use_case} ({model.size})
          </option>
        ))}
      </select>

      {selectedModelInfo && (
        <div className="mt-2 p-3 bg-slate-600 rounded-md">
          <div className="flex flex-wrap gap-4 text-sm">
            <span className="text-slate-300">
              <strong className="text-teal-300">大小:</strong> {selectedModelInfo.size}
            </span>
            <span className="text-slate-300">
              <strong className="text-teal-300">速度:</strong> {selectedModelInfo.speed}
            </span>
            <span className="text-slate-300">
              <strong className="text-teal-300">准确度:</strong> {selectedModelInfo.accuracy}
            </span>
          </div>
          <p className="text-slate-400 text-sm mt-1">
            {selectedModelInfo.use_case}
          </p>
        </div>
      )}

      {showDetails && (
        <div className="mt-4 bg-slate-700 rounded-md p-4">
          <h4 className="text-teal-300 font-medium mb-3">所有可用模型对比</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {models.map((model) => (
              <div
                key={model.name}
                className={`p-3 rounded-md border-2 cursor-pointer transition-all ${
                  model.name === selectedModel
                    ? 'border-teal-500 bg-slate-600'
                    : 'border-slate-600 bg-slate-800 hover:border-slate-500'
                }`}
                onClick={() => !disabled && onModelChange(model.name)}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="font-medium text-white">{model.name}</span>
                  <span className="text-xs text-slate-400">{model.size}</span>
                </div>
                <div className="text-xs text-slate-400 mb-1">
                  速度: {model.speed} | 准确度: {model.accuracy}
                </div>
                <div className="text-xs text-slate-300">{model.use_case}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelSelector;
