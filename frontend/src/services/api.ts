import axios, { AxiosResponse } from 'axios';

// 定义 API 响应类型
export interface ModelInfo {
  name: string;
  size: string;
  speed: string;
  accuracy: string;
  use_case: string;
}

export interface ModelsResponse {
  models: ModelInfo[];
  default_model: string;
}

export interface UploadRequest {
  model?: string;
  language?: string;
  output_format?: string;
  task?: string;
}

export interface UploadResponse {
  task_id: string;
  file_id: string;
  message: string;
  model_used: string;
  estimated_time: number;
}

export interface TaskStatus {
  state: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  status?: string;
  result?: {
    status: string;
    files: Array<{
      type: string;
      filename: string;
      path: string;
    }>;
    original_filename: string;
    file_id: string;
    full_text: string;
    transcription_params: {
      model: string;
      language: string;
      output_format: string;
      task_type: string;
    };
    timing: {
      total_time: number;
      total_time_formatted: string;
      transcription_time: number;
    };
  };
}

export interface HealthStatus {
  status: string;
  config?: string;
  redis?: string;
  deployment?: {
    mode: string;
    device: string;
    model: string;
  };
  version?: string;
}

/**
 * Audio2Sub API 客户端类
 */
class Audio2SubAPI {
  private baseURL: string;

  constructor(baseURL = '/api') {
    this.baseURL = baseURL;
  }

  /**
   * 健康检查
   */
  async healthCheck(): Promise<HealthStatus> {
    try {
      const response: AxiosResponse<HealthStatus> = await axios.get(`${this.baseURL}/health`);
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  /**
   * 获取可用模型列表
   */
  async getModels(): Promise<ModelsResponse> {
    try {
      const response: AxiosResponse<ModelsResponse> = await axios.get(`${this.baseURL}/models/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get models:', error);
      throw error;
    }
  }

  /**
   * 上传文件进行转录
   */
  async uploadFile(
    file: File,
    options: UploadRequest = {}
  ): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      // 添加可选参数
      if (options.model) formData.append('model', options.model);
      if (options.language) formData.append('language', options.language);
      if (options.output_format) formData.append('output_format', options.output_format);
      if (options.task) formData.append('task', options.task);

      const response: AxiosResponse<UploadResponse> = await axios.post(
        `${this.baseURL}/upload/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      return response.data;
    } catch (error) {
      console.error('File upload failed:', error);
      throw error;
    }
  }

  /**
   * 检查任务状态
   */
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    try {
      const response: AxiosResponse<TaskStatus> = await axios.get(
        `${this.baseURL}/status/${taskId}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get task status:', error);
      throw error;
    }
  }

  /**
   * 等待任务完成（带进度回调）
   */
  async waitForCompletion(
    taskId: string,
    maxWait = 300000, // 5分钟
    onProgress?: (status: TaskStatus) => void
  ): Promise<TaskStatus['result']> {
    const startTime = Date.now();
    const checkInterval = 3000; // 3秒检查一次

    while (Date.now() - startTime < maxWait) {
      try {
        const status = await this.getTaskStatus(taskId);

        if (onProgress) {
          onProgress(status);
        }

        if (status.state === 'SUCCESS') {
          return status.result;
        } else if (status.state === 'FAILURE') {
          throw new Error(status.status || 'Task failed');
        }

        // 等待下次检查
        await new Promise(resolve => setTimeout(resolve, checkInterval));
      } catch (error) {
        console.error('Status check error:', error);
        await new Promise(resolve => setTimeout(resolve, checkInterval));
      }
    }

    throw new Error('Task timeout');
  }
}

// 创建单例实例
export const audio2subAPI = new Audio2SubAPI();

export default Audio2SubAPI;
