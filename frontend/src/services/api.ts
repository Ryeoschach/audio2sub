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

// 批量处理相关类型定义
export interface BatchTaskInfo {
  file_id: string;
  filename: string;
  task_id: string;
  status: string;
  progress: number;
  estimated_time?: number;
  error?: string;
}

export interface BatchUploadRequest {
  model?: string;
  language?: string;
  output_format?: string;
  task?: string;
  concurrent_limit?: number;
}

export interface BatchUploadResponse {
  batch_id: string;
  message: string;
  total_files: number;
  tasks: BatchTaskInfo[];
  model_used: string;
  estimated_total_time: number;
}

export interface BatchTaskStatus {
  batch_id: string;
  total_files: number;
  completed_files: number;
  failed_files: number;
  progress_percentage: number;
  overall_status: string;
  tasks: BatchTaskInfo[];
  start_time?: string;
  estimated_completion_time?: string;
}

export interface BatchResultSummary {
  batch_id: string;
  total_files: number;
  successful_files: number;
  failed_files: number;
  total_processing_time: number;
  results: Array<{
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
  }>;
  errors: Array<{
    file_id: string;
    filename: string;
    error: string;
  }>;
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

  /**
   * 批量上传文件进行转录
   */
  async uploadFiles(
    files: File[],
    options: BatchUploadRequest = {}
  ): Promise<BatchUploadResponse> {
    try {
      const formData = new FormData();
      
      // 添加文件
      files.forEach(file => {
        formData.append('files', file);
      });
      
      // 添加可选参数
      if (options.model) formData.append('model', options.model);
      if (options.language) formData.append('language', options.language);
      if (options.output_format) formData.append('output_format', options.output_format);
      if (options.task) formData.append('task', options.task);
      if (options.concurrent_limit) formData.append('concurrent_limit', String(options.concurrent_limit));

      const response: AxiosResponse<BatchUploadResponse> = await axios.post(
        `${this.baseURL}/batch-upload/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      return response.data;
    } catch (error) {
      console.error('Batch file upload failed:', error);
      throw error;
    }
  }

  /**
   * 检查批量任务状态
   */
  async getBatchTaskStatus(batchId: string): Promise<BatchTaskStatus> {
    try {
      const response: AxiosResponse<BatchTaskStatus> = await axios.get(
        `${this.baseURL}/batch-status/${batchId}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get batch task status:', error);
      throw error;
    }
  }

  /**
   * 获取批量任务结果汇总
   */
  async getBatchResultSummary(batchId: string): Promise<BatchResultSummary> {
    try {
      const response: AxiosResponse<BatchResultSummary> = await axios.get(
        `${this.baseURL}/batch-result/${batchId}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to get batch result summary:', error);
      throw error;
    }
  }

  /**
   * 等待批量任务完成（带进度回调）
   */
  async waitForBatchCompletion(
    batchId: string,
    maxWait = 300000, // 5分钟
    onProgress?: (status: BatchTaskStatus) => void
  ): Promise<BatchResultSummary> {
    const startTime = Date.now();
    const checkInterval = 3000; // 3秒检查一次

    while (Date.now() - startTime < maxWait) {
      try {
        const status = await this.getBatchTaskStatus(batchId);

        if (onProgress) {
          onProgress(status);
        }

        if (status.overall_status === 'COMPLETED') {
          // 获取批量任务的结果汇总
          return await this.getBatchResultSummary(batchId);
        } else if (status.overall_status === 'FAILED') {
          throw new Error('Batch task failed');
        }

        // 等待下次检查
        await new Promise(resolve => setTimeout(resolve, checkInterval));
      } catch (error) {
        console.error('Batch status check error:', error);
        await new Promise(resolve => setTimeout(resolve, checkInterval));
      }
    }

    throw new Error('Batch task timeout');
  }
}

// 创建单例实例
export const audio2subAPI = new Audio2SubAPI();

export default Audio2SubAPI;
