import { useState } from 'react';
import { useSessions } from '../../hooks/useSessions';
import { SessionList } from '../sessions/SessionList';
import { NewSessionButton } from '../sessions/NewSessionButton';
import { Loading } from '../common/Loading';
import { ErrorMessage } from '../common/ErrorMessage';

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

  return (
    <aside className="w-80 bg-gray-900 p-4 border-r border-gray-700 flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Sessions</h2>
        <NewSessionButton
          onClick={createNewSession}
          isLoading={isLoading && sessions.length === 0}
        />
      </div>

      <div className="mb-4">
        <label className="flex items-center space-x-2 text-sm text-gray-400">
          <input
            type="checkbox"
            checked={showClosed}
            onChange={handleToggleShowClosed}
            className="rounded bg-gray-700 border-gray-600 focus:ring-indigo-500"
          />
          <span>Show closed sessions</span>
        </label>
      </div>

      {isLoading && sessions.length === 0 && <Loading />}
      {error && <ErrorMessage message={error} />}
      
      <div className="overflow-y-auto flex-1">
        <SessionList
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
        />
      </div>
    </aside>
  );
}
