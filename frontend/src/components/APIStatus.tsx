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
    if (loading) return 'from-yellow-400 to-orange-400';
    if (error) return 'from-red-400 to-pink-400';
    if (healthStatus?.status === 'healthy') return 'from-green-400 to-emerald-400';
    return 'from-orange-400 to-red-400';
  };

  const getStatusIcon = () => {
    if (loading) return '🔄';
    if (error) return '❌';
    if (healthStatus?.status === 'healthy') return '✅';
    return '⚠️';
  };

  const getStatusText = () => {
    if (loading) return '正在检查API状态...';
    if (error) return 'API 连接失败';
    if (healthStatus?.status === 'healthy') return 'API 服务运行正常';
    return 'API 服务异常';
  };

  return (
    <div className="glass-effect p-6 rounded-xl shadow-xl border border-white/20 mb-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`w-4 h-4 rounded-full bg-gradient-to-r ${getStatusColor()} shadow-lg ${loading ? 'animate-pulse' : ''}`}></div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">{getStatusIcon()}</span>
            <span className="text-theme-primary font-medium">{getStatusText()}</span>
          </div>
          {modelsData && (
            <span className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 px-3 py-1 rounded-full border border-purple-400/30 text-purple-300 text-sm">
              🤖 {modelsData.models.length} 个模型可用
            </span>
          )}
        </div>
        <button
          onClick={checkAPIStatus}
          disabled={loading}
          className="px-4 py-2 bg-gradient-to-r from-blue-500/20 to-purple-500/20 hover:from-blue-500/30 hover:to-purple-500/30 text-white border border-blue-400/30 rounded-lg transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>检查中...</span>
            </>
          ) : (
            <>
              🔄 <span>重新检查</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-gradient-to-r from-red-500/20 to-pink-500/20 border border-red-400/30 rounded-xl backdrop-blur-sm">
          <div className="flex items-start gap-3">
            <span className="text-2xl">🚨</span>
            <div className="flex-1">
              <p className="font-medium text-red-300 mb-1">连接错误</p>
              <p className="text-red-200 text-sm mb-2">{error}</p>
              <div className="bg-red-500/20 p-3 rounded-lg border border-red-400/30">
                <p className="text-red-300 text-sm flex items-center gap-2">
                  💡 <span>请确保后端服务正在运行：</span>
                </p>
                <code className="bg-black/30 px-2 py-1 rounded text-red-200 text-xs mt-1 block">
                  uvicorn app.main:app --reload
                </code>
              </div>
            </div>
          </div>
        </div>
      )}

      {healthStatus && !error && (
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <div className="bg-gradient-to-r from-blue-500/20 to-cyan-500/20 p-3 rounded-lg border border-blue-400/30">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">🚀</span>
              <span className="text-blue-300 font-medium">部署模式</span>
            </div>
            <span className="text-theme-primary text-lg font-bold">{healthStatus.deployment?.mode || 'N/A'}</span>
          </div>
          <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 p-3 rounded-lg border border-purple-400/30">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">🖥️</span>
              <span className="text-purple-300 font-medium">设备</span>
            </div>
            <span className="text-theme-primary text-lg font-bold">{healthStatus.deployment?.device || 'N/A'}</span>
          </div>
          <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 p-3 rounded-lg border border-green-400/30">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">🔄</span>
              <span className="text-green-300 font-medium">Redis</span>
            </div>
            <span className={`text-lg font-bold ${healthStatus.redis?.includes('connected') ? 'text-green-300' : 'text-red-300'}`}>
              {healthStatus.redis?.includes('connected') ? '✅ 已连接' : '❌ 未连接'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default APIStatus;
