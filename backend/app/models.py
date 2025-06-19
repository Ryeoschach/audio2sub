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
