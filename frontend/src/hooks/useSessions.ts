import { useState, useEffect, useCallback } from 'react';
import type { Session } from '../services/types';
import * as api from '../services/api';
import { useAuth } from './useAuth';

export function useSessions() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = useCallback(async (includeClosed = false) => {
    if (!user) return;
    setIsLoading(true);
    setError(null);
    try {
      const fetchedSessions = await api.getSessions(user.email, includeClosed);
      setSessions(fetchedSessions);
      if (!activeSessionId && fetchedSessions.length > 0) {
        setActiveSessionId(fetchedSessions[0].session_id);
      }
    } catch (err) {
      setError('Failed to load sessions.');
    } finally {
      setIsLoading(false);
    }
  }, [user, activeSessionId]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const createNewSession = async () => {
    if (!user) return;
    setIsLoading(true);
    setError(null);
    try {
      const newSession = await api.createSession(user.email);
      setSessions([newSession, ...sessions]);
      setActiveSessionId(newSession.session_id);
    } catch (err) {
      setError('Failed to create a new session.');
    } finally {
      setIsLoading(false);
    }
  };

  return {
    sessions,
    activeSessionId,
    setActiveSessionId,
    isLoading,
    error,
    loadSessions,
    createNewSession,
  };
}
