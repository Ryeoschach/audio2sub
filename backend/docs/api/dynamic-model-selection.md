# 🎯 动态模型选择 API 使用指南

Audio2Sub 现在支持在每次转录请求时动态选择不同的 Whisper 模型！

## 🤖 支持的模型

| 模型名称 | 文件大小 | 相对速度 | 准确度 | 适用场景 |
|---------|---------|---------|--------|----------|
| `tiny` | 39 MB | ~32x | 较低 | 快速测试 |
| `tiny.en` | 39 MB | ~32x | 较低 | 英文快速转录 |
| `base` | 142 MB | ~16x | 良好 | 日常使用推荐 ⭐ |
| `base.en` | 142 MB | ~16x | 良好 | 英文日常使用 |
| `small` | 466 MB | ~6x | 较高 | 高质量转录 |
| `small.en` | 466 MB | ~6x | 较高 | 英文高质量 |
| `medium` | 1.5 GB | ~2x | 高 | 专业转录 |
| `medium.en` | 1.5 GB | ~2x | 高 | 英文专业转录 |
| `large-v1` | 2.9 GB | ~1x | 最高 | 最高质量 |
| `large-v2` | 2.9 GB | ~1x | 最高 | 最高质量v2 |
| `large-v3` | 2.9 GB | ~1x | 最高 | 最新最高质量 |
| `large-v3-turbo` | 809 MB | ~8x | 很高 | 快速高质量 ⭐ |

## 📡 API 端点

### 1. 获取支持的模型列表

```http
GET /models/
```

**响应示例:**
```json
{
  "models": [
    {
      "name": "base",
      "size": "142 MB",
      "speed": "~16x",
      "accuracy": "良好",
      "use_case": "日常使用推荐"
    }
  ],
  "default_model": "base"
}
```

### 2. 上传文件进行转录

```http
POST /upload/
Content-Type: multipart/form-data
```

**参数:**
- `file` (文件) - 音频或视频文件
- `model` (可选) - 模型名称，默认: `base`
- `language` (可选) - 语言代码，默认: `auto`
- `output_format` (可选) - 输出格式，默认: `both`
  - `srt`: 只生成 SRT 格式
  - `vtt`: 只生成 VTT 格式  
  - `both`: 生成两种格式
- `task` (可选) - 任务类型，默认: `transcribe`
  - `transcribe`: 转录为原语言
  - `translate`: 翻译为英文

**响应示例:**
```json
{
  "task_id": "abc123",
  "file_id": "file456",
  "message": "文件已上传，开始使用 base 模型进行转录",
  "model_used": "base",
  "estimated_time": 60
}
```

### 3. 查询任务状态

```http
GET /status/{task_id}
```

**响应示例:**
```json
{
  "state": "SUCCESS",
  "result": {
    "status": "Completed",
    "files": [
      {"type": "srt", "filename": "audio.srt", "path": "/path/to/audio.srt"},
      {"type": "vtt", "filename": "audio.vtt", "path": "/path/to/audio.vtt"}
    ],
    "transcription_params": {
      "model": "base",
      "language": "zh",
      "output_format": "both",
      "task_type": "transcribe"
    },
    "timing": {
      "total_time": 45.2,
      "transcription_time": 30.1
    }
  }
}
```

## 💡 使用示例

### JavaScript/TypeScript (前端)

```javascript
// 1. 获取支持的模型
const modelsResponse = await fetch('/api/models/');
const models = await modelsResponse.json();
console.log('支持的模型:', models.models);

// 2. 上传文件并指定模型
const formData = new FormData();
formData.append('file', audioFile);
formData.append('model', 'small');  // 使用 small 模型
formData.append('language', 'zh');
formData.append('output_format', 'srt');

const uploadResponse = await fetch('/api/upload/', {
  method: 'POST',
  body: formData
});

const result = await uploadResponse.json();
console.log('任务ID:', result.task_id);
console.log('使用模型:', result.model_used);

// 3. 轮询任务状态
const checkStatus = async (taskId) => {
  const statusResponse = await fetch(`/api/status/${taskId}`);
  const status = await statusResponse.json();
  
  if (status.state === 'SUCCESS') {
    console.log('转录完成!');
    console.log('生成文件:', status.result.files);
  } else if (status.state === 'FAILURE') {
    console.error('转录失败:', status.status);
  } else {
    // 继续轮询
    setTimeout(() => checkStatus(taskId), 2000);
  }
};

checkStatus(result.task_id);
```

