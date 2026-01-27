import type {
  ResumeListResponse,
  Resume,
  UploadResponse,
  HealthResponse,
  PhoneLinksResponse,
  PhoneLink,
  PhoneLinkRequest,
  CallListResponse,
  CallDetail,
  OutboundCallRequest,
  OutboundCallResponse,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail || response.statusText);
  }
  return response.json();
}

// Health
export const getHealth = () => request<HealthResponse>('/health');

// Resumes
export const listResumes = () => request<ResumeListResponse>('/resumes');

export const getResume = (id: string) => request<Resume>(`/resumes/${id}`);

export const deleteResume = (id: string) =>
  request<{ message: string }>(`/resumes/${id}`, { method: 'DELETE' });

export const uploadResume = async (file: File, candidateName?: string): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (candidateName) {
    formData.append('candidate_name', candidateName);
  }
  return request<UploadResponse>('/resumes', { method: 'POST', body: formData });
};

export const getResumeContext = (id: string) =>
  request<{ system_prompt: string }>(`/resumes/${id}/context`);

export const getResumePhones = (id: string) =>
  request<{ phones: string[] }>(`/resumes/${id}/phones`);

// Phone Links
export const listPhoneLinks = () => request<PhoneLinksResponse>('/phone-links');

export const createPhoneLink = (data: PhoneLinkRequest) =>
  request<PhoneLink>('/phone-links', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

export const deletePhoneLink = (phone: string) =>
  request<{ message: string }>(`/phone-links/${encodeURIComponent(phone)}`, { method: 'DELETE' });

// Calls
export const listCalls = () => request<CallListResponse>('/calls');

export const getCall = (id: string) => request<CallDetail>(`/calls/${id}`);

export const makeOutboundCall = (data: OutboundCallRequest) =>
  request<OutboundCallResponse>('/calls/outbound', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

export const getListenToken = (roomName: string) =>
  request<{ token: string; url: string; room_name: string }>(`/calls/listen/${encodeURIComponent(roomName)}`);
