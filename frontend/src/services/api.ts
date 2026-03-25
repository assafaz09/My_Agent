import axios from 'axios';

// If NEXT_PUBLIC_API_URL is not set, we rely on Next.js rewrites and call API routes relatively.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

const api = axios.create({
  baseURL: API_BASE_URL ?? '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chat API
export interface ChatRequest {
  message: string;
  session_id?: string;
  language?: 'en' | 'he';
}

export interface ChatResponse {
  response: string;
  session_id: string;
  language: string;
  sources: string[];
  timestamp: string;
}

export const chatApi = {
  sendMessage: async (data: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post('/api/chat/', data);
    return response.data;
  },

  getSessions: async () => {
    const response = await api.get('/api/chat/sessions');
    return response.data;
  },

  resetSession: async (sessionId: string) => {
    const response = await api.post(`/api/chat/sessions/${sessionId}/reset`);
    return response.data;
  },
};

// Upload API
export interface UploadStatus {
  upload_id: string;
  filename: string;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  error_message?: string;
  created_at: string;
}

export const uploadApi = {
  uploadFile: async (file: File): Promise<{ upload_id: string; filename: string; status: string; message: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getUploadStatus: async (uploadId: string): Promise<UploadStatus> => {
    const response = await api.get(`/api/upload/status/${uploadId}`);
    return response.data;
  },

  getUploads: async () => {
    const response = await api.get('/api/upload/uploads');
    return response.data;
  },

  deleteUpload: async (uploadId: string) => {
    const response = await api.delete(`/api/upload/${uploadId}`);
    return response.data;
  },
};

// Knowledge API
export interface KnowledgeDocument {
  document_id: string;
  filename: string;
  file_type: string;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
  processed: boolean;
}

export interface PersonalProfile {
  profile_id: string;
  name?: string;
  relationships: Array<Record<string, string>>;
  important_events: Array<Record<string, string>>;
  preferences: Array<Record<string, string>>;
  communication_style: Record<string, string>;
  emotional_patterns: Array<Record<string, string>>;
  goals_aspirations: Array<Record<string, string>>;
  cultural_background: Record<string, string>;
  languages: string[];
  last_updated: string;
}

export const knowledgeApi = {
  getDocuments: async (): Promise<KnowledgeDocument[]> => {
    const response = await api.get('/api/knowledge/');
    return response.data;
  },

  searchKnowledge: async (query: string, limit = 5, threshold = 0.7) => {
    const response = await api.get('/api/knowledge/search', {
      params: { query, limit, threshold },
    });
    return response.data;
  },

  getProfile: async (): Promise<PersonalProfile> => {
    const response = await api.get('/api/knowledge/profile');
    return response.data;
  },

  deleteDocument: async (documentId: string) => {
    const response = await api.delete(`/api/knowledge/${documentId}`);
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/api/knowledge/stats');
    return response.data;
  },
};

// Health check
export const healthApi = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};
