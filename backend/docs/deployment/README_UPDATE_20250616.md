# Audio2Sub 后端系统更新文档

## 📅 更新日期：2025年6月16日

---

## 🎯 今日主要优化内容

### 1. 🔧 修复 insanely-fast-whisper 兼容性问题
- **问题**：`insanely-fast-whisper` 存在张量维度不匹配错误
- **解决方案**：切换到更稳定的 `transformers` pipeline 直接调用
- **效果**：提高了系统稳定性和兼容性

### 2. ⚡ 性能优化配置
- **批处理优化**：添加 `BATCH_SIZE` 配置（默认4）
- **块处理优化**：`CHUNK_LENGTH_S` 和 `STRIDE_LENGTH_S` 参数
- **设备优化**：智能 MPS/CPU 设备选择
- **效果**：显著提升转录速度

### 3. ⏱️ 时间跟踪功能
- **详细计时**：各阶段执行时间记录
- **控制台展示**：emoji 图标美化的时间日志
- **API 返回**：完整的时间信息结构
- **效果**：便于性能分析和监控

### 4. 📝 智能字幕分段
- **多重分段条件**：时间、词数、字符数、语义边界
- **配置化参数**：可调整的分段规则
- **自然断句**：在句号、感叹号、问号处优先分段
- **效果**：生成更合理的字幕时间段（6秒以内）

### 5. 🔇 警告信息优化
- **过滤无关警告**：过滤 transformers 库的弃用警告
- **环境变量设置**：减少冗余日志输出
- **效果**：清洁的控制台输出

---

## 🛠️ 系统配置参数

### 模型配置
```python
MODEL_NAME: str = "openai/whisper-large-v3-turbo"  # 高性能模型
MODEL_DEVICE: str = "mps"  # Apple Silicon 优化
TORCH_DTYPE: str = "float16"  # 内存优化
```

### 性能优化配置
```python
BATCH_SIZE: int = 4  # 批处理大小
CHUNK_LENGTH_S: int = 30  # 音频块长度（秒）
STRIDE_LENGTH_S: int = 5  # 块重叠长度（秒）
```

### 字幕分段配置
```python
MAX_SUBTITLE_DURATION: int = 6  # 最大字幕时长（秒）
MAX_WORDS_PER_SUBTITLE: int = 10  # 最大词数
MAX_CHARS_PER_SUBTITLE: int = 60  # 最大字符数
```

---

## 🌐 API 接口文档

### 1. 文件上传接口

**POST** `/upload/`

**请求格式：**
```
Content-Type: multipart/form-data
```

**参数：**
- `file`: 音频/视频文件
  - 支持格式：MP3, WAV, FLAC, M4A, AAC, OGG, WMA
  - 视频格式：MP4, AVI, MOV, MKV, WEBM, FLV, WMV

**响应：**
```json
{
  "task_id": "uuid-string",
  "message": "File uploaded and transcription task started"
}
```

### 2. 任务状态查询接口

**GET** `/status/{task_id}`

**响应格式：**

#### 处理中状态
```json
{
  "state": "PROGRESS",
  "status": "Starting transcription...",
  "progress": 30
}
```

#### 成功状态
```json
{
  "state": "SUCCESS",
  "status": "Completed",
  "result": {
    "status": "Completed",
    "srt_path": "filename.srt",
    "vtt_path": "filename.vtt",
    "original_filename": "原始文件名.mp3",
    "file_id": "uuid-string",
    "full_text": "完整转录文本内容",
    "timing": {
      "total_time": 41.22,
      "total_time_formatted": "0:00:41",
      "ffmpeg_time": 2.35,
      "transcription_time": 38.72,
      "subtitle_generation_time": 0.15,
      "start_time": "2025-06-16T22:45:30",
      "end_time": "2025-06-16T22:46:15"
    }
  }
}
```

#### 失败状态
```json
{
  "state": "FAILURE",
  "status": "错误描述信息",
  "total_time": 15.5
}
```

### 3. 结果文件下载接口

**GET** `/results/{file_id}/{filename}`

**参数：**
- `file_id`: 任务ID
- `filename`: 文件名（.srt 或 .vtt）

**响应：**
- SRT 文件：`Content-Type: application/x-subrip`
- VTT 文件：`Content-Type: text/vtt`

---

## 📊 时间跟踪信息详解

### 控制台输出示例
```
📁 Starting transcription task for file: example.mp3
🕐 Task started at: 2025-06-16 22:45:30
🆔 File ID: abc123-def456
🎬 Extracting audio from video: /path/to/video.mp4
✅ Audio extraction completed in 2.35 seconds
🎙️ Starting transcription with model: openai/whisper-large-v3-turbo
✅ Transcription completed
✅ Subtitle generation completed in 0.15 seconds
📄 SRT saved to: /path/to/result.srt
📄 VTT saved to: /path/to/result.vtt
🏁 Task completed at: 2025-06-16 22:46:15
⏱️  TIMING SUMMARY:
   📁 File processing: 2.35s
   🎙️  Transcription: 38.72s
   📄 Subtitle generation: 0.15s
   🎯 TOTAL TIME: 41.22s (0:00:41)
```

