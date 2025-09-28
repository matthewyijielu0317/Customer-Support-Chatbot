import type { Session } from '../../services/types';
import { Bot, CheckCircle, Clock, MessageSquare } from 'lucide-react';

interface SessionCardProps {
  session: Session;
  isActive: boolean;
  onSelect: () => void;
}

export function SessionCard({ session, isActive, onSelect }: SessionCardProps) {
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch {
      return 'Recently';
    }
  };

  return (
    <div
      onClick={onSelect}
      className={`group relative p-4 rounded-xl cursor-pointer transition-all duration-200 border ${
        isActive 
          ? 'bg-gradient-to-r from-primary-600 to-primary-700 border-primary-500 shadow-medium' 
          : 'bg-gray-800/50 hover:bg-gray-700/70 border-gray-700/50 hover:border-gray-600/50 hover:shadow-soft'
      }`}
    >
      {/* Active indicator */}
      {isActive && (
        <div className="absolute inset-0 bg-gradient-to-r from-primary-500/20 to-transparent rounded-xl pointer-events-none"></div>
      )}

      <div className="relative space-y-3">
        {/* Header row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`flex items-center justify-center w-8 h-8 rounded-lg transition-colors ${
              isActive 
                ? 'bg-white/20 text-white' 
                : 'bg-gray-700 text-gray-300 group-hover:bg-gray-600 group-hover:text-gray-200'
            }`}>
              <MessageSquare size={16} />
            </div>
            <div className="flex-1 min-w-0">
              <p className={`font-medium truncate text-sm ${
                isActive ? 'text-white' : 'text-gray-200 group-hover:text-white'
              }`}>
                {session.session_id.length > 12 
                  ? `${session.session_id.substring(0, 12)}...` 
                  : session.session_id
                }
              </p>
            </div>
          </div>

          {/* Status indicator */}
          <div className="flex items-center space-x-2">
            {session.status === 'active' ? (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-success-400 rounded-full animate-pulse-soft"></div>
                <span className={`text-xs font-medium ${
                  isActive ? 'text-white/90' : 'text-success-400'
                }`}>
                  Active
                </span>
              </div>
            ) : (
              <div className="flex items-center space-x-1">
                <CheckCircle size={14} className={`${
                  isActive ? 'text-white/70' : 'text-gray-400'
                }`} />
                <span className={`text-xs ${
                  isActive ? 'text-white/70' : 'text-gray-400'
                }`}>
                  Closed
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Summary */}
        {session.summary && (
          <div className="space-y-1">
            <p className={`text-xs leading-relaxed line-clamp-2 ${
              isActive ? 'text-white/80' : 'text-gray-400 group-hover:text-gray-300'
            }`}>
              {session.summary}
            </p>
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center space-x-1">
            <Clock size={12} className={isActive ? 'text-white/60' : 'text-gray-500'} />
            <span className={isActive ? 'text-white/60' : 'text-gray-500'}>
              {session.updated_at ? formatDate(session.updated_at) : 'Recently'}
            </span>
          </div>
          
          {session.message_count !== undefined && (
            <div className="flex items-center space-x-1">
              <Bot size={12} className={isActive ? 'text-white/60' : 'text-gray-500'} />
              <span className={isActive ? 'text-white/60' : 'text-gray-500'}>
                {session.message_count} msg{session.message_count !== 1 ? 's' : ''}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Hover effect overlay */}
      {!isActive && (
        <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"></div>
      )}
    </div>
  );
}
