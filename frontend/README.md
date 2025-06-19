# 🎵 Audio2Sub Frontend

音频/视频转字幕的前端用户界面，基于 React + TypeScript + Vite 构建。

## 🏗️ 项目结构

```
frontend/
├── 📁 src/                      # 源代码
│   ├── 📁 components/           # React 组件
│   │   ├── ApiStatus.tsx        # API 状态监控
│   │   ├── FileUpload.tsx       # 文件上传组件
│   │   ├── ModelSelector.tsx    # 模型选择器
│   │   ├── TranscriptionOptions.tsx # 转录选项配置
│   │   ├── TranscriptionStatus.tsx  # 转录状态显示
│   │   └── ResultsDisplay.tsx   # 结果展示组件
│   ├── 📁 services/             # API 服务
│   │   └── api.ts              # API 接口封装
│   ├── 📁 types/               # TypeScript 类型定义
│   │   └── index.ts            # 通用类型
│   ├── App.tsx                 # 主应用组件
│   ├── main.tsx               # 应用入口点
│   └── index.css              # 全局样式
├── 📄 index.html              # HTML 模板
├── 📋 package.json            # 项目配置和依赖
├── ⚙️ vite.config.ts         # Vite 构建配置
├── ⚙️ tailwind.config.js     # Tailwind CSS 配置
├── ⚙️ tsconfig.json          # TypeScript 配置
└── 🐳 Dockerfile             # Docker 构建文件
```

## ✨ 核心功能

### 🎯 动态模型选择
- **智能推荐**: 根据用户需求推荐最适合的模型
- **实时切换**: 支持在转录过程中动态选择模型
- **性能对比**: 显示不同模型的速度和质量对比

### 🌍 多语言支持
- **智能检测**: 根据浏览器语言自动设置默认值
- **语言指定**: 支持手动指定音频语言
- **混合语音**: 处理多语言混合的音频内容

### 📄 灵活输出格式
- **SRT 格式**: 兼容性最好，支持大多数播放器
- **VTT 格式**: 适用于网页播放器
- **双格式**: 同时生成 SRT 和 VTT 文件

### ⚡ 实时状态监控
- **上传进度**: 显示文件上传的实时进度
- **转录状态**: 实时更新转录任务的状态
- **错误处理**: 友好的错误信息和重试机制

## 🚀 快速开始

### 环境要求
- Node.js 18+
- npm 或 pnpm 或 yarn

### 安装依赖
```bash
# 使用 pnpm (推荐)
pnpm install

# 或使用 npm
npm install

# 或使用 yarn
yarn install
```

### 开发模式
```bash
# 启动开发服务器
pnpm dev

# 或
npm run dev
```

应用将在 http://localhost:5173 启动

### 构建生产版本
```bash
# 构建生产版本
pnpm build

# 预览生产版本
pnpm preview
```

## 🔧 开发指南

### 组件说明

#### 1. `FileUpload.tsx` - 文件上传组件
**功能**: 处理音频/视频文件的选择和上传

**特性**:
- 拖拽上传支持
- 文件格式验证
- 智能默认语言设置
- 上传进度显示

**使用示例**:
```tsx
<FileUpload
  onUploadSuccess={(result) => setTaskId(result.task_id)}
  onUploadError={(error) => setError(error)}
  models={availableModels}
  defaultModel="base"
/>
```

#### 2. `ModelSelector.tsx` - 模型选择器
**功能**: 动态选择 Whisper 模型

**支持的模型**:
- `tiny` - 最快速度，适合实时处理
- `base` - 平衡推荐，日常使用
- `small` - 高质量转录
- `large-v3-turbo` - 最佳质量

**使用示例**:
```tsx
<ModelSelector
  models={models}
  selectedModel={selectedModel}
  onModelChange={setSelectedModel}
  loading={isLoading}
/>
```

#### 3. `TranscriptionOptions.tsx` - 转录选项
**功能**: 配置转录参数

**选项包括**:
- **语言选择**: auto/zh/en 等
- **输出格式**: srt/vtt/both
- **任务类型**: transcribe/translate

**智能特性**:
- 根据浏览器语言自动设置默认值
- 为中文用户推荐 `zh` 而非 `auto`
- 实时参数验证

#### 4. `TranscriptionStatus.tsx` - 状态监控
**功能**: 实时显示转录进度和状态

**状态类型**:
- `PENDING` - 等待开始
- `PROGRESS` - 转录中
- `SUCCESS` - 完成
- `FAILURE` - 失败

#### 5. `ResultsDisplay.tsx` - 结果展示
**功能**: 展示转录结果和文件下载

**展示内容**:
- 转录文本预览
- 处理时间统计
- 生成的字幕文件
- 下载链接

### API 服务 (`services/api.ts`)

#### 主要接口
```typescript
class Audio2SubAPI {
  // 健康检查
  async getHealth(): Promise<HealthResponse>
  
  // 获取模型列表
  async getModels(): Promise<ModelsResponse>
  
  // 上传文件
  async uploadFile(file: File, options: UploadOptions): Promise<UploadResponse>
  
  // 查询任务状态
  async getTaskStatus(taskId: string): Promise<TaskStatusResponse>
  
  // 下载文件
  async downloadFile(fileId: string, filename: string): Promise<void>
}
```

#### 使用示例
```typescript
import { Audio2SubAPI } from './services/api';

const api = new Audio2SubAPI('http://localhost:8000');

// 上传文件
const result = await api.uploadFile(file, {
  model: 'base',
  language: 'zh',
  output_format: 'both',
  task: 'transcribe'
});

// 监控状态
const status = await api.getTaskStatus(result.task_id);
```

## 🎨 样式和主题

