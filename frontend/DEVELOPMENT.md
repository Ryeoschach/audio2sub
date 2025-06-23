# 🔧 Audio2Sub 前端开发指南

## 🎯 开发环境设置

### 1. 环境要求
- Node.js 18.0+
- pnpm (推荐) 或 npm
- VS Code (推荐编辑器)

### 2. 项目初始化
```bash
# 克隆项目
git clone <repository-url>
cd audio2sub/frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 3. VS Code 推荐插件
- TypeScript Vue Plugin (Volar)
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- Auto Rename Tag
- Bracket Pair Colorizer

## 🏗️ 项目架构

### 组件设计原则
```
🔹 单一职责原则: 每个组件只负责一个功能
🔹 可复用性: 通过 props 使组件可配置
🔹 类型安全: 严格的 TypeScript 类型定义
🔹 状态管理: 使用 React Hooks 管理状态
```

### 目录结构说明
```
src/
├── components/          # 可复用组件
│   ├── ui/             # 基础 UI 组件
│   ├── forms/          # 表单组件
│   └── layout/         # 布局组件
├── services/           # API 和外部服务
├── hooks/              # 自定义 React Hooks
├── utils/              # 工具函数
├── types/              # TypeScript 类型定义
├── constants/          # 常量定义
└── styles/             # 样式文件
```

## 🧩 组件开发规范

### 组件模板
```tsx
import React, { useState, useEffect } from 'react';

// 类型定义
interface ComponentProps {
  title: string;
  onAction?: (data: any) => void;
  loading?: boolean;
}

// 组件实现
const Component: React.FC<ComponentProps> = ({
  title,
  onAction,
  loading = false
}) => {
  // 状态管理
  const [state, setState] = useState<string>('');

  // 副作用
  useEffect(() => {
    // 组件挂载逻辑
  }, []);

  // 事件处理
  const handleAction = () => {
    if (onAction) {
      onAction(state);
    }
  };

  // 渲染
  return (
    <div className="component-container">
      <h2 className="text-xl font-semibold text-slate-200">{title}</h2>
      {loading ? (
        <div className="loading-spinner">加载中...</div>
      ) : (
        <button onClick={handleAction} className="btn-primary">
          执行操作
        </button>
      )}
    </div>
  );
};

export default Component;
```

### Props 设计原则
```tsx
// ✅ 好的设计
interface FileUploadProps {
  onSuccess: (result: UploadResult) => void;
  onError: (error: string) => void;
  acceptedFormats?: string[];
  maxSize?: number;
  disabled?: boolean;
}

// ❌ 避免的设计
interface BadProps {
  callback: any; // 类型不明确
  config: object; // 过于宽泛
  data: any; // 失去类型安全
}
```

## 🎨 样式开发规范

### Tailwind CSS 使用
```tsx
// 基础样式类
const baseClasses = {
  container: "min-h-screen bg-slate-900 text-white",
  card: "bg-slate-800 rounded-lg border border-slate-700 p-6",
  button: "px-4 py-2 rounded-md font-medium transition-colors",
  input: "w-full p-3 bg-slate-700 border border-slate-600 rounded-lg"
};

// 状态样式
const stateClasses = {
  primary: "bg-blue-600 hover:bg-blue-700 text-white",
  success: "bg-green-600 hover:bg-green-700 text-white",
  warning: "bg-yellow-600 hover:bg-yellow-700 text-white",
  danger: "bg-red-600 hover:bg-red-700 text-white"
};
```

### 响应式设计
```tsx
// 响应式组件示例
const ResponsiveGrid: React.FC = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* 移动端单列，平板双列，桌面三列 */}
    </div>
  );
};
```

## 🔌 API 集成开发

### API 服务类设计
```typescript
// services/api.ts
class Audio2SubAPI {
  private baseURL: string;
  private timeout: number;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.timeout = 30000;
  }

  // 统一错误处理
  private handleError(error: any): never {
    if (error.response) {
      // 服务器返回错误状态
      throw new Error(`API Error: ${error.response.status} - ${error.response.data.detail}`);
    } else if (error.request) {
      // 网络错误
      throw new Error('Network Error: 无法连接到服务器');
    } else {
      // 其他错误
      throw new Error(`Error: ${error.message}`);
    }
  }

  // API 方法实现
  async uploadFile(file: File, options: UploadOptions): Promise<UploadResult> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      Object.entries(options).forEach(([key, value]) => {
        formData.append(key, value);
      });

      const response = await fetch(`${this.baseURL}/upload/`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      this.handleError(error);
    }
  }
}
```

### 自定义 Hook 开发
```typescript
// hooks/useAPI.ts
import { useState, useCallback } from 'react';
import { Audio2SubAPI } from '../services/api';

