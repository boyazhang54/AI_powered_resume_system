import axios from 'axios';
import type { AuthResponse, HistoryItem, MatchResult, ResumeParseResult, User } from './types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 60000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('resume_ai_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function register(username: string, password: string): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/api/auth/register', { username, password });
  return response.data;
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/api/auth/login', { username, password });
  return response.data;
}

export async function getMe(): Promise<User> {
  const response = await api.get<User>('/api/auth/me');
  return response.data;
}

export async function getHistory(): Promise<HistoryItem[]> {
  const response = await api.get<HistoryItem[]>('/api/history');
  return response.data;
}

export async function parseResume(file: File): Promise<ResumeParseResult> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post<ResumeParseResult>('/api/resumes/parse', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function matchResume(resumeId: string, content: string): Promise<MatchResult> {
  const response = await api.post<MatchResult>(`/api/resumes/${resumeId}/match`, {
    job_source: {
      source_type: 'text',
      content,
    },
  });
  return response.data;
}
