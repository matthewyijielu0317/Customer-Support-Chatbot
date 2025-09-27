import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from 'react';
import type { Session } from '../services/types';
import * as api from '../services/api';
import { useAuth } from './useAuth';

interface SessionsContextValue {
  sessions: Session[];
  activeSessionId: string | null;
  setActiveSessionId: Dispatch<SetStateAction<string | null>>;
  isLoading: boolean;
  error: string | null;
  loadSessions: (includeClosed?: boolean) => Promise<void>;
  createNewSession: () => Promise<void>;
}

const SessionsContext = createContext<SessionsContextValue | undefined>(undefined);

export function SessionsProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = useCallback(async (includeClosed = false) => {
    if (!user) {
      setSessions([]);
      setActiveSessionId(null);
      setError(null);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const fetchedSessions = await api.getSessions(user.email, includeClosed);
      setSessions(fetchedSessions);
      setActiveSessionId((currentId) => {
        if (currentId && fetchedSessions.some((s) => s.session_id === currentId)) {
          return currentId;
        }
        return fetchedSessions.length > 0 ? fetchedSessions[0].session_id : null;
      });
    } catch (err) {
      setError('Failed to load sessions.');
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  const createNewSession = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    setError(null);
    try {
      const newSession = await api.createSession(user.email);
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.session_id);
    } catch (err) {
      setError('Failed to create a new session.');
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  const value = useMemo(
    () => ({
      sessions,
      activeSessionId,
      setActiveSessionId,
      isLoading,
      error,
      loadSessions,
      createNewSession,
    }),
    [
      sessions,
      activeSessionId,
      isLoading,
      error,
      loadSessions,
      createNewSession,
    ]
  );

  return <SessionsContext.Provider value={value}>{children}</SessionsContext.Provider>;
}

export function useSessions(): SessionsContextValue {
  const context = useContext(SessionsContext);
  if (!context) {
    throw new Error('useSessions must be used within a SessionsProvider');
  }
  return context;
}
