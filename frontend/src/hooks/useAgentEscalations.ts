import { useCallback, useEffect, useState } from 'react';
import * as api from '../services/api';
import type { EscalationSummary } from '../services/types';

interface UseAgentEscalationsResult {
  escalations: EscalationSummary[];
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  claim: (sessionId: string) => Promise<EscalationSummary | null>;
}

export function useAgentEscalations(agentId: string | null): UseAgentEscalationsResult {
  const [escalations, setEscalations] = useState<EscalationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!agentId) {
      setEscalations([]);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const results = await api.getEscalations(agentId);
      setEscalations(results);
    } catch (err) {
      setError('Failed to load escalations.');
    } finally {
      setIsLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const claim = useCallback(
    async (sessionId: string) => {
      if (!agentId) return null;
      try {
        const result = await api.claimEscalation(sessionId, agentId);
        setEscalations((prev) => prev.filter((item) => item.session_id !== sessionId));
        return result;
      } catch (err) {
        setError('Failed to claim escalation.');
        return null;
      }
    },
    [agentId]
  );

  return { escalations, isLoading, error, refresh, claim };
}