### Tailwind CSS 配置
项目使用 Tailwind CSS 进行样式管理，配置文件: `tailwind.config.js`

**主要样式特点**:
- 🌙 深色主题为主
- 🎨 现代化的 UI 设计
- 📱 完全响应式布局
- ♿ 无障碍访问支持

### 颜色方案
```css
/* 主色调 */
--primary: slate-700
--secondary: teal-500
--accent: blue-500

/* 状态颜色 */
--success: green-500
--warning: yellow-500
--error: red-500
--info: blue-500
```

### 响应式断点
- `sm`: 640px+
- `md`: 768px+
- `lg`: 1024px+
- `xl`: 1280px+

## 🧪 测试

### 组件测试
```bash
# 运行单元测试
pnpm test

# 运行测试覆盖率
pnpm test:coverage
```

### E2E 测试
```bash
# 运行端到端测试
pnpm test:e2e
```

### API 集成测试
前端项目包含了完整的 API 测试工具:

**浏览器测试页面**:
- 文件: `../backend/scripts/testing/test_api_page.html`
- 功能: 可视化测试界面，支持实时监控

**JavaScript 测试库**:
- 文件: `../backend/scripts/testing/test_api_frontend.js`
- 功能: 编程式 API 测试工具

### 测试工作流
1. **开发阶段**: 使用组件测试验证功能
2. **集成阶段**: 使用 API 测试验证接口
3. **发布前**: 运行完整的 E2E 测试

## 🐳 Docker 部署

### 构建镜像
```bash
# 构建前端镜像
docker build -t audio2sub-frontend .
```

### 运行容器
```bash
# 运行前端容器
docker run -p 3000:80 audio2sub-frontend
```

### Docker Compose 集成
```yaml
# docker-compose.yml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

## 🔧 配置说明

### 环境变量
创建 `.env.local` 文件配置环境变量:

```bash
# API 服务地址
VITE_API_BASE_URL=http://localhost:8000

# 上传文件大小限制 (MB)
VITE_MAX_FILE_SIZE=100

# 支持的文件格式
VITE_SUPPORTED_FORMATS=mp3,wav,flac,m4a,mp4,avi,mov
```

### Vite 配置 (`vite.config.ts`)
```typescript
export default defineConfig({
  plugins: [react()],
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
})
```

## 📱 用户界面说明

### 主界面布局
```
┌─────────────────────────────────────┐
│ 🎵 Audio2Sub - 音频转字幕          │
├─────────────────────────────────────┤
│ 📊 API 状态: ●健康                  │
├─────────────────────────────────────┤
│ 🤖 模型选择: [base ▼]               │
│ 🌍 语言设置: [中文 ▼]               │
│ 📄 输出格式: [SRT+VTT ▼]            │
│ 🔧 任务类型: [转录为原语言 ▼]        │
├─────────────────────────────────────┤
│ 📤 文件上传区域                     │
│ 拖拽文件到此处或点击选择             │
├─────────────────────────────────────┤
│ ⏳ 转录状态: 等待上传               │
├─────────────────────────────────────┤
│ 📥 转录结果                         │
│ • audio.srt (下载)                  │
│ • audio.vtt (下载)                  │
└─────────────────────────────────────┘
```

### 用户体验优化
- **智能默认值**: 根据浏览器语言设置
- **实时反馈**: 上传和转录过程可视化
- **错误提示**: 友好的错误信息和解决建议
- **性能优化**: 懒加载和组件优化

## 🚨 故障排除

### 常见问题

#### 1. API 连接失败
```
❌ 无法连接到后端服务
```
**解决方案**:
- 检查后端服务是否启动
- 确认 API 地址配置正确
- 检查网络连接和防火墙设置

#### 2. 文件上传失败
```
❌ 文件上传失败: 413 Request Entity Too Large
```
**解决方案**:
- 检查文件大小是否超过限制
- 确认文件格式是否支持
- 查看服务器配置的上传限制

#### 3. 转录结果为空
```
⚠️ 转录完成但结果为空
```
**解决方案**:
- 确保音频文件质量良好
- 检查语言设置是否正确
- 尝试使用更高质量的模型

### 开发调试
```bash
# 启用详细日志
export VITE_LOG_LEVEL=debug

# 开发服务器详细输出
pnpm dev --debug
```

## 📈 性能优化

### 构建优化
- **代码分割**: 使用动态导入减少初始包大小
- **资源压缩**: 自动压缩 JS/CSS/图片
- **缓存策略**: 合理设置资源缓存

### 运行时优化
- **React.memo**: 避免不必要的组件重渲染
- **useMemo/useCallback**: 优化昂贵的计算和函数
- **虚拟滚动**: 处理大量数据时的性能优化

### 监控和分析
```bash
# 分析打包大小
pnpm build --analyze

# 性能审计
lighthouse http://localhost:5173
```

## 🔗 相关文档

- [后端 API 文档](../backend/README.md)
- [测试指南](../backend/scripts/testing/README.md)
- [部署指南](../backend/docs/deployment/)
- [API 接口文档](../backend/docs/api.md)

## 🤝 贡献指南

### 开发流程
1. Fork 项目到个人仓库
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交变更: `git commit -m 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 创建 Pull Request

### 代码规范
- 使用 TypeScript 严格模式
- 遵循 ESLint 和 Prettier 配置
- 编写单元测试覆盖新功能
- 更新相关文档

### 提交信息格式
```
type(scope): description

feat(upload): add drag and drop support
fix(api): handle network timeout errors
docs(readme): update installation guide
```

---

**最后更新**: 2025年6月19日  
**版本**: 1.0.0  
**维护者**: Audio2Sub 开发团队
