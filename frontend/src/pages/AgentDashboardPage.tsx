import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useAgentEscalations } from '../hooks/useAgentEscalations';
import * as api from '../services/api';
import type { EscalationDetail, EscalationSummary } from '../services/types';
import { MessageList } from '../components/chat/MessageList';
import { MessageInput } from '../components/chat/MessageInput';
import { RefreshCw, LogOut, Users, AlertTriangle, Clock, User, MessageSquare, CheckCircle } from 'lucide-react';

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
    <div className="h-screen bg-gradient-to-br from-gray-900 via-gray-925 to-gray-950 text-white flex overflow-hidden">
      <aside className="w-80 bg-gradient-to-b from-gray-950 to-gray-925 border-r border-gray-800/50 flex flex-col shadow-large">
        <div className="p-6 border-b border-gray-800/50 bg-gray-950/50 backdrop-blur-sm">
          <div className="flex items-center space-x-3 mb-4">
            <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-warning-500 to-warning-600 rounded-xl shadow-soft">
              <AlertTriangle size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">Escalation Queue</h1>
              <p className="text-xs text-gray-400">Agent Dashboard</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-3 bg-gray-800/50 rounded-xl border border-gray-700/50 mb-4">
            <div className="flex items-center justify-center w-8 h-8 bg-gradient-to-br from-gray-600 to-gray-700 rounded-full">
              <User size={14} className="text-gray-300" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-200 truncate">{agentId}</p>
              <p className="text-xs text-gray-400">Signed in as Agent</p>
            </div>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => refresh()}
              className="group flex-1 flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium bg-gray-800/50 hover:bg-gray-700/70 text-gray-300 hover:text-white rounded-xl border border-gray-700/50 hover:border-gray-600/50 transition-all duration-200"
            >
              <RefreshCw size={14} className="transition-transform group-hover:rotate-180" />
              <span>Refresh</span>
            </button>
            <button
              onClick={logout}
              className="group flex items-center justify-center space-x-2 px-3 py-2 text-sm font-medium bg-gray-800/50 hover:bg-error-900/50 text-gray-300 hover:text-error-200 rounded-xl border border-gray-700/50 hover:border-error-700/50 transition-all duration-200"
            >
              <LogOut size={14} className="transition-transform group-hover:scale-110" />
              <span className="sr-only">Logout</span>
            </button>
          </div>
          
          {isQueueLoading && (
            <div className="flex items-center space-x-2 mt-3 text-sm text-gray-400">
              <div className="w-4 h-4 border-2 border-gray-600 border-t-primary-500 rounded-full animate-spin"></div>
              <span>Loading queue…</span>
            </div>
          )}
          {queueError && (
            <div className="flex items-center space-x-2 mt-3 p-3 bg-error-950/30 border border-error-800/50 rounded-xl">
              <AlertTriangle size={16} className="text-error-400 flex-shrink-0" />
              <p className="text-sm text-error-200">{queueError}</p>
            </div>
          )}
        </div>
        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-track-gray-900 scrollbar-thumb-gray-700 hover:scrollbar-thumb-gray-600">
          {combinedSessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center p-6">
              <div className="w-16 h-16 bg-gray-700/50 rounded-full flex items-center justify-center mb-4">
                <MessageSquare size={24} className="text-gray-400" />
              </div>
              <h3 className="text-sm font-medium text-gray-300 mb-2">No escalations pending</h3>
              <p className="text-xs text-gray-500">All conversations are handled by AI</p>
            </div>
          ) : (
            <div className="p-3 space-y-2">
              {combinedSessions.map((item) => {
                const isSelected = selectedSessionId === item.session_id;
                const statusConfig = {
                  pending_handoff: { color: 'warning', label: 'Pending', icon: Clock },
                  live_agent: { color: 'success', label: 'Live', icon: CheckCircle },
                  closed: { color: 'gray', label: 'Closed', icon: CheckCircle }
                };
                const config = statusConfig[item.status as keyof typeof statusConfig] || statusConfig.pending_handoff;
                const StatusIcon = config.icon;
                
                return (
                  <div key={item.session_id} className="relative">
                    <button
                      onClick={() => setSelectedSessionId(item.session_id)}
                      className={`group relative w-full text-left p-4 rounded-xl border transition-all duration-200 ${
                        isSelected
                          ? 'bg-gradient-to-r from-primary-600/20 to-primary-700/20 border-primary-500/50 shadow-medium'
                          : 'bg-gray-800/30 hover:bg-gray-700/50 border-gray-700/50 hover:border-gray-600/50 hover:shadow-soft'
                      }`}
                    >
                      {/* Active indicator */}
                      {isSelected && (
                        <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 to-transparent rounded-xl pointer-events-none"></div>
                      )}
                      
                      <div className="relative space-y-3">
                        {/* Header */}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className={`flex items-center justify-center w-8 h-8 rounded-lg transition-colors ${
                              isSelected
                                ? 'bg-white/20 text-white'
                                : 'bg-gray-700 text-gray-300 group-hover:bg-gray-600 group-hover:text-gray-200'
                            }`}>
                              <MessageSquare size={16} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className={`font-medium truncate text-sm ${
                                isSelected ? 'text-white' : 'text-gray-200 group-hover:text-white'
                              }`}>
                                {item.session_id.length > 10
                                  ? `${item.session_id.substring(0, 10)}...`
                                  : item.session_id
                                }
                              </p>
                            </div>
                          </div>
                          
                          {/* Status badge */}
                          <div className={`flex items-center space-x-1 px-2 py-1 rounded-lg text-xs font-medium ${
                            config.color === 'warning' ? 'bg-warning-500/20 text-warning-300' :
                            config.color === 'success' ? 'bg-success-500/20 text-success-300' :
                            'bg-gray-500/20 text-gray-400'
                          }`}>
                            <StatusIcon size={12} />
                            <span>{config.label}</span>
                          </div>
                        </div>
                        
                        {/* Content */}
                        <div className="space-y-2">
                          <p className={`text-xs leading-relaxed line-clamp-2 ${
                            isSelected ? 'text-white/80' : 'text-gray-400 group-hover:text-gray-300'
                          }`}>
                            {item.escalation_reason || 'Escalated conversation'}
                          </p>
                          
                          {item.agent_id && (
                            <div className="flex items-center space-x-1">
                              <Users size={12} className={isSelected ? 'text-white/60' : 'text-gray-500'} />
                              <span className={`text-xs ${
                                isSelected ? 'text-white/60' : 'text-gray-500'
                              }`}>
                                Assigned to {item.agent_id}
                              </span>
                            </div>
                          )}
                        </div>
                        
                        {/* Claim button */}
                        {item.status === 'pending_handoff' && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              void handleClaim(item.session_id);
                            }}
                            className="group/claim w-full flex items-center justify-center space-x-2 mt-3 px-3 py-2 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-500 hover:to-primary-600 text-white text-xs font-medium rounded-lg shadow-soft hover:shadow-medium transition-all duration-200"
                          >
                            <Users size={14} />
                            <span>Claim Conversation</span>
                          </button>
                        )}
                      </div>
                      
                      {/* Hover effect */}
                      {!isSelected && (
                        <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none"></div>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </aside>
      <main className="flex-1 flex flex-col bg-gradient-to-br from-gray-800 to-gray-850 relative">
        {/* Background decoration */}
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-primary-950/5 to-primary-900/10 pointer-events-none"></div>
        
        <header className="relative p-6 border-b border-gray-700/50 bg-gray-900/50 backdrop-blur-sm">
          {selectedSessionId ? (
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl shadow-soft">
                  <MessageSquare size={20} className="text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-white">Session {selectedSessionId}</h2>
                  <p className="text-sm text-gray-400">Live conversation</p>
                </div>
              </div>
              
              {detail?.escalation && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                    <div className="flex items-center space-x-2 mb-2">
                      <User size={16} className="text-gray-400" />
                      <span className="text-sm font-medium text-gray-300">User</span>
                    </div>
                    <p className="text-sm text-white font-mono">{detail.escalation.user_id}</p>
                  </div>
                  
                  <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                    <div className="flex items-center space-x-2 mb-2">
                      <AlertTriangle size={16} className="text-gray-400" />
                      <span className="text-sm font-medium text-gray-300">Status</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        detail.escalation.status === 'live_agent' ? 'bg-success-500' :
                        detail.escalation.status === 'pending_handoff' ? 'bg-warning-500' :
                        'bg-gray-500'
                      }`}></div>
                      <span className="text-sm text-white capitalize">{detail.escalation.status.replace('_', ' ')}</span>
                    </div>
                  </div>
                  
                  <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                    <div className="flex items-center space-x-2 mb-2">
                      <Clock size={16} className="text-gray-400" />
                      <span className="text-sm font-medium text-gray-300">Agent</span>
                    </div>
                    <p className="text-sm text-white">
                      {detail.escalation.agent_id || 'Unassigned'}
                    </p>
                  </div>
                </div>
              )}
              
              {detail?.escalation.escalation_reason && (
                <div className="bg-warning-950/30 border border-warning-800/50 rounded-xl p-4">
                  <div className="flex items-start space-x-3">
                    <AlertTriangle size={18} className="text-warning-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-medium text-warning-100 mb-1">Escalation Reason</h4>
                      <p className="text-sm text-warning-200/80 leading-relaxed">
                        {detail.escalation.escalation_reason}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-gray-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
                <MessageSquare size={24} className="text-gray-400" />
              </div>
              <h2 className="text-xl font-semibold text-gray-300 mb-2">Select an escalation</h2>
              <p className="text-gray-500">Choose a conversation from the queue to start assisting</p>
            </div>
          )}
        </header>
        <div className="relative flex-1 flex flex-col overflow-hidden">
          {detailLoading && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-4">
                <div className="w-12 h-12 border-4 border-gray-700 border-t-primary-500 rounded-full animate-spin mx-auto"></div>
                <p className="text-gray-400">Loading conversation…</p>
              </div>
            </div>
          )}
          
          {detailError && (
            <div className="flex-1 flex items-center justify-center p-6">
              <div className="text-center space-y-4 max-w-md">
                <div className="w-16 h-16 bg-error-500/20 rounded-full flex items-center justify-center mx-auto">
                  <AlertTriangle size={24} className="text-error-400" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-error-100 mb-2">Failed to load conversation</h3>
                  <p className="text-error-200/80">{detailError}</p>
                </div>
                <button
                  onClick={() => selectedSessionId && loadDetail(selectedSessionId)}
                  className="inline-flex items-center space-x-2 px-4 py-2 bg-error-600 hover:bg-error-500 text-white rounded-xl transition-colors"
                >
                  <RefreshCw size={16} />
                  <span>Try again</span>
                </button>
              </div>
            </div>
          )}
          
          {!detailLoading && !detailError && detail && (
            <>
              <MessageList messages={detail.messages} />
              
              {!canRespond && (
                <div className="flex items-center space-x-3 px-6 py-4 bg-gradient-to-r from-warning-900/80 to-warning-800/80 border-t border-warning-700/50">
                  <div className="flex items-center justify-center w-6 h-6 bg-warning-600 rounded-full">
                    <Users size={14} className="text-warning-100" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-warning-100">
                      Claim Required
                    </p>
                    <p className="text-xs text-warning-200/80">
                      You need to claim this conversation to start responding.
                    </p>
                  </div>
                  <button
                    onClick={() => selectedSessionId && handleClaim(selectedSessionId)}
                    className="px-4 py-2 bg-warning-600 hover:bg-warning-500 text-warning-100 rounded-xl text-sm font-medium transition-colors"
                  >
                    Claim Now
                  </button>
                </div>
              )}
              
              <MessageInput
                onSendMessage={handleSendMessage}
                disabled={!canRespond}
              />
            </>
          )}
          
          {!detailLoading && !detailError && !detail && (
            <div className="flex-1 flex items-center justify-center text-center p-6">
              <div className="space-y-4 max-w-md">
                <div className="w-16 h-16 bg-gray-700/50 rounded-full flex items-center justify-center mx-auto">
                  <MessageSquare size={24} className="text-gray-400" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-300 mb-2">No conversation selected</h3>
                  <p className="text-gray-500 leading-relaxed">
                    Select an escalation from the queue to view the conversation and start assisting the customer.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
