export interface Resume {
  id: string;
  candidate_name: string;
  file_path: string;
  created_at: string;
  content_preview: string;
  voice?: string;
}

export interface ResumeListResponse {
  resumes: Resume[];
  total: number;
}

export interface UploadResponse {
  id: string;
  candidate_name: string;
  message: string;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface PhoneLink {
  phone: string;
  resume_id: string;
  candidate_name: string;
}

export interface PhoneLinksResponse {
  links: PhoneLink[];
  total: number;
}

export interface PhoneLinkRequest {
  phone: string;
  resume_id: string;
}

// Call History
export interface CallTranscriptEntry {
  role: 'user' | 'agent';
  text: string;
  timestamp: number;
}

export interface CallSummary {
  id: string;
  room_name: string;
  resume_id: string | null;
  candidate_name: string;
  caller_phone: string | null;
  direction: 'inbound' | 'outbound';
  started_at: string;
  ended_at: string | null;
  turn_count: number;
  summary?: string | null;
}

export interface CallDetail extends CallSummary {
  transcript: CallTranscriptEntry[];
}

export interface CallListResponse {
  calls: CallSummary[];
  total: number;
}

// Outbound
export interface OutboundCallRequest {
  phone: string;
  resume_id: string;
  caller_id?: string;
  job_detail?: string;
}

export interface OutboundCallResponse {
  call_id: string;
  phone: string;
  resume_id: string;
  status: string;
}
