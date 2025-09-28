import { useState } from 'react';
import { useSessions } from '../../hooks/useSessions';
import { SessionList } from '../sessions/SessionList';
import { NewSessionButton } from '../sessions/NewSessionButton';
import { Loading } from '../common/Loading';
import { ErrorMessage } from '../common/ErrorMessage';
import { History, Filter } from 'lucide-react';

export function Sidebar() {
  const {
    sessions,
    activeSessionId,
    setActiveSessionId,
    isLoading,
    error,
    loadSessions,
    createNewSession,
  } = useSessions();
  const [showClosed, setShowClosed] = useState(false);

  const handleToggleShowClosed = () => {
    const newShowClosed = !showClosed;
    setShowClosed(newShowClosed);
    loadSessions(newShowClosed);
  };

  const activeSessions = sessions.filter(s => s.status === 'active');
  const closedSessions = sessions.filter(s => s.status === 'closed');

  return (
    <aside className="h-full bg-gradient-to-b from-gray-950 to-gray-925 border-r border-gray-800/50 flex flex-col shadow-medium">
      {/* Header Section */}
      <div className="p-5 border-b border-gray-800/50 bg-gray-950/50 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <History size={18} className="text-gray-400" />
            <h2 className="text-base font-semibold tracking-tight text-white">Sessions</h2>
          </div>
          <NewSessionButton
            onClick={createNewSession}
            isLoading={isLoading && sessions.length === 0}
          />
        </div>

        {/* Filter Controls */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">Filters</span>
            <Filter size={14} className="text-gray-500" />
          </div>
          <label className="group flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-800/30 transition-colors cursor-pointer">
            <input
              type="checkbox"
              checked={showClosed}
              onChange={handleToggleShowClosed}
              className="w-4 h-4 rounded bg-gray-700 border-gray-600 text-primary-600 focus:ring-primary-500 focus:ring-offset-0 focus:ring-2"
            />
            <span className="text-sm text-gray-300 group-hover:text-gray-200 transition-colors">
              Show closed sessions
            </span>
          </label>
        </div>

        {/* Session Stats */}
        <div className="mt-4 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-success-500 rounded-full"></div>
            <span className="text-gray-400">{activeSessions.length} active</span>
          </div>
          {showClosed && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
              <span className="text-gray-500">{closedSessions.length} closed</span>
            </div>
          )}
        </div>
      </div>

      {/* Content Section */}
      <div className="flex-1 overflow-hidden flex flex-col">
        {isLoading && sessions.length === 0 && (
          <div className="flex-1 flex items-center justify-center">
            <Loading />
          </div>
        )}
        
        {error && (
          <div className="p-4">
            <ErrorMessage message={error} />
          </div>
        )}
        
        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-track-gray-900 scrollbar-thumb-gray-700 hover:scrollbar-thumb-gray-600">
          <div className="p-3">
            <SessionList
              sessions={sessions}
              activeSessionId={activeSessionId}
              onSelectSession={setActiveSessionId}
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800/50 bg-gray-950/50">
        <div className="text-xs text-gray-500 text-center">
          {sessions.length} {sessions.length === 1 ? 'session' : 'sessions'} total
        </div>
      </div>
    </aside>
  );
}
