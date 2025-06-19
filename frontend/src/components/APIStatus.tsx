import React, { useState, useEffect } from 'react';
import { audio2subAPI, HealthStatus, ModelsResponse } from '../services/api';

interface APIStatusProps {
  onModelsLoaded: (models: ModelsResponse) => void;
  onHealthStatus: (isHealthy: boolean) => void;
}

const APIStatus: React.FC<APIStatusProps> = ({ onModelsLoaded, onHealthStatus }) => {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [modelsData, setModelsData] = useState<ModelsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkAPIStatus = async () => {
    setLoading(true);
    setError(null);

    try {
      // 并行检查健康状态和模型列表
      const [healthResult, modelsResult] = await Promise.all([
        audio2subAPI.healthCheck(),
        audio2subAPI.getModels()
      ]);

      setHealthStatus(healthResult);
      setModelsData(modelsResult);

      const isHealthy = healthResult.status === 'healthy';
      onHealthStatus(isHealthy);
      onModelsLoaded(modelsResult);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'API 连接失败';
      setError(errorMessage);
      onHealthStatus(false);
      console.error('API status check failed:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAPIStatus();
  }, []);

  const getStatusColor = () => {
    if (loading) return 'bg-yellow-500';
    if (error) return 'bg-red-500';
    if (healthStatus?.status === 'healthy') return 'bg-green-500';
    return 'bg-orange-500';
  };

  const getStatusText = () => {
    if (loading) return '检查中...';
    if (error) return 'API 连接失败';
    if (healthStatus?.status === 'healthy') return 'API 服务正常';
    return 'API 服务异常';
  };

  return (
    <div className="bg-slate-700 p-4 rounded-lg mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${getStatusColor()}`}></div>
          <span className="text-slate-300 font-medium">{getStatusText()}</span>
          {modelsData && (
            <span className="text-slate-400 text-sm">
              ({modelsData.models.length} 个模型可用)
            </span>
          )}
        </div>
        <button
          onClick={checkAPIStatus}
          disabled={loading}
          className="px-3 py-1 bg-slate-600 hover:bg-slate-500 text-slate-300 text-sm rounded transition-colors disabled:opacity-50"
        >
          {loading ? '检查中...' : '重新检查'}
        </button>
      </div>

      {error && (
        <div className="mt-3 p-3 bg-red-900/30 border border-red-500/50 rounded text-red-200 text-sm">
          <p className="font-medium">连接错误:</p>
          <p>{error}</p>
          <p className="mt-1 text-red-300">
            请确保后端服务正在运行：<code className="bg-red-800/50 px-1 rounded">uvicorn app.main:app --reload</code>
          </p>
        </div>
      )}

      {healthStatus && !error && (
        <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <div className="bg-slate-600 p-2 rounded">
            <span className="text-slate-400">部署模式:</span>
            <span className="text-white ml-2">{healthStatus.deployment?.mode || 'N/A'}</span>
          </div>
          <div className="bg-slate-600 p-2 rounded">
            <span className="text-slate-400">设备:</span>
            <span className="text-white ml-2">{healthStatus.deployment?.device || 'N/A'}</span>
          </div>
          <div className="bg-slate-600 p-2 rounded">
            <span className="text-slate-400">Redis:</span>
            <span className="text-white ml-2">
              {healthStatus.redis?.includes('connected') ? '已连接' : '未连接'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default APIStatus;
