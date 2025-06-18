"""
混合Whisper处理器
结合transformers（使用MPS）和faster-whisper（使用CPU）的优势
"""
import time
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

# transformers相关
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import librosa

# faster-whisper相关
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("Warning: faster-whisper not available")

from config import get_device_config, MODEL_CONFIG, SUBTITLE_CONFIG

@dataclass
class TranscriptionSegment:
    """转录片段数据结构"""
    start: float
    end: float
    text: str
    confidence: Optional[float] = None
    
    @property
    def duration(self) -> float:
        return self.end - self.start

class HybridWhisperProcessor:
    """混合Whisper处理器"""
    
    def __init__(self, use_transformers: bool = True, use_faster_whisper: bool = True):
        self.device_config = get_device_config()
        self.use_transformers = use_transformers and self.device_config["mps_available"]
        self.use_faster_whisper = use_faster_whisper and FASTER_WHISPER_AVAILABLE
        
        # 初始化transformers模型（使用MPS）
        if self.use_transformers:
            print("Initializing transformers Whisper model on MPS...")
            self.transformers_processor = WhisperProcessor.from_pretrained(f"openai/whisper-{MODEL_CONFIG['whisper_model']}")
            self.transformers_model = WhisperForConditionalGeneration.from_pretrained(f"openai/whisper-{MODEL_CONFIG['whisper_model']}")
            self.transformers_model.to(self.device_config["transformers_device"])
            print(f"Transformers model loaded on {self.device_config['transformers_device']}")
        
        # 初始化faster-whisper模型（使用CPU）
        if self.use_faster_whisper:
            print("Initializing faster-whisper model on CPU...")
            from config import FASTER_WHISPER_MODEL_PATH
            
            # 尝试使用本地模型，失败则下载
            try:
                if FASTER_WHISPER_MODEL_PATH.exists():
                    model_path = str(FASTER_WHISPER_MODEL_PATH)
                    print(f"Using local model: {model_path}")
                else:
                    model_path = MODEL_CONFIG['whisper_model']
                    print(f"Downloading model: {model_path}")
                
                self.faster_whisper_model = WhisperModel(
                    model_path,
                    device=self.device_config["faster_whisper_device"],
                    compute_type=self.device_config["faster_whisper_compute_type"]
                )
                print(f"Faster-whisper model loaded on {self.device_config['faster_whisper_device']}")
            except Exception as e:
                print(f"Failed to load faster-whisper model: {e}")
                self.use_faster_whisper = False
    
    def transcribe_with_transformers(self, audio_path: str) -> List[TranscriptionSegment]:
        """使用transformers进行转录（支持MPS加速）"""
        if not self.use_transformers:
            return []
        
        print("Transcribing with transformers...")
        start_time = time.time()
        
        # 加载音频
        audio, sr = librosa.load(audio_path, sr=16000)
        
        # 处理音频
        inputs = self.transformers_processor(audio, sampling_rate=16000, return_tensors="pt")
        inputs = {k: v.to(self.device_config["transformers_device"]) for k, v in inputs.items()}
        
        # 生成转录
        with torch.no_grad():
            forced_decoder_ids = self.transformers_processor.get_decoder_prompt_ids(
                language=MODEL_CONFIG["language"], 
                task=MODEL_CONFIG["task"]
            )
            predicted_ids = self.transformers_model.generate(
                inputs["input_features"],
                forced_decoder_ids=forced_decoder_ids,
                temperature=MODEL_CONFIG["temperature"]
            )
        
        # 解码文本
        transcription = self.transformers_processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        # 注意：transformers的基础模型不提供时间戳，这里创建一个简单的分段
        duration = len(audio) / sr
        segments = [TranscriptionSegment(
            start=0.0,
            end=duration,
            text=transcription.strip()
        )]
        
        elapsed = time.time() - start_time
        print(f"Transformers transcription completed in {elapsed:.2f}s")
        print(f"Result: {transcription[:100]}...")
        
        return segments
    
    def transcribe_with_faster_whisper(self, audio_path: str) -> List[TranscriptionSegment]:
        """使用faster-whisper进行转录（提供精确时间戳）"""
        if not self.use_faster_whisper:
            return []
        
        print("Transcribing with faster-whisper...")
        start_time = time.time()
        
        segments_list = []
        segments, info = self.faster_whisper_model.transcribe(
            audio_path,
            language=MODEL_CONFIG["language"],
            task=MODEL_CONFIG["task"],
            temperature=MODEL_CONFIG["temperature"],
            no_speech_threshold=MODEL_CONFIG["no_speech_threshold"],
            logprob_threshold=MODEL_CONFIG["logprob_threshold"],
            compression_ratio_threshold=MODEL_CONFIG["compression_ratio_threshold"],
            word_timestamps=True
        )
        
        for segment in segments:
            segments_list.append(TranscriptionSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text.strip(),
                confidence=segment.avg_logprob if hasattr(segment, 'avg_logprob') else None
            ))
        
        elapsed = time.time() - start_time
        print(f"Faster-whisper transcription completed in {elapsed:.2f}s")
        print(f"Generated {len(segments_list)} segments")
        print(f"Language detected: {info.language} (probability: {info.language_probability:.2f})")
        
        return segments_list
    
    def process_audio(self, audio_path: str) -> Dict[str, List[TranscriptionSegment]]:
        """处理音频文件，返回两种方法的结果"""
        results = {}
        
        if self.use_transformers:
            results["transformers"] = self.transcribe_with_transformers(audio_path)
        
        if self.use_faster_whisper:
            results["faster_whisper"] = self.transcribe_with_faster_whisper(audio_path)
        
        return results

