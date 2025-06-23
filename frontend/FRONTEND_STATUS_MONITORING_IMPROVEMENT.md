# 🔄 前端状态监控改进方案

## 📋 当前实现问题

前端 APIStatus 组件目前只在组件初始化时检查一次状态，缺乏实时监控机制。

## 🔧 改进方案

### 1. 定时轮询实现

```typescript
// frontend/src/components/APIStatus.tsx
import React, { useState, useEffect, useRef } from 'react';
import { audio2subAPI, HealthStatus, ModelsResponse } from '../services/api';

interface APIStatusProps {
  onModelsLoaded: (models: ModelsResponse) => void;
  onHealthStatus: (isHealthy: boolean) => void;
  pollInterval?: number; // 轮询间隔，默认30秒
  enablePolling?: boolean; // 是否启用轮询，默认true
}

const APIStatus: React.FC<APIStatusProps> = ({ 
  onModelsLoaded, 
  onHealthStatus,
  pollInterval = 30000, // 30秒
  enablePolling = true
}) => {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [modelsData, setModelsData] = useState<ModelsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const checkAPIStatus = async (isManual = false) => {
    if (!isManual && loading) return; // 避免重复请求
    
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
      setLastChecked(new Date());

      const isHealthy = healthResult.status === 'healthy';
      onHealthStatus(isHealthy);
      onModelsLoaded(modelsResult);

      // 如果 Redis 状态发生变化，显示通知
      if (healthStatus && healthStatus.redis !== healthResult.redis) {
        console.log(`Redis 状态变化: ${healthStatus.redis} -> ${healthResult.redis}`);
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'API 连接失败';
      setError(errorMessage);
      onHealthStatus(false);
      console.error('API status check failed:', err);
    } finally {
      setLoading(false);
    }
  };

  // 启动定时检查
  const startPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    if (enablePolling && pollInterval > 0) {
      intervalRef.current = setInterval(() => {
        checkAPIStatus(false);
      }, pollInterval);
    }
  };

  // 停止定时检查
  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  useEffect(() => {
    // 初始检查
    checkAPIStatus(true);
    
    // 启动定时检查
    startPolling();

    // 清理函数
    return () => {
      stopPolling();
    };
  }, [enablePolling, pollInterval]);

  // 手动刷新
  const handleManualRefresh = () => {
    checkAPIStatus(true);
  };

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

  const formatLastChecked = () => {
    if (!lastChecked) return '';
    return lastChecked.toLocaleTimeString();
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
          {lastChecked && (
            <span className="text-xs text-gray-400">
              最后检查: {formatLastChecked()}
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* 轮询状态指示器 */}
          <div className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded-full ${enablePolling ? 'bg-green-400 animate-pulse' : 'bg-gray-400'}`}></span>
            <span className="text-xs text-gray-400">
              {enablePolling ? `自动检查 (${pollInterval/1000}s)` : '手动模式'}
            </span>
          </div>
          
          {/* 切换轮询按钮 */}
          <button
            onClick={() => enablePolling ? stopPolling() : startPolling()}
            className="px-2 py-1 text-xs bg-gray-500/20 hover:bg-gray-500/30 text-gray-300 border border-gray-400/30 rounded transition-all duration-300"
          >
            {enablePolling ? '⏸️' : '▶️'}
          </button>
          
          {/* 手动刷新按钮 */}
          <button
            onClick={handleManualRefresh}
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
                🔄 <span>立即检查</span>
              </>
            )}
          </button>
        </div>
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
            <div className="flex items-center gap-2">
              <span className={`text-lg font-bold ${healthStatus.redis?.includes('connected') ? 'text-green-300' : 'text-red-300'}`}>
                {healthStatus.redis?.includes('connected') ? '✅ 已连接' : '❌ 未连接'}
              </span>
              {/* Redis 连接状态变化动画 */}
              {healthStatus.redis?.includes('connected') && (
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default APIStatus;
```

### 2. 使用改进后的组件

```typescript
// 在父组件中使用
<APIStatus 
  onModelsLoaded={handleModelsLoaded}
  onHealthStatus={handleHealthStatus}
  pollInterval={30000}  // 30秒轮询一次
  enablePolling={true}  // 启用自动轮询
/>
```

### 3. WebSocket 实时监控实现（高级方案）

```typescript
// frontend/src/hooks/useRealtimeStatus.ts
import { useState, useEffect, useRef } from 'react';
import { HealthStatus } from '../services/api';

interface UseRealtimeStatusOptions {
  wsUrl?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const useRealtimeStatus = (options: UseRealtimeStatusOptions = {}) => {
  const {
    wsUrl = 'ws://localhost:8000/ws/status',
    reconnectInterval = 5000,
    maxReconnectAttempts = 5
  } = options;

  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const connect = () => {
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setHealthStatus(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // 自动重连
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else {
          setError('WebSocket连接失败，已达到最大重试次数');
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket连接错误');
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('无法建立WebSocket连接');
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  };

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [wsUrl]);

  return {
    healthStatus,
    isConnected,
    error,
    reconnect: connect,
    disconnect
  };
};
```

## 🎯 实施建议

1. **开发阶段**：使用定时轮询方案（30秒间隔）
2. **生产环境**：考虑实现 WebSocket 实时推送
3. **用户体验**：
   - 显示最后检查时间
   - 提供手动刷新按钮
   - 显示轮询状态指示器
   - 支持暂停/恢复自动检查

4. **性能优化**：
   - 避免重复请求
   - 合理设置轮询间隔
   - 页面不可见时暂停轮询

5. **错误处理**：
   - 网络错误重试机制
   - 显示详细错误信息
   - 提供故障排查建议

这样可以确保前端能够及时感知到 Redis 状态的变化，解决状态不一致的问题。
