export interface SearchSessionPublic {
  id: string;
  title: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export interface SearchSessionsPublic {
  data: SearchSessionPublic[];
  count: number;
}

export interface SearchSessionCreate {
  title?: string;
}

export interface SearchHistoryPublic {
  id: string;
  session_id: string;
  owner_id: number;
  query: string;
  result: string | null;
  created_at: string;
}

export interface SearchSessionWithHistoryPublic extends SearchSessionPublic {
  history: SearchHistoryPublic[];
}

export interface AgentChatRequest {
  message: string;
}

export interface AgentChatResponse {
  session_id: string;
  reply: string;
}

export interface DeleteSearchResponse {
  message: string;
}
