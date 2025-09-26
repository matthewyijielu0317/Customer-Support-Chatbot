import axios from 'axios';
import type { User, Session, Message, ChatResponse, HealthStatus } from './types';

// Use relative URL in production (nginx proxy) or localhost in development
const API_BASE_URL = import.meta.env.PROD ? '/v1' : 'http://localhost:8000/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const login = async (email: string, passcode: string) => {
  const response = await apiClient.post<{ success: boolean; user: User }>(
    '/auth/login',
    { email, passcode }
  );
  return response.data;
};

export const getSessions = async (userId: string, includeClosed = false) => {
  const response = await apiClient.get<{ sessions: Session[] }>('/sessions', {
    params: { user_id: userId, include_closed: includeClosed },
  });
  return response.data.sessions;
};

export const createSession = async (userId: string) => {
  const response = await apiClient.post<Session>('/sessions', { user_id: userId });
  return response.data;
};

export const getMessages = async (sessionId: string, userId: string) => {
  const response = await apiClient.get<{ messages: Message[] }>(
    `/sessions/${sessionId}/messages`,
    { params: { user_id: userId } }
  );
  return response.data.messages;
};

export const sendMessage = async (
  userId: string,
  query: string,
  sessionId?: string
) => {
  const response = await apiClient.post<ChatResponse>('/chat', {
    user_id: userId,
    query,
    session_id: sessionId,
  });
  return response.data;
};

export const getHealth = async () => {
  const response = await apiClient.get<HealthStatus>('/health');
  return response.data;
};
