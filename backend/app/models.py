"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class ModelSize(str, Enum):
    """支持的 Whisper 模型大小"""
    TINY = "tiny"
    TINY_EN = "tiny.en"
    BASE = "base"
    BASE_EN = "base.en"
    SMALL = "small"
    SMALL_EN = "small.en"
    MEDIUM = "medium"
    MEDIUM_EN = "medium.en"
    LARGE_V1 = "large-v1"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"
    LARGE_V3_TURBO = "large-v3-turbo"

class OutputFormat(str, Enum):
    """输出格式选项"""
    SRT = "srt"
    VTT = "vtt"
    BOTH = "both"

class LanguageCode(str, Enum):
    """支持的语言代码"""
    AUTO = "auto"
    ZH = "zh"
    EN = "en"
    JA = "ja"
    KO = "ko"
    FR = "fr"
    DE = "de"
    ES = "es"
    RU = "ru"
    IT = "it"
    PT = "pt"

class TranscriptionRequest(BaseModel):
    """转录请求参数"""
    model: ModelSize = Field(
        default=ModelSize.BASE,
        description="Whisper 模型大小，影响准确度和速度"
    )
    language: LanguageCode = Field(
        default=LanguageCode.AUTO,
        description="音频语言，auto 为自动检测"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.BOTH,
        description="输出格式：srt, vtt 或 both"
    )
    task: str = Field(
        default="transcribe",
        description="任务类型：transcribe(转录) 或 translate(翻译为英文)"
    )

class TranscriptionResponse(BaseModel):
    """转录响应"""
    task_id: str = Field(description="任务ID，用于查询状态")
    file_id: str = Field(description="文件ID")
    message: str = Field(description="响应消息")
    model_used: str = Field(description="使用的模型")
    estimated_time: Optional[int] = Field(description="预估处理时间（秒）")

class ModelInfo(BaseModel):
    """模型信息"""
    name: str = Field(description="模型名称")
    size: str = Field(description="模型文件大小")
    speed: str = Field(description="相对速度")
    accuracy: str = Field(description="准确度描述")
    use_case: str = Field(description="适用场景")

class ModelsListResponse(BaseModel):
    """模型列表响应"""
    models: List[ModelInfo] = Field(description="支持的模型列表")
    default_model: str = Field(description="默认模型")

class TaskStatus(BaseModel):
    """任务状态"""
    state: str = Field(description="任务状态")
    current: Optional[int] = Field(description="当前进度")
    total: Optional[int] = Field(description="总进度")
    status: Optional[str] = Field(description="状态描述")
    result: Optional[dict] = Field(description="结果信息")

# 批量处理相关模型
class BatchTaskInfo(BaseModel):
    """批量任务中的单个文件信息"""
    file_id: str = Field(description="文件ID")
    filename: str = Field(description="原始文件名")
    task_id: str = Field(description="单个文件的任务ID")
    status: str = Field(description="任务状态", default="PENDING")
    progress: Optional[int] = Field(description="进度百分比", default=0)
    estimated_time: Optional[int] = Field(description="预估处理时间（秒）")
    error: Optional[str] = Field(description="错误信息", default=None)

class BatchTranscriptionRequest(BaseModel):
    """批量转录请求参数"""
    model: ModelSize = Field(
        default=ModelSize.BASE,
        description="Whisper 模型大小，影响准确度和速度"
    )
    language: LanguageCode = Field(
        default=LanguageCode.AUTO,
        description="音频语言，auto 为自动检测"
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.BOTH,
        description="输出格式：srt, vtt 或 both"
    )
    task: str = Field(
        default="transcribe",
        description="任务类型：transcribe(转录) 或 translate(翻译为英文)"
    )
    concurrent_limit: Optional[int] = Field(
        default=3,
        description="并发处理文件数量限制",
        ge=1,
        le=10
    )

class BatchTranscriptionResponse(BaseModel):
    """批量转录响应"""
    batch_id: str = Field(description="批量任务ID")
    message: str = Field(description="响应消息")
    total_files: int = Field(description="总文件数量")
    tasks: List[BatchTaskInfo] = Field(description="各个文件的任务信息")
    model_used: str = Field(description="使用的模型")
    estimated_total_time: int = Field(description="总预估处理时间（秒）")

class BatchTaskStatus(BaseModel):
    """批量任务状态"""
    batch_id: str = Field(description="批量任务ID")
    total_files: int = Field(description="总文件数量")
    completed_files: int = Field(description="已完成文件数量")
    failed_files: int = Field(description="失败文件数量")
    progress_percentage: float = Field(description="总体进度百分比")
    overall_status: str = Field(description="整体状态: PENDING, PROCESSING, COMPLETED, FAILED")
    tasks: List[BatchTaskInfo] = Field(description="各个文件的详细状态")
    start_time: Optional[str] = Field(description="开始时间")
    estimated_completion_time: Optional[str] = Field(description="预估完成时间")

class BatchResultSummary(BaseModel):
    """批量处理结果汇总"""
    batch_id: str = Field(description="批量任务ID")
    total_files: int = Field(description="总文件数量")
    successful_files: int = Field(description="成功文件数量")
    failed_files: int = Field(description="失败文件数量")
    total_processing_time: float = Field(description="总处理时间（秒）")
    results: List[dict] = Field(description="成功文件的结果详情")
    errors: List[dict] = Field(description="失败文件的错误信息")