### 时间信息字段说明
- `total_time`: 总处理时间（秒）
- `total_time_formatted`: 格式化的总时间（时:分:秒）
- `ffmpeg_time`: 音频提取时间（仅视频文件）
- `transcription_time`: 转录处理时间
- `subtitle_generation_time`: 字幕生成时间
- `start_time`: 任务开始时间（ISO 格式）
- `end_time`: 任务结束时间（ISO 格式）

---

## 📝 字幕分段优化

### 分段规则优先级
1. **时间限制**：单个字幕条目不超过 6 秒
2. **词数限制**：不超过 10 个词
3. **字符限制**：不超过 60 个字符
4. **语义分段**：在句号、感叹号、问号处自然分段
5. **最小长度**：确保至少 2 个词才在句子边界分段

### 字幕效果对比

**优化前：**
```
1
00:00:00,000 --> 00:05:49,900
整个音频文件的所有内容都在一个字幕条目里，时间跨度过长，不便阅读。
```

**优化后：**
```
1
00:00:00,000 --> 00:00:05,200
第一段合理长度的字幕内容。

2
00:00:05,200 --> 00:00:10,800
第二段在句子边界自然分段。

3
00:00:10,800 --> 00:00:16,500
第三段确保时间和长度合理。
```

---

## 🚀 部署和使用

### 启动服务

1. **启动 Redis**（如果使用外部 Redis）：
```bash
redis-server
```

2. **启动 Celery Worker**：
```bash
cd /Users/creed/Workspace/OpenSource/audio2sub/backend
source .venv/bin/activate
celery -A celery_app.celery_app worker --loglevel=info --pool=solo
```

3. **启动 FastAPI 服务**：
```bash
cd /Users/creed/Workspace/OpenSource/audio2sub/backend
source .venv/bin/activate
uv run uvicorn app.main:app --reload --port 8000
```

### 服务地址
- **API 服务**：http://127.0.0.1:8000
- **API 文档**：http://127.0.0.1:8000/docs

---

## 🔧 前端集成示例

### JavaScript 调用示例

```javascript
// 1. 上传文件
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/upload/', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  return result.task_id;
}

// 2. 查询任务状态
async function checkTaskStatus(taskId) {
  const response = await fetch(`/status/${taskId}`);
  const status = await response.json();
  
  if (status.state === 'SUCCESS') {
    console.log('转录完成！');
    console.log('总时间：', status.result.timing.total_time_formatted);
    console.log('SRT文件：', status.result.srt_path);
    console.log('VTT文件：', status.result.vtt_path);
  } else if (status.state === 'PROGRESS') {
    console.log('进度：', status.progress + '%');
    console.log('状态：', status.status);
  }
  
  return status;
}

// 3. 下载结果文件
function downloadSubtitle(fileId, filename) {
  const url = `/results/${fileId}/${filename}`;
  window.open(url, '_blank');
}

// 4. 完整工作流程
async function transcribeAudio(file) {
  try {
    // 上传文件
    const taskId = await uploadFile(file);
    console.log('任务ID：', taskId);
    
    // 轮询状态
    const interval = setInterval(async () => {
      const status = await checkTaskStatus(taskId);
      
      if (status.state === 'SUCCESS') {
        clearInterval(interval);
        const result = status.result;
        
        // 显示结果
        console.log('转录文本：', result.full_text);
        console.log('处理时间：', result.timing.total_time_formatted);
        
        // 可以下载字幕文件
        // downloadSubtitle(result.file_id, result.srt_path);
      } else if (status.state === 'FAILURE') {
        clearInterval(interval);
        console.error('转录失败：', status.status);
      }
    }, 2000); // 每2秒查询一次
    
  } catch (error) {
    console.error('错误：', error);
  }
}
```

---

## 📈 性能指标

### 处理速度参考
- **音频文件**：通常 1:2 到 1:3 的处理比例（1分钟音频需要2-3分钟处理）
- **视频文件**：额外增加音频提取时间（通常几秒到几十秒）
- **模型大小影响**：
  - `whisper-tiny`: 最快，准确度较低
  - `whisper-base`: 平衡选择
  - `whisper-large-v3-turbo`: 当前使用，高准确度

### 优化建议
- 对于实时性要求高的场景，可以调整为 `whisper-base` 模型
- 可以通过调整 `BATCH_SIZE` 来平衡速度和内存使用
- 字幕分段参数可以根据具体需求调整

---

## 🔮 后续优化方向

1. **WebSocket 支持**：实时进度推送
2. **多语言支持**：语言检测和多语言转录
3. **说话人识别**：区分不同说话人
4. **字幕样式**：支持更多字幕格式和样式
5. **批量处理**：支持多文件批量上传
6. **缓存机制**：重复文件的智能缓存

---

*文档更新时间：2025年6月16日 23:15*
