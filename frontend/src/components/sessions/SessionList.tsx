import type { Session } from '../../services/types';
import { SessionCard } from './SessionCard';

interface SessionListProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
}

export function SessionList({
  sessions,
  activeSessionId,
  onSelectSession,
}: SessionListProps) {
  if (sessions.length === 0) {
    return <p className="text-gray-400">No sessions found.</p>;
  }

  return (
    <div className="space-y-2">
      {sessions.map((session) => (
        <SessionCard
          key={session.session_id}
          session={session}
          isActive={session.session_id === activeSessionId}
          onSelect={() => onSelectSession(session.session_id)}
        />
      ))}
    </div>
  );
}
