import { Bot } from 'lucide-react';

interface LoadingProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function Loading({ message = 'Loading...', size = 'md' }: LoadingProps) {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-12 h-12',
    lg: 'w-16 h-16'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  return (
    <div className="flex flex-col items-center justify-center h-full space-y-4 text-center animate-fade-in">
      {/* Loading animation */}
      <div className="relative">
        {/* Spinning border */}
        <div className={`${sizeClasses[size]} border-4 border-gray-700 border-t-primary-500 rounded-full animate-spin`}></div>
        
        {/* Center icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          <Bot size={size === 'sm' ? 14 : size === 'md' ? 20 : 24} className="text-gray-400" />
        </div>
      </div>

      {/* Loading text */}
      <div className="space-y-2">
        <p className={`font-medium text-gray-300 ${textSizeClasses[size]}`}>
          {message}
        </p>
        <div className="flex space-x-1 justify-center">
          <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></div>
          <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
          <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
        </div>
      </div>
    </div>
  );
}

