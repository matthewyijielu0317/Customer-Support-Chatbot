export interface User {
  email: string;
  first_name?: string;
  last_name?: string;
  role?: 'customer' | 'agent';
}

export interface Session {
  session_id: string;
  user_id: string;
  status: string;
  created_at: string;
  updated_at?: string;
  summary?: string;
}

export interface Message {
  id?: string;
  session_id: string;
  role: 'user' | 'assistant' | 'agent';
  content: string;
  created_at: string;
  agent_id?: string;
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
  session_status: string;
}

export interface EscalationSummary {
  session_id: string;
  user_id: string;
  status: string;
  created_at?: string | null;
  last_updated?: string | null;
  escalated_at?: string | null;
  escalation_reason?: string | null;
  agent_id?: string | null;
  last_query?: string | null;
  last_response?: string | null;
}

export interface EscalationDetail {
  escalation: EscalationSummary;
  messages: Message[];
}

export interface HealthStatus {
  status: 'ok' | 'degraded';
  redis: 'ok' | string;
  mongo: 'ok' | string;
}
