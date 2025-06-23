import React from 'react';

export interface TranscriptionOptions {
  language: string;
  output_format: string;
  task: string;
}

interface TranscriptionOptionsProps {
  options: TranscriptionOptions;
  onOptionsChange: (options: TranscriptionOptions) => void;
  disabled?: boolean;
}

const TranscriptionOptionsComponent: React.FC<TranscriptionOptionsProps> = ({
  options,
  onOptionsChange,
  disabled = false
}) => {
  const handleChange = (field: keyof TranscriptionOptions, value: string) => {
    onOptionsChange({
      ...options,
      [field]: value
    });
  };

  const languageOptions = [
    { value: 'auto', label: '自动检测 (可能不准确)' },
    { value: 'zh', label: '中文 (默认)' },
    { value: 'en', label: '英文' },
    { value: 'ja', label: '日文' },
    { value: 'ko', label: '韩文' },
    { value: 'fr', label: '法文' },
    { value: 'de', label: '德文' },
    { value: 'es', label: '西班牙文' },
    { value: 'it', label: '意大利文' },
    { value: 'ru', label: '俄文' },
  ];

  const outputFormatOptions = [
    { value: 'both', label: 'SRT + VTT (推荐)' },
    { value: 'srt', label: '仅 SRT 格式' },
    { value: 'vtt', label: '仅 VTT 格式' },
  ];

  const taskOptions = [
    { value: 'transcribe', label: '转录为原语言' },
    { value: 'translate', label: '翻译为英文' },
  ];

  return (
    <div className="mb-6">
      <h3 className="text-lg font-semibold mb-4 text-blue-300 flex items-center gap-2">
        ⚙️ 转录设置
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 语言选择 */}
        <div className="space-y-3">
          <label className="block text-sm font-medium text-white/90 flex items-center gap-2">
            🌍 语言选择
          </label>
          <select
            value={options.language}
            onChange={(e) => handleChange('language', e.target.value)}
            disabled={disabled}
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400/50 disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-sm transition-all duration-300 hover:bg-white/20"
          >
            {languageOptions.map((option) => (
              <option key={option.value} value={option.value} className="bg-slate-800 text-white">
                {option.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-white/60 bg-white/10 p-2 rounded border border-white/20 flex items-center gap-1">
            💡 {options.language === 'auto' ? '将自动检测音频语言' : '指定音频的语言'}
          </p>
        </div>

        {/* 输出格式选择 */}
        <div className="space-y-3">
          <label className="block text-sm font-medium text-white/90 flex items-center gap-2">
            📄 输出格式
          </label>
          <select
            value={options.output_format}
            onChange={(e) => handleChange('output_format', e.target.value)}
            disabled={disabled}
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400/50 disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-sm transition-all duration-300 hover:bg-white/20"
          >
            {outputFormatOptions.map((option) => (
              <option key={option.value} value={option.value} className="bg-slate-800 text-white">
                {option.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-white/60 bg-white/10 p-2 rounded border border-white/20 flex items-center gap-1">
            📋 {options.output_format === 'both' 
              ? '生成两种格式的字幕文件' 
              : `只生成 ${options.output_format.toUpperCase()} 格式`}
          </p>
        </div>

        {/* 任务类型选择 */}
        <div className="space-y-3">
          <label className="block text-sm font-medium text-white/90 flex items-center gap-2">
            🎯 任务类型
          </label>
          <select
            value={options.task}
            onChange={(e) => handleChange('task', e.target.value)}
            disabled={disabled}
            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-green-500/50 focus:border-green-400/50 disabled:opacity-50 disabled:cursor-not-allowed backdrop-blur-sm transition-all duration-300 hover:bg-white/20"
          >
            {taskOptions.map((option) => (
              <option key={option.value} value={option.value} className="bg-slate-800 text-white">
                {option.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-white/60 bg-white/10 p-2 rounded border border-white/20 flex items-center gap-1">
            🔄 {options.task === 'transcribe' 
              ? '保持原语言进行转录' 
              : '转录并翻译为英文'}
          </p>
        </div>
      </div>
    </div>
  );
};

export default TranscriptionOptionsComponent;