def split_text_for_subtitles(text: str, max_chars: int = SUBTITLE_CONFIG["max_chars_per_line"]) -> List[str]:
    """智能分割文本用于字幕显示"""
    if len(text) <= max_chars:
        return [text]
    
    # 中文智能分割
    lines = []
    current_line = ""
    
    # 按标点符号分割
    import re
    sentences = re.split(r'([，。！？；：])', text)
    
    for i in range(0, len(sentences), 2):
        sentence = sentences[i] if i < len(sentences) else ""
        punct = sentences[i + 1] if i + 1 < len(sentences) else ""
        full_sentence = sentence + punct
        
        if len(current_line + full_sentence) <= max_chars:
            current_line += full_sentence
        else:
            if current_line:
                lines.append(current_line.strip())
                current_line = full_sentence
            else:
                # 如果单个句子太长，强制分割
                while len(full_sentence) > max_chars:
                    lines.append(full_sentence[:max_chars])
                    full_sentence = full_sentence[max_chars:]
                current_line = full_sentence
    
    if current_line:
        lines.append(current_line.strip())
    
    return lines

def optimize_segments_for_subtitles(segments: List[TranscriptionSegment]) -> List[TranscriptionSegment]:
    """优化segments用于字幕显示"""
    optimized = []
    
    for segment in segments:
        # 分割长文本
        lines = split_text_for_subtitles(segment.text, SUBTITLE_CONFIG["max_chars_per_line"])
        
        if len(lines) == 1:
            # 单行字幕
            optimized.append(segment)
        else:
            # 多行字幕，按时间均匀分配
            duration_per_line = segment.duration / len(lines)
            
            for i, line in enumerate(lines):
                start_time = segment.start + i * duration_per_line
                end_time = segment.start + (i + 1) * duration_per_line
                
                # 确保不超过最大持续时间
                if end_time - start_time > SUBTITLE_CONFIG["max_duration"]:
                    end_time = start_time + SUBTITLE_CONFIG["max_duration"]
                
                # 确保不少于最小持续时间
                if end_time - start_time < SUBTITLE_CONFIG["min_duration"]:
                    end_time = start_time + SUBTITLE_CONFIG["min_duration"]
                
                optimized.append(TranscriptionSegment(
                    start=start_time,
                    end=end_time,
                    text=line,
                    confidence=segment.confidence
                ))
    
    return optimized

if __name__ == "__main__":
    # 测试混合处理器
    processor = HybridWhisperProcessor()
    print(f"Transformers available: {processor.use_transformers}")
    print(f"Faster-whisper available: {processor.use_faster_whisper}")
