import { AlertTriangle, RefreshCw, XCircle } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  variant?: 'error' | 'warning' | 'info';
  size?: 'sm' | 'md' | 'lg';
}

export function ErrorMessage({ 
  message, 
  onRetry, 
  variant = 'error',
  size = 'md' 
}: ErrorMessageProps) {
  const variants = {
    error: {
      icon: XCircle,
      colors: 'text-error-400 bg-error-950/20 border-error-800/30',
      iconBg: 'bg-error-500/20',
      textColor: 'text-error-100'
    },
    warning: {
      icon: AlertTriangle,
      colors: 'text-warning-400 bg-warning-950/20 border-warning-800/30',
      iconBg: 'bg-warning-500/20',
      textColor: 'text-warning-100'
    },
    info: {
      icon: AlertTriangle,
      colors: 'text-primary-400 bg-primary-950/20 border-primary-800/30',
      iconBg: 'bg-primary-500/20',
      textColor: 'text-primary-100'
    }
  };

  const sizeClasses = {
    sm: {
      container: 'p-4 space-y-3',
      icon: 'w-8 h-8',
      iconSize: 20,
      text: 'text-sm',
      button: 'px-3 py-1.5 text-sm'
    },
    md: {
      container: 'p-6 space-y-4',
      icon: 'w-12 h-12',
      iconSize: 24,
      text: 'text-base',
      button: 'px-4 py-2 text-sm'
    },
    lg: {
      container: 'p-8 space-y-6',
      icon: 'w-16 h-16',
      iconSize: 32,
      text: 'text-lg',
      button: 'px-6 py-3 text-base'
    }
  };

  const config = variants[variant];
  const Icon = config.icon;
  const sizes = sizeClasses[size];

  return (
    <div className="flex flex-col justify-center items-center h-full animate-fade-in">
      <div className={`max-w-md mx-auto text-center rounded-2xl border ${config.colors} ${sizes.container}`}>
        {/* Error icon */}
        <div className={`mx-auto flex items-center justify-center ${sizes.icon} rounded-full ${config.iconBg}`}>
          <Icon size={sizes.iconSize} className={config.colors.split(' ')[0]} />
        </div>

        {/* Error message */}
        <div className="space-y-2">
          <h3 className={`font-semibold ${config.textColor} ${sizes.text}`}>
            {variant === 'error' ? 'Something went wrong' : 
             variant === 'warning' ? 'Warning' : 'Information'}
          </h3>
          <p className={`text-gray-300 ${sizes.text === 'text-lg' ? 'text-base' : 'text-sm'} leading-relaxed`}>
            {message}
          </p>
        </div>

        {/* Retry button */}
        {onRetry && (
          <button
            onClick={onRetry}
            className={`group inline-flex items-center space-x-2 ${sizes.button} font-medium ${config.textColor} ${config.iconBg} hover:bg-opacity-30 rounded-xl border border-transparent hover:border-gray-700/50 transition-all duration-200`}
          >
            <RefreshCw size={16} className="transition-transform group-hover:rotate-45" />
            <span>Try again</span>
          </button>
        )}
      </div>
    </div>
  );
}

