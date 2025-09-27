import { useState, useEffect, useCallback } from 'react';
import type { Message } from '../services/types';
import * as api from '../services/api';
import { useAuth } from './useAuth';

export function useMessages(sessionId: string | null) {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEscalated, setIsEscalated] = useState(false);

  const loadMessages = useCallback(async () => {
    if (!user || !sessionId) {
      setMessages([]);
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const fetchedMessages = await api.getMessages(sessionId, user.email);
      setMessages(fetchedMessages);
      if (fetchedMessages.some((msg) => msg.role === 'agent')) {
        setIsEscalated(true);
      }
    } catch (err) {
      setError('Failed to load messages.');
    } finally {
      setIsLoading(false);
    }
  }, [user, sessionId]);

  useEffect(() => {
    loadMessages();
  }, [loadMessages]);

  useEffect(() => {
    setIsEscalated(false);
  }, [sessionId]);

  const postMessage = async (query: string) => {
    if (!user) return;
    
    const userMessage: Message = {
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
      session_id: sessionId || '',
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await api.sendMessage(user.email, query, sessionId || undefined);
      if (response.answer) {
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.answer,
          created_at: new Date().toISOString(),
          session_id: response.session_id,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
      if (response.session_status && response.session_status !== 'active') {
        setIsEscalated(true);
      }
      if (response.should_escalate) {
        setIsEscalated(true);
      }
    } catch (err) {
      setError('Failed to send message.');
      setMessages((prev) => prev.slice(0, -1)); // Remove user message on error
    }
  };

  return { messages, isLoading, error, postMessage, isEscalated };
}
