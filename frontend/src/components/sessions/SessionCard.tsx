import type { Session } from '../../services/types';
import { Bot, CheckCircle } from 'lucide-react';

interface SessionCardProps {
  session: Session;
  isActive: boolean;
  onSelect: () => void;
}

export function SessionCard({ session, isActive, onSelect }: SessionCardProps) {
  const baseClasses =
    'p-3 rounded-lg cursor-pointer transition-colors duration-200';
  const activeClasses = 'bg-indigo-600';
  const inactiveClasses = 'bg-gray-700 hover:bg-gray-600';

  return (
    <div
      onClick={onSelect}
      className={`${baseClasses} ${isActive ? activeClasses : inactiveClasses}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Bot size={18} />
          <span className="font-medium truncate">{session.session_id}</span>
        </div>
        {session.status === 'active' ? (
          <div className="w-2 h-2 bg-green-500 rounded-full" title="Active"></div>
        ) : (
          <span title="Closed">
            <CheckCircle size={16} className="text-gray-400" aria-hidden="true" />
          </span>
        )}
      </div>
      {session.summary && (
        <p className="text-xs text-gray-400 mt-1 truncate">
          {session.summary}
        </p>
      )}
    </div>
  );
}
