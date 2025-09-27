import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useAgentEscalations } from '../hooks/useAgentEscalations';
import * as api from '../services/api';
import type { EscalationDetail, EscalationSummary } from '../services/types';
import { MessageList } from '../components/chat/MessageList';
import { MessageInput } from '../components/chat/MessageInput';

function combineSessions(
  pending: EscalationSummary[],
  claimed: EscalationSummary[]
): EscalationSummary[] {
  const map = new Map<string, EscalationSummary>();
  for (const item of claimed) {
    map.set(item.session_id, item);
  }
  for (const item of pending) {
    if (!map.has(item.session_id)) {
      map.set(item.session_id, item);
    }
  }
  return Array.from(map.values());
}

export function AgentDashboardPage() {
  const { user, logout } = useAuth();
  const agentId = user?.email ?? null;
  const {
    escalations,
    isLoading: isQueueLoading,
    error: queueError,
    refresh,
    claim,
  } = useAgentEscalations(agentId);
  const [claimedSessions, setClaimedSessions] = useState<EscalationSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [detail, setDetail] = useState<EscalationDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const combinedSessions = useMemo(
    () => combineSessions(escalations, claimedSessions),
    [escalations, claimedSessions]
  );

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get('session_id');
    if (sessionId) {
      setSelectedSessionId(sessionId);
    }
  }, []);

  useEffect(() => {
    if (!selectedSessionId && combinedSessions.length > 0) {
      setSelectedSessionId(combinedSessions[0].session_id);
    }
  }, [combinedSessions, selectedSessionId]);

  const loadDetail = useCallback(
    async (sessionId: string) => {
      setDetailLoading(true);
      setDetailError(null);
      try {
        const response = await api.getEscalationDetail(sessionId);
        setDetail(response);
        if (
          response.escalation.agent_id === agentId &&
          response.escalation.status === 'live_agent'
        ) {
          setClaimedSessions((prev) => {
            const filtered = prev.filter((item) => item.session_id !== sessionId);
            return [...filtered, response.escalation];
          });
        }
      } catch (err) {
        setDetailError('Failed to load conversation.');
      } finally {
        setDetailLoading(false);
      }
    },
    [agentId]
  );

  useEffect(() => {
    if (selectedSessionId) {
      void loadDetail(selectedSessionId);
    } else {
      setDetail(null);
    }
  }, [selectedSessionId, loadDetail]);

  const handleClaim = async (sessionId: string) => {
    const result = await claim(sessionId);
    if (result) {
      setClaimedSessions((prev) => {
        const filtered = prev.filter((item) => item.session_id !== sessionId);
        return [...filtered, result];
      });
      setSelectedSessionId(sessionId);
      await loadDetail(sessionId);
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!selectedSessionId || !agentId) return;
    try {
      const response = await api.sendAgentMessage(selectedSessionId, agentId, message);
      const updatedMeta: EscalationSummary = {
        ...(detail?.escalation ?? {
          session_id: selectedSessionId,
          user_id: '',
          status: response.status,
        }),
        status: response.status,
        agent_id: agentId,
        last_response: message,
      };

      const updatedDetail: EscalationDetail = {
        escalation: updatedMeta,
        messages: response.messages,
      };
      setDetail(updatedDetail);
      setClaimedSessions((prev) => {
        const filtered = prev.filter((item) => item.session_id !== selectedSessionId);
        return [...filtered, updatedMeta];
      });
    } catch (err) {
      setDetailError('Failed to send message.');
    }
  };

  const canRespond =
    detail?.escalation.status === 'live_agent' && detail?.escalation.agent_id === agentId;

  return (
    <div className="h-screen bg-gray-900 text-white flex">
      <aside className="w-80 bg-gray-950 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-lg font-semibold">Escalation Queue</h1>
          <p className="text-sm text-gray-400">Signed in as {agentId}</p>
          <div className="mt-3 flex space-x-2">
            <button
              onClick={() => refresh()}
              className="px-3 py-1 text-sm bg-gray-800 rounded hover:bg-gray-700"
            >
              Refresh
            </button>
            <button
              onClick={logout}
              className="px-3 py-1 text-sm bg-gray-800 rounded hover:bg-gray-700"
            >
              Logout
            </button>
          </div>
          {isQueueLoading && (
            <p className="text-sm text-gray-400 mt-2">Loading queue…</p>
          )}
          {queueError && (
            <p className="text-sm text-red-400 mt-2">{queueError}</p>
          )}
        </div>
        <div className="flex-1 overflow-y-auto">
          {combinedSessions.length === 0 ? (
            <p className="text-sm text-gray-400 p-4">No escalations pending.</p>
          ) : (
            <ul>
              {combinedSessions.map((item) => (
                <li key={item.session_id}>
                  <button
                    onClick={() => setSelectedSessionId(item.session_id)}
                    className={`w-full text-left px-4 py-3 border-b border-gray-800 hover:bg-gray-800 ${
                      selectedSessionId === item.session_id ? 'bg-gray-800' : ''
                    }`}
                  >
                    <p className="text-sm font-semibold">{item.session_id}</p>
                    <p className="text-xs text-gray-400 truncate">
                      {item.escalation_reason || 'Escalated conversation'}
                    </p>
                    <p className="text-xs text-indigo-300 mt-1">
                      {item.status}{item.agent_id ? ` · ${item.agent_id}` : ''}
                    </p>
                    {item.status === 'pending_handoff' && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          void handleClaim(item.session_id);
                        }}
                        className="mt-2 inline-flex items-center px-2 py-1 text-xs bg-indigo-600 rounded hover:bg-indigo-500"
                      >
                        Claim
                      </button>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
      <main className="flex-1 flex flex-col">
        <header className="p-4 border-b border-gray-800">
          {selectedSessionId ? (
            <div>
              <h2 className="text-xl font-semibold">Session {selectedSessionId}</h2>
              {detail?.escalation && (
                <p className="text-sm text-gray-400">
                  User: {detail.escalation.user_id} · Status: {detail.escalation.status}
                </p>
              )}
              {detail?.escalation.escalation_reason && (
                <p className="text-sm text-gray-400 mt-1">
                  Reason: {detail.escalation.escalation_reason}
                </p>
              )}
            </div>
          ) : (
            <h2 className="text-xl font-semibold">Select an escalation</h2>
          )}
        </header>
        <div className="flex-1 flex flex-col bg-gray-800">
          {detailLoading && (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-gray-400">Loading conversation…</p>
            </div>
          )}
          {detailError && (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-red-400">{detailError}</p>
            </div>
          )}
          {!detailLoading && !detailError && detail && (
            <>
              <MessageList messages={detail.messages} />
              {!canRespond && (
                <div className="px-4 py-2 bg-yellow-900 text-yellow-100 text-sm border-t border-yellow-700">
                  Claim the conversation to start responding.
                </div>
              )}
              <MessageInput
                onSendMessage={handleSendMessage}
                disabled={!canRespond}
              />
            </>
          )}
          {!detailLoading && !detailError && !detail && (
            <div className="flex-1 flex items-center justify-center text-gray-400">
              Select an escalation to view the conversation.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
