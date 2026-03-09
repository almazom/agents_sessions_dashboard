/** API client for Agent Nexus backend */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Session {
  session_id: string;
  agent_type: string;
  agent_name: string;
  cwd: string;
  timestamp_start: string;
  timestamp_end?: string;
  status: 'active' | 'completed' | 'error' | 'paused' | 'unknown';
  user_intent: string;
  tool_calls: string[];
  token_usage: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  files_modified: string[];
  source_file: string;
  error_message?: string;
}

export interface Metrics {
  total_sessions: number;
  by_agent: Record<string, number>;
  by_status: Record<string, number>;
  total_tokens: number;
  last_updated: string;
}

export interface SessionsResponse {
  total: number;
  limit: number;
  offset: number;
  sessions: Session[];
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async fetch<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      credentials: 'include', // cookies for auth
    });

    if (!res.ok) {
      throw new Error(`API Error: ${res.status}`);
    }

    return res.json();
  }

  // Sessions
  async getSessions(params?: {
    status?: string;
    agent?: string;
    limit?: number;
    offset?: number;
  }): Promise<SessionsResponse> {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.agent) searchParams.set('agent', params.agent);
    if (params?.limit) searchParams.set('limit', String(params.limit));
    if (params?.offset) searchParams.set('offset', String(params.offset));

    const query = searchParams.toString();
    return this.fetch<SessionsResponse>(`/api/sessions${query ? `?${query}` : ''}`);
  }

  async getSession(sessionId: string): Promise<Session> {
    return this.fetch<Session>(`/api/sessions/${sessionId}`);
  }

  async getMetrics(): Promise<{ success: boolean; data: Metrics }> {
    return this.fetch(`/api/metrics`);
  }

  async rescanSessions(): Promise<{ success: boolean; sessions_found: number }> {
    return this.fetch('/api/sessions/scan', { method: 'POST' });
  }

  // Auth
  async login(password: string): Promise<{ success: boolean; message: string }> {
    return this.fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });
  }

  async logout(): Promise<{ success: boolean }> {
    return this.fetch('/api/auth/logout', { method: 'POST' });
  }

  async getAuthStatus(): Promise<{ authenticated: boolean; password_required: boolean }> {
    return this.fetch('/api/auth/status');
  }

  // WebSocket
  getWebSocketUrl(): string {
    const wsProtocol = this.baseUrl.startsWith('https') ? 'wss' : 'ws';
    return `${this.baseUrl.replace(/^https?/, wsProtocol)}/ws`;
  }
}

export const api = new ApiClient(API_BASE);