export const useAPI = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const api = new Audio2SubAPI();

  const execute = useCallback(async <T>(
    apiCall: () => Promise<T>
  ): Promise<T | null> => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : '未知错误');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { api, loading, error, execute };
};

// 使用示例
const MyComponent: React.FC = () => {
  const { api, loading, error, execute } = useAPI();
  
  const handleUpload = async (file: File) => {
    const result = await execute(() => 
      api.uploadFile(file, { model: 'base', language: 'zh' })
    );
    
    if (result) {
      console.log('上传成功:', result);
    }
  };

  return (
    <div>
      {loading && <div>加载中...</div>}
      {error && <div className="text-red-500">错误: {error}</div>}
      {/* 组件内容 */}
    </div>
  );
};
```

## 🧪 测试开发

### 单元测试示例
```typescript
// __tests__/components/FileUpload.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import FileUpload from '../components/FileUpload';

describe('FileUpload', () => {
  test('应该渲染文件上传区域', () => {
    render(<FileUpload onSuccess={() => {}} onError={() => {}} />);
    
    expect(screen.getByText(/拖拽文件到此处/)).toBeInTheDocument();
  });

  test('应该处理文件选择', () => {
    const onSuccess = jest.fn();
    render(<FileUpload onSuccess={onSuccess} onError={() => {}} />);
    
    const input = screen.getByLabelText(/选择文件/);
    const file = new File(['test'], 'test.mp3', { type: 'audio/mp3' });
    
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(onSuccess).toHaveBeenCalled();
  });
});
```

### 集成测试
```typescript
// __tests__/integration/api.test.ts
import { Audio2SubAPI } from '../services/api';

describe('API Integration', () => {
  let api: Audio2SubAPI;

  beforeEach(() => {
    api = new Audio2SubAPI('http://localhost:8000');
  });

  test('应该获取健康状态', async () => {
    const health = await api.getHealth();
    expect(health.status).toBe('healthy');
  });

  test('应该获取模型列表', async () => {
    const models = await api.getModels();
    expect(models.models).toBeInstanceOf(Array);
    expect(models.models.length).toBeGreaterThan(0);
  });
});
```

## 🚀 构建和部署

### 构建优化
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    // 代码分割
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          api: ['axios']
        }
      }
    },
    // 资源优化
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  },
  // 开发服务器配置
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
});
```

### 环境配置
```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_LOG_LEVEL=debug

# .env.production  
VITE_API_BASE_URL=https://api.audio2sub.com
VITE_LOG_LEVEL=warn
```

## 🔧 开发工具配置

### ESLint 配置
```json
// .eslintrc.json
{
  "extends": [
    "eslint:recommended",
    "@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended"
  ],
  "rules": {
    "react/react-in-jsx-scope": "off",
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn"
  }
}
```

### Prettier 配置
```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

## 📱 移动端适配

### 响应式设计策略
```tsx
// 移动端优先的设计
const MobileFirstComponent: React.FC = () => {
  return (
    <div className="
      p-4 
      sm:p-6 
      md:p-8 
      lg:p-12
      text-sm 
      sm:text-base 
      md:text-lg
    ">
      <div className="
        grid 
        grid-cols-1 
        sm:grid-cols-2 
        lg:grid-cols-3 
        gap-4
      ">
        {/* 内容 */}
      </div>
    </div>
  );
};
```

### 触摸交互优化
```tsx
// 触摸友好的组件
const TouchFriendlyButton: React.FC = () => {
  return (
    <button className="
      min-h-[44px] 
      min-w-[44px] 
      touch-manipulation
      active:scale-95 
      transition-transform
    ">
      点击我
    </button>
  );
};
```

## 🔍 调试技巧

### React DevTools
```tsx
// 组件调试
const DebugComponent: React.FC = () => {
  const debugInfo = {
    timestamp: Date.now(),
    userAgent: navigator.userAgent,
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight
    }
  };

  // 开发环境下输出调试信息
  if (import.meta.env.DEV) {
    console.log('DebugComponent rendered:', debugInfo);
  }

  return <div>组件内容</div>;
};
```

### 性能监控
```tsx
// 性能监控 Hook
const usePerformanceMonitor = (componentName: string) => {
  useEffect(() => {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      console.log(`${componentName} render time: ${endTime - startTime}ms`);
    };
  });
};
```

---

**最后更新**: 2025年6月19日  
**维护者**: Audio2Sub 开发团队
