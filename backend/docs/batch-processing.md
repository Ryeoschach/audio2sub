# 🚀 Audio2Sub 批量处理功能文档

## 概述

Audio2Sub 现在支持批量处理多个音频/视频文件，可以同时上传最多50个文件进行转录，支持并发处理以提高效率。

## 🌟 新增功能

### 1. 批量上传API
- **端点**: `POST /batch-upload/`
- **功能**: 同时上传多个音频/视频文件进行转录
- **限制**: 最多50个文件，每个文件大小限制与单文件相同
- **并发控制**: 支持1-10个文件并发处理

### 2. 批量状态监控
- **端点**: `GET /batch-status/{batch_id}`
- **功能**: 实时监控批量任务的整体进度和各个文件的状态
- **信息**: 总体进度、完成数量、失败数量、各文件详细状态

### 3. 批量结果汇总
- **端点**: `GET /batch-result/{batch_id}`
- **功能**: 获取批量任务完成后的结果汇总
- **信息**: 成功/失败统计、处理时间、转录结果、错误信息

### 4. 批量任务取消
- **端点**: `DELETE /batch/{batch_id}`
- **功能**: 取消正在进行的批量任务
- **行为**: 尝试终止所有相关的子任务

## 📡 API 接口详解

### 批量上传

```http
POST /batch-upload/
Content-Type: multipart/form-data

参数:
- files: 多个音频/视频文件 (必需)
- model: Whisper模型 (默认: base)
- language: 语言代码 (默认: auto)
- output_format: 输出格式 (默认: both)
- task: 任务类型 (默认: transcribe)
- concurrent_limit: 并发限制 (默认: 3, 范围: 1-10)
```

**响应示例:**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "批量任务已创建，共 3 个文件，使用 base 模型",
  "total_files": 3,
  "tasks": [
    {
      "file_id": "file-uuid-1",
      "filename": "audio1.mp3",
      "task_id": "",
      "status": "PENDING",
      "progress": 0,
      "estimated_time": 60
    }
  ],
  "model_used": "base",
  "estimated_total_time": 120
}
```

### 批量状态查询

```http
GET /batch-status/{batch_id}
```

**响应示例:**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_files": 3,
  "completed_files": 2,
  "failed_files": 0,
  "progress_percentage": 66.7,
  "overall_status": "PROCESSING",
  "tasks": [
    {
      "file_id": "file-uuid-1",
      "filename": "audio1.mp3",
      "task_id": "task-uuid-1",
      "status": "SUCCESS",
      "progress": 100
    },
    {
      "file_id": "file-uuid-2",
      "filename": "audio2.mp3",
      "task_id": "task-uuid-2",
      "status": "PROGRESS",
      "progress": 75
    }
  ],
  "start_time": "2024-01-01T10:00:00Z"
}
```

### 批量结果汇总

```http
GET /batch-result/{batch_id}
```

**响应示例:**
```json
{
  "batch_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_files": 3,
  "successful_files": 2,
  "failed_files": 1,
  "total_processing_time": 180.5,
  "results": [
    {
      "file_id": "file-uuid-1",
      "filename": "audio1.mp3",
      "status": "Completed",
      "srt_path": "audio1.srt",
      "vtt_path": "audio1.vtt",
      "full_text": "转录的文本内容...",
      "timing": {
        "total_time": 85.2,
        "transcription_time": 78.1
      }
    }
  ],
  "errors": [
    {
      "file_id": "file-uuid-3",
      "filename": "corrupted.mp3",
      "error": "File format not supported"
    }
  ]
}
```

## 🔧 使用指南

### 1. Python 客户端示例

