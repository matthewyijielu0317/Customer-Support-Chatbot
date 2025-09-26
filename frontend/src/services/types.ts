export interface User {
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface Session {
  session_id: string;
  user_id: string;
  status: 'active' | 'closed';
  created_at: string;
  updated_at?: string;
  summary?: string;
}

export interface Message {
  id?: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Citation {
  source: string;
  title?: string;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  citations: Citation[];
  should_escalate: boolean;
  cache_hit: boolean;
}

export interface HealthStatus {
  status: 'ok' | 'degraded';
  redis: 'ok' | string;
  mongo: 'ok' | string;
}