### Python (脚本/后端)

```python
import requests
import time

# 1. 获取模型列表
models_response = requests.get('http://localhost:8000/models/')
models = models_response.json()
print(f"默认模型: {models['default_model']}")

# 2. 上传文件转录
with open('audio.mp3', 'rb') as f:
    files = {'file': f}
    data = {
        'model': 'large-v3-turbo',  # 使用快速高质量模型
        'language': 'auto',         # 自动检测语言
        'output_format': 'both',    # 生成 SRT 和 VTT
        'task': 'transcribe'        # 转录任务
    }
    
    response = requests.post('http://localhost:8000/upload/', 
                           files=files, data=data)

result = response.json()
task_id = result['task_id']
print(f"任务已创建: {task_id}")
print(f"使用模型: {result['model_used']}")
print(f"预估时间: {result['estimated_time']}秒")

# 3. 监控任务状态
while True:
    status_response = requests.get(f'http://localhost:8000/status/{task_id}')
    status = status_response.json()
    
    if status['state'] == 'SUCCESS':
        result = status['result']
        print("转录完成!")
        print(f"使用模型: {result['transcription_params']['model']}")
        print(f"处理时间: {result['timing']['total_time_formatted']}")
        
        for file_info in result['files']:
            print(f"生成文件: {file_info['filename']} ({file_info['type']})")
        break
    elif status['state'] == 'FAILURE':
        print(f"转录失败: {status.get('status', 'Unknown error')}")
        break
    else:
        print(f"处理中... ({status.get('status', '')})")
        time.sleep(2)
```

### curl (命令行)

```bash
# 1. 获取模型列表
curl -X GET "http://localhost:8000/models/" | jq

# 2. 上传文件转录 (使用 small 模型)
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@audio.mp3" \
  -F "model=small" \
  -F "language=zh" \
  -F "output_format=srt" \
  -F "task=transcribe"

# 3. 查询任务状态
curl -X GET "http://localhost:8000/status/your-task-id" | jq
```

## 🎯 模型选择建议

### 🚀 追求速度
- **超快**: `tiny` / `tiny.en` (32倍速度)
- **快速**: `base` / `base.en` (16倍速度)
- **平衡**: `large-v3-turbo` (8倍速度 + 高质量)

### 🎯 追求质量
- **高质量**: `small` / `medium`
- **最高质量**: `large-v3` (最新最佳)
- **专业级**: `large-v2` / `large-v1`

### 🌍 语言特定
- **英文专用**: 选择 `.en` 后缀模型 (更快更准确)
- **多语言**: 选择无后缀模型
- **中文**: 推荐 `base` 或以上模型

### 💾 存储考虑
- **小文件**: `tiny` (39MB) / `base` (142MB)
- **中等**: `small` (466MB) / `large-v3-turbo` (809MB)
- **大文件**: `medium` (1.5GB) / `large-v3` (2.9GB)

## ⚠️ 注意事项

1. **首次使用**: 模型会自动下载，首次使用某个模型时会较慢
2. **存储空间**: 大模型需要更多磁盘空间
3. **内存要求**: 大模型需要更多内存
4. **网络环境**: 模型下载需要稳定的网络连接

## 🔧 故障排除

- **模型下载失败**: 检查网络连接和磁盘空间
- **内存不足**: 尝试使用较小的模型
- **转录质量差**: 尝试使用更大的模型
- **处理太慢**: 使用 `tiny` 或 `base` 模型
