from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
import os
import platform
import multiprocessing
import subprocess
import shutil
import logging

# 全局logger
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    APP_NAME: str = "Audio2Sub Backend"
    DEBUG: bool = True

    # Default to local Redis settings
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 16379  # 使用Redis默认端口
    REDIS_PASSWORD: str | None = None  # 使用密码
    REDIS_DB: int = 0

    # Default Celery broker and result backend to local Redis with password
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Whisper.cpp executable path
    WHISPER_CPP_PATH: str = "/usr/local/bin/whisper-cli"
    
    # Whisper.cpp model configuration
    MODEL_PATH: str = "models/ggml-base.bin"  # Path to whisper.cpp model file
    MODEL_NAME: str = "base"  # Model size: tiny, base, small, medium, large-v1, large-v2, large-v3
    
    # Processing device configuration
    # whisper.cpp supports: "cpu", "cuda", "metal" (for Apple Silicon)
    WHISPER_DEVICE: str = "auto"  # auto, cpu, cuda, metal
    
    # Deployment mode: docker, hybrid, native
    DEPLOYMENT_MODE: str = "auto"  # Will be auto-detected
    
    # Whisper.cpp processing parameters
    WHISPER_THREADS: int = 0  # 0 = auto-detect optimal thread count
    WHISPER_PROCESSORS: int = 1  # Number of processors to use
    WHISPER_COMPUTE_TYPE: str = "auto"  # auto, int8, float16, float32
    
    # Language and task settings
    WHISPER_LANGUAGE: str = "zh"  # "auto" for auto-detection, or specific language code like "zh" for Chinese
    WHISPER_TASK: str = "transcribe"  # "transcribe" or "translate"
    
    # Audio processing settings
    WHISPER_MAX_LEN: int = 0  # Maximum length to process (0 = no limit)
    WHISPER_SPLIT_ON_WORD: bool = True  # Split on word boundaries
    WHISPER_WORD_TIMESTAMPS: bool = True  # Enable word-level timestamps
    
    # Model performance settings
    WHISPER_TEMPERATURE: float = 0.0  # Temperature for sampling (0.0 = deterministic)
    WHISPER_BEST_OF: int = 5  # Number of candidates to consider
    
    # Deployment detection and configuration
    _deployment_mode: Optional[str] = None
    _whisper_path: Optional[str] = None
    _model_path: Optional[str] = None
    _device_type: Optional[str] = None
    _initialized: bool = False
    
    def model_post_init(self, __context):
        """Initialize settings with dynamic detection after model creation"""
        if not self._initialized:
            self._setup_logging()
            self._detect_and_configure()
            self._initialized = True
    
    def _setup_logging(self):
        """Setup logging for configuration detection"""
        logging.basicConfig(level=logging.INFO)
        # 使用全局logger，避免Pydantic验证问题
        global logger
        logger = logging.getLogger(__name__)
    
    def _detect_and_configure(self):
        """Detect system environment and configure automatically"""
        try:
            # Detect deployment mode
            self._deployment_mode = self._detect_deployment_mode()
            
            # Detect optimal device
            self._device_type = self._get_optimal_device()
            
            # Find whisper executable
            self._whisper_path = self._find_whisper_executable()
            
            # Find model file
            self._model_path = self._find_model_file()
            
            # Apply detected configuration
            self._apply_configuration()
            
            logger.info(f"智能配置完成:")
            logger.info(f"  部署模式: {self._deployment_mode}")
            logger.info(f"  设备类型: {self._device_type}")
            logger.info(f"  Whisper路径: {self._whisper_path}")
            logger.info(f"  模型路径: {self._model_path}")
            
        except Exception as e:
            logger.warning(f"自动配置失败，使用默认配置: {e}")
    
    def _detect_deployment_mode(self) -> str:
        """智能检测部署模式"""
        # 检查环境变量强制设置
        env_mode = os.getenv('DEPLOYMENT_MODE')
        if env_mode:
            return env_mode.lower()
        
        # 检测Docker环境
        in_docker = os.path.exists('/.dockerenv') or os.getenv('DOCKER_ENV') == '1'
        
        # 检测宿主机whisper.cpp可用性
        host_whisper_available = self._check_host_whisper()
        
        # 根据环境自动选择
        if in_docker:
            return "cpu"  # 容器内默认CPU模式
        elif host_whisper_available:
            return "hybrid"  # 宿主机有whisper.cpp，使用混合模式
        else:
            return "native"  # 完全原生模式
    
    def _get_optimal_device(self) -> str:
        """检测最佳推理设备"""
        # 检查环境变量强制设置
        env_device = os.getenv('WHISPER_DEVICE')
        if env_device and env_device != 'auto':
            return env_device.lower()
        
        return self._detect_host_device()
    
    def _detect_host_device(self) -> str:
        """检测宿主机最佳设备"""
        system = platform.system().lower()
        
        if system == "darwin":  # macOS
            # 检测Apple Silicon
            try:
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and "Apple" in result.stdout:
                    return "mps"  # Apple Silicon支持MPS
                else:
                    return "cpu"  # Intel Mac使用CPU
            except:
                return "cpu"
                
        elif system == "linux":
            # 检测NVIDIA GPU
            try:
                result = subprocess.run(['nvidia-smi'], capture_output=True, timeout=5)
                if result.returncode == 0:
                    return "cuda"
            except:
                pass
            return "cpu"
        else:
            return "cpu"
    
    def _check_host_whisper(self) -> bool:
        """检查宿主机whisper.cpp可用性"""
        try:
            whisper_path = self._find_whisper_executable()
            return whisper_path is not None and os.path.isfile(whisper_path)
        except:
            return False
    
    def _find_whisper_executable(self) -> Optional[str]:
        """查找whisper可执行文件"""
        # 检查环境变量
        env_path = os.getenv('HOST_WHISPER_CPP_PATH')
        if env_path and os.path.isfile(env_path):
            return env_path
        
        # 常见路径搜索
        search_paths = [
            "/Users/creed/workspace/sourceCode/whisper.cpp/build/bin/whisper-cli",
            "/Users/creed/workspace/sourceCode/whisper.cpp/build/bin/main",
            "./whisper.cpp/build/bin/whisper-cli",
            "./whisper.cpp/build/bin/main",
            "/usr/local/bin/whisper-cli",
            "/usr/local/bin/whisper",
            "/opt/homebrew/bin/whisper-cli",
            "/opt/homebrew/bin/whisper",
        ]
        
        for path in search_paths:
            if os.path.isfile(path):
                return path
        
        # 检查PATH中的命令
        for cmd in ['whisper-cli', 'whisper']:
            path = shutil.which(cmd)
            if path:
                return path
        
        return None
    
    def _find_model_file(self) -> Optional[str]:
        """查找模型文件"""
        # 检查环境变量
        env_path = os.getenv('HOST_MODEL_PATH')
        if env_path and os.path.isfile(env_path):
            return env_path
        
        # 常见模型路径搜索
        model_dirs = [
            "/Users/creed/workspace/sourceCode/whisper.cpp/models",
            "./whisper.cpp/models",
            "/usr/local/share/whisper/models",
            "/opt/homebrew/share/whisper/models",
            "./models"
        ]
        
        model_files = [
            "ggml-base.bin",
            "ggml-small.bin", 
            "ggml-tiny.bin",
            "ggml-medium.bin"
        ]
        
        for model_dir in model_dirs:
            if os.path.isdir(model_dir):
                for model_file in model_files:
                    full_path = os.path.join(model_dir, model_file)
                    if os.path.isfile(full_path):
                        return full_path
        
        return None
    
    def _apply_configuration(self):
        """应用检测到的配置"""
        # 设置设备类型
        if self._device_type:
            self.WHISPER_DEVICE = self._device_type
        
        # 设置部署模式
        if self._deployment_mode:
            self.DEPLOYMENT_MODE = self._deployment_mode
        
        # 设置whisper路径
        if self._whisper_path:
            self.WHISPER_CPP_PATH = self._whisper_path
        
        # 设置模型路径
        if self._model_path:
            self.MODEL_PATH = self._model_path
        
        # 根据部署模式调整Redis配置
        if self._deployment_mode == "hybrid":
            # 混合模式使用容器化Redis
            self.REDIS_HOST = "audio2sub_redis_hybrid"
            self.REDIS_PORT = 6379
        elif self._deployment_mode == "native":
            # 原生模式使用本地Redis或容器Redis
            self.REDIS_HOST = "localhost"
            self.REDIS_PORT = 16379
    
    @property
    def is_whisper_available(self) -> bool:
        """检查whisper是否可用"""
        return (self._whisper_path is not None and 
                os.path.isfile(self._whisper_path) and
                self._model_path is not None and
                os.path.isfile(self._model_path))
    
    @property 
    def deployment_info(self) -> Dict[str, Any]:
        """获取部署信息"""
        return {
            "deployment_mode": self._deployment_mode,
            "device_type": self._device_type,
            "whisper_path": self._whisper_path,
            "model_path": self._model_path,
            "whisper_available": self.is_whisper_available,  # 这是一个属性，应该自动调用
            "redis_host": self.REDIS_HOST,
            "redis_port": self.REDIS_PORT
        }

    class Config:
        env_file = ".env"
    WHISPER_BEAM_SIZE: int = 5  # Beam size for beam search
    
    # Subtitle generation settings
    MAX_SUBTITLE_DURATION: int = 4  # Maximum duration for a single subtitle entry (seconds)
    MAX_WORDS_PER_SUBTITLE: int = 8  # Maximum number of words per subtitle entry
    MAX_CHARS_PER_SUBTITLE: int = 50  # Maximum number of characters per subtitle entry
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # File upload and results directories
    UPLOAD_DIR: str = "uploads"
    RESULTS_DIR: str = "results"

    class Config:
        env_file = ".env" # This will override defaults if .env file exists
        env_file_encoding = "utf-8"
        extra = "ignore" # Add this to ignore extra fields not defined in Settings

    def __init__(self, **values):
        super().__init__(**values)
        
        # 动态配置设置
        self._setup_dynamic_config()
        
        # Construct Celery URLs after other base settings are loaded
        if self.REDIS_PASSWORD:
            self.CELERY_BROKER_URL = f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            self.CELERY_RESULT_BACKEND = f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            self.CELERY_BROKER_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            self.CELERY_RESULT_BACKEND = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        
        # Create upload and results directories
        import os
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.RESULTS_DIR, exist_ok=True)
    
    def _setup_dynamic_config(self):
        """根据运行环境动态配置设备和路径"""
        # 检测运行环境
        if self.DEPLOYMENT_MODE == "auto":
            self.DEPLOYMENT_MODE = self._detect_deployment_mode()
        
        # 设置最优设备
        if self.WHISPER_DEVICE == "auto":
            self.WHISPER_DEVICE = self._get_optimal_device()
        
        # 设置最优配置参数
        if self.WHISPER_COMPUTE_TYPE == "auto":
            config = self._get_optimal_config()
            self.WHISPER_THREADS = config["threads"]
            self.WHISPER_PROCESSORS = config["processors"]
            self.WHISPER_COMPUTE_TYPE = config["compute_type"]
        
        # 根据部署模式调整路径
        self._adjust_paths_for_deployment()
    
    def _detect_deployment_mode(self) -> str:
        """检测当前部署模式"""
        # 优先使用环境变量
        env_mode = os.getenv('DEPLOYMENT_MODE')
        if env_mode:
            return env_mode
            
        if os.path.exists('/.dockerenv'):
            # Docker环境
            return "docker"
        else:
            return "native"
    
    def _get_optimal_device(self) -> str:
        """根据运行环境选择最佳设备"""
        # 优先使用环境变量设置
        env_device = os.getenv('WHISPER_DEVICE')
        if env_device and env_device != "auto":
            return env_device
        
        if self.DEPLOYMENT_MODE == "docker":
            # Docker环境 - 检查GPU支持
            if os.path.exists('/usr/local/cuda') and os.getenv('NVIDIA_VISIBLE_DEVICES'):
                return "cuda"
            else:
                return "cpu"
        elif self.DEPLOYMENT_MODE == "hybrid":
            # 混合模式 - 使用宿主机设备检测
            return self._detect_host_device()
        else:
            # 宿主机环境 - 直接检测
            return self._detect_host_device()
    
    def _detect_host_device(self) -> str:
        """检测宿主机最佳设备"""
        system = platform.system()
        
        if system == "Darwin":
            # macOS - 检查是否支持MPS/Metal
            try:
                import subprocess
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"], 
                    capture_output=True, text=True, timeout=5
                )
                if "Apple" in result.stdout:
                    return "mps"  # Apple Silicon支持Metal Performance Shaders
                else:
                    return "cpu"  # Intel Mac
            except:
                return "cpu"
        elif system == "Linux":
            # Linux - 检查CUDA支持
            if (os.path.exists('/usr/local/cuda') or 
                os.path.exists('/opt/cuda') or 
                os.path.exists('/usr/lib/cuda')):
                return "cuda"
            else:
                return "cpu"
        else:
            return "cpu"
    
    def _get_optimal_config(self) -> Dict[str, Any]:
        """根据设备返回最优配置"""
        device = getattr(self, 'WHISPER_DEVICE', 'cpu')
        cpu_count = multiprocessing.cpu_count()
        
        if device == "cuda":
            return {
                "threads": 1,
                "processors": 1,
                "compute_type": "float16"
            }
        elif device == "mps":
            return {
                "threads": 0,  # 使用所有核心
                "processors": 1,
                "compute_type": "float32"
            }
        else:  # CPU
            return {
                "threads": 0,  # 使用所有核心
                "processors": min(cpu_count, 4),  # 限制最大进程数
                "compute_type": "int8"  # CPU优化
            }
    
    def _adjust_paths_for_deployment(self):
        """根据部署模式调整路径"""
        if self.DEPLOYMENT_MODE == "hybrid":
            # 混合模式 - 优先使用宿主机路径
            host_whisper_path = os.getenv('HOST_WHISPER_CPP_PATH')
            if host_whisper_path and os.path.exists(host_whisper_path):
                self.WHISPER_CPP_PATH = host_whisper_path
            
            host_model_path = os.getenv('HOST_MODEL_PATH')
            if host_model_path and os.path.exists(host_model_path):
                self.MODEL_PATH = host_model_path
        
        elif self.DEPLOYMENT_MODE == "native":
            # 本地模式 - 自动检测whisper命令路径
            whisper_path = self._find_whisper_executable()
            if whisper_path:
                self.WHISPER_CPP_PATH = whisper_path
            
            # 本地模式下尝试找到模型文件
            model_path = self._find_model_file()
            if model_path:
                self.MODEL_PATH = model_path
        
        # 如果是Docker环境，调整Redis主机
        if self.DEPLOYMENT_MODE == "docker":
            # Docker环境中Redis通常是服务名
            if self.REDIS_HOST in ["127.0.0.1", "localhost"]:
                self.REDIS_HOST = "redis"
                self.REDIS_PORT = 6379  # Docker中使用标准端口
    
    def get_whisper_command_args(self, input_file: str, output_file: str) -> List[str]:
        """获取whisper命令行参数"""
        args = [
            self.WHISPER_CPP_PATH,
            "-m", self.MODEL_PATH,
            "-f", input_file,
            "-osrt",  # 输出SRT格式
            "-of", output_file,
        ]
        
        # 添加语言设置
        if self.WHISPER_LANGUAGE and self.WHISPER_LANGUAGE != "auto":
            args.extend(["-l", self.WHISPER_LANGUAGE])
        
        # 添加线程设置
        if self.WHISPER_THREADS > 0:
            args.extend(["-t", str(self.WHISPER_THREADS)])
        
        # 添加处理器设置
        if self.WHISPER_PROCESSORS > 1:
            args.extend(["-p", str(self.WHISPER_PROCESSORS)])
        
        # 添加计算类型参数
        if self.WHISPER_COMPUTE_TYPE == "float16":
            args.append("-fp16")
        elif self.WHISPER_COMPUTE_TYPE == "int8":
            args.append("-q")
        
        return args
    
    def get_deployment_info(self) -> Dict[str, Any]:
        """获取部署信息用于调试和健康检查"""
        return {
            "deployment_mode": self.DEPLOYMENT_MODE,
            "device": self.WHISPER_DEVICE,
            "threads": self.WHISPER_THREADS,
            "processors": self.WHISPER_PROCESSORS,
            "compute_type": self.WHISPER_COMPUTE_TYPE,
            "whisper_path": self.WHISPER_CPP_PATH,
            "model_path": self.MODEL_PATH,
            "platform": platform.system(),
            "cpu_count": multiprocessing.cpu_count(),
            "in_docker": os.path.exists('/.dockerenv'),
            "redis_host": self.REDIS_HOST,
            "redis_port": self.REDIS_PORT
        }

    class Config:
        env_file = ".env"
