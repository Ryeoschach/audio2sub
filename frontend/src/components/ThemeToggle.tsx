import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    toggleTheme();
  };

  return (
    <button
      onClick={handleClick}
      type="button"
      style={{ zIndex: 9999, pointerEvents: 'auto' }}
      className="
        relative inline-flex items-center justify-center
        w-12 h-12 rounded-xl
        bg-gray-200 dark:bg-gray-700
        hover:bg-gray-300 dark:hover:bg-gray-600
        border border-gray-300 dark:border-gray-600
        transition-all duration-300 ease-in-out
        hover:scale-105 active:scale-95
        focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2
        shadow-lg hover:shadow-xl
        group
        cursor-pointer
      "
      title={`切换到${theme === 'light' ? '深色' : '浅色'}主题`}
      aria-label={`切换到${theme === 'light' ? '深色' : '浅色'}主题`}
    >
      <div className="relative w-6 h-6 overflow-hidden">
        {/* 太阳图标 (浅色主题时显示) */}
        <div className={`
          absolute inset-0 transform transition-all duration-300 ease-in-out
          ${theme === 'light' 
            ? 'translate-y-0 opacity-100 rotate-0' 
            : '-translate-y-full opacity-0 rotate-180'
          }
        `}>
          <svg 
            className="w-6 h-6 text-yellow-500" 
            fill="currentColor" 
            viewBox="0 0 20 20"
          >
            <path 
              fillRule="evenodd" 
              d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" 
              clipRule="evenodd" 
            />
          </svg>
        </div>
        
        {/* 月亮图标 (深色主题时显示) */}
        <div className={`
          absolute inset-0 transform transition-all duration-300 ease-in-out
          ${theme === 'dark' 
            ? 'translate-y-0 opacity-100 rotate-0' 
            : 'translate-y-full opacity-0 -rotate-180'
          }
        `}>
          <svg 
            className="w-6 h-6 text-blue-400" 
            fill="currentColor" 
            viewBox="0 0 20 20"
          >
            <path 
              d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" 
            />
          </svg>
        </div>
      </div>
      
      {/* 悬停提示点 */}
      <div className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full opacity-0 scale-0 transition-all duration-200 group-hover:opacity-100 group-hover:scale-100"></div>
    </button>
  );
};

export default ThemeToggle;