```python
import requests

# 1. 批量上传
files = [
    ('files', ('audio1.mp3', open('audio1.mp3', 'rb'), 'audio/mpeg')),
    ('files', ('audio2.mp3', open('audio2.mp3', 'rb'), 'audio/mpeg')),
    ('files', ('video1.mp4', open('video1.mp4', 'rb'), 'video/mp4'))
]

data = {
    'model': 'base',
    'language': 'zh',
    'output_format': 'both',
    'concurrent_limit': 3
}

response = requests.post('http://localhost:8000/batch-upload/', files=files, data=data)
batch_info = response.json()
batch_id = batch_info['batch_id']

# 2. 监控进度
import time

while True:
    status_response = requests.get(f'http://localhost:8000/batch-status/{batch_id}')
    status = status_response.json()
    
    print(f"Progress: {status['progress_percentage']:.1f}%")
    
    if status['overall_status'] in ['COMPLETED', 'FAILED', 'PARTIAL_SUCCESS']:
        break
    
    time.sleep(5)

# 3. 获取结果
result_response = requests.get(f'http://localhost:8000/batch-result/{batch_id}')
results = result_response.json()

print(f"Successful files: {results['successful_files']}")
print(f"Failed files: {results['failed_files']}")
```

### 2. JavaScript 客户端示例

```javascript
// 批量上传
async function batchUpload(files) {
    const formData = new FormData();
    
    files.forEach(file => {
        formData.append('files', file);
    });
    
    formData.append('model', 'base');
    formData.append('language', 'auto');
    formData.append('output_format', 'both');
    formData.append('concurrent_limit', '3');
    
    const response = await fetch('/batch-upload/', {
        method: 'POST',
        body: formData
    });
    
    return await response.json();
}

// 监控进度
async function monitorBatchProgress(batchId) {
    while (true) {
        const response = await fetch(`/batch-status/${batchId}`);
        const status = await response.json();
        
        console.log(`Progress: ${status.progress_percentage}%`);
        
        if (['COMPLETED', 'FAILED', 'PARTIAL_SUCCESS'].includes(status.overall_status)) {
            break;
        }
        
        await new Promise(resolve => setTimeout(resolve, 5000));
    }
}
```

### 3. 命令行测试

```bash
# 使用提供的测试脚本
cd /Users/creed/workspace/sourceCode/audio2sub/backend
python scripts/testing/test_batch_api.py
```

## ⚡ 性能优化

### 并发处理策略
- **默认并发数**: 3个文件同时处理
- **推荐设置**: 根据服务器性能调整
  - 低配置: 1-2个并发
  - 中等配置: 3-5个并发
  - 高配置: 5-10个并发

### 内存管理
- 每个并发任务占用独立内存空间
- 自动清理临时文件
- 合理设置并发限制避免内存溢出

### 处理时间估算
批量处理总时间 ≈ (总文件数 ÷ 并发数) × 单文件平均处理时间

## 🚨 注意事项

### 文件限制
- **最大文件数**: 50个
- **单文件大小**: 与单文件上传相同限制
- **支持格式**: 所有单文件支持的音频/视频格式

### 错误处理
- 单个文件失败不影响其他文件处理
- 提供详细的错误信息和状态码
- 支持部分成功的批量任务

### 资源管理
- 任务状态在Redis中保存24小时
- 自动清理临时文件
- 支持任务取消和资源释放

## 🔧 配置说明

### 环境变量
```bash
# Redis配置 (用于批量任务状态管理)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 建议配置
```python
# 生产环境建议
CONCURRENT_LIMIT_DEFAULT = 3
MAX_BATCH_FILES = 50
BATCH_STATUS_TTL = 86400  # 24小时
```

## 🧪 测试

运行完整的批量处理测试：

```bash
# 确保后端服务运行在 localhost:8000
python scripts/testing/test_batch_api.py
```

测试包括：
1. API健康检查
2. 批量文件上传
3. 进度监控
4. 结果获取
5. 错误处理

## 📈 监控和日志

### 日志输出
- 批量任务创建和开始
- 各个文件的处理进度
- 错误和异常信息
- 性能统计信息

### 监控指标
- 批量任务成功率
- 平均处理时间
- 并发任务数量
- 资源使用情况

## 🔄 升级指南

如果从单文件版本升级到批量版本：

1. **更新依赖**: 确保Redis可用
2. **数据模型**: 新增批量处理相关模型
3. **API端点**: 添加批量处理端点
4. **任务系统**: 扩展Celery任务支持批量处理
5. **测试验证**: 运行测试脚本验证功能

批量处理功能完全兼容原有的单文件处理API，无需修改现有客户端代码。
