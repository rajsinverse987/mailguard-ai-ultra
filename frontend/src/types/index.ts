/** Shared frontend types. */

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  whatsapp_number?: string;
  role: string;
  preferred_language: string;
  preferred_voice: string;
  voice_gender: string;
  morning_briefing_time: string;
  enable_voice_alerts: boolean;
  enable_text_alerts: boolean;
}

export interface EmailSummary {
  id: string;
  subject: string;
  sender_email: string;
  sender_name?: string | null;
  sender_company?: string | null;
  snippet?: string | null;
  category: string;
  priority: string;
  sentiment: string;
  intent?: string | null;
  confidence: number;
  summary?: string | null;
  summary_hi?: string | null;
  action_items: string[];
  due_dates: string[];
  is_phishing: boolean;
  is_spam: boolean;
  threat_score: number;
  threat_reason?: string | null;
  received_at: string;
  notified: boolean;
}

export interface EmailAccount {
  id: string;
  provider: string;
  email_address: string;
  display_name?: string | null;
  is_active: boolean;
  last_sync_at?: string | null;
  created_at: string;
}

export interface NotificationLog {
  id: string;
  channel: string;
  status: string;
  provider: string;
  to_number: string;
  delivered: boolean;
  error?: string | null;
  created_at: string;
  email_id?: string | null;
}

export interface VoiceNote {
  id: string;
  text: string;
  text_hi?: string | null;
  language: string;
  voice: string;
  gender: string;
  engine: string;
  audio_url?: string | null;
  duration_ms?: number | null;
  mime: string;
  created_at: string;
}

export interface FraudAlert {
  id: string;
  email_id: string;
  threat_score: number;
  severity: string;
  is_phishing: boolean;
  is_scam: boolean;
  reasons: string[];
  suspicious_links: string[];
  reasoning?: string | null;
  created_at: string;
  acknowledged: boolean;
}

export interface AnalyticsOverview {
  total_emails: number;
  total_important: number;
  total_fraud: number;
  total_interviews: number;
  total_banking: number;
  total_unread: number;
  voice_notes_sent: number;
  whatsapp_sent: number;
}

export interface AnalyticsResponse {
  overview: AnalyticsOverview;
  by_category: { key: string; count: number }[];
  by_priority: { key: string; count: number }[];
  by_sender: { key: string; count: number }[];
  timeline: { date: string; count: number }[];
  scam_trend: { date: string; count: number }[];
}
