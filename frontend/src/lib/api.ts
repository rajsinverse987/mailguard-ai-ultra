/**
 * API client - typed fetch wrapper around the MailGuard backend.
 */

import axios, { AxiosInstance } from "axios";

const baseURL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 10_000,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem("mailguard_token");
    if (token) {
      config.headers = config.headers || {};
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error?.response?.status === 401 && typeof window !== "undefined") {
      window.localStorage.removeItem("mailguard_token");
    }
    return Promise.reject(error);
  }
);

// --- Auth ---
export const authApi = {
  register: (payload: {
    email: string;
    password: string;
    full_name: string;
    phone?: string;
  }) => api.post("/api/v1/auth/register", payload).then((r) => r.data),
  login: (payload: { email: string; password: string }) =>
    api.post("/api/v1/auth/login", payload).then((r) => r.data),
  me: () => api.get("/api/v1/auth/me", { timeout: 3_000 }).then((r) => r.data),
  updateMe: (payload: Record<string, unknown>) =>
    api.patch("/api/v1/auth/me", payload).then((r) => r.data),
};

// --- Accounts ---
export const accountsApi = {
  list: () => api.get("/api/v1/accounts").then((r) => r.data),
  gmailStart: () => api.get("/api/v1/accounts/gmail/start").then((r) => r.data),
  outlookStart: () => api.get("/api/v1/accounts/outlook/start").then((r) => r.data),
  disconnect: (id: string) => api.delete(`/api/v1/accounts/${id}`),
};

// --- Emails ---
export const emailsApi = {
  list: (params: {
    page?: number;
    size?: number;
    category?: string;
    priority?: string;
    search?: string;
  }) => api.get("/api/v1/emails", { params }).then((r) => r.data),
  createManual: (payload: {
    subject: string;
    sender_email: string;
    sender_name?: string;
    body_text: string;
  }) => api.post("/api/v1/emails/manual", payload).then((r) => r.data),
  get: (id: string) => api.get(`/api/v1/emails/${id}`).then((r) => r.data),
  semantic: (q: string, k = 10) =>
    api
      .get("/api/v1/emails/semantic/search", { params: { q, k } })
      .then((r) => r.data),
};

// --- Notifications / Voice ---
export const notificationsApi = {
  list: () => api.get("/api/v1/notifications").then((r) => r.data),
  voiceNotes: () => api.get("/api/v1/notifications/voice").then((r) => r.data),
  generateLatestVoice: () =>
    api.post("/api/v1/notifications/voice/latest").then((r) => r.data),
  whatsappStatus: () =>
    api.get("/api/v1/notifications/whatsapp/status").then((r) => r.data),
  sendLatestWhatsApp: () =>
    api.post("/api/v1/notifications/whatsapp/latest").then((r) => r.data),
  retry: (emailId: string) =>
    api.post(`/api/v1/notifications/retry/${emailId}`).then((r) => r.data),
};

// --- Fraud ---
export const fraudApi = {
  alerts: () => api.get("/api/v1/fraud/alerts").then((r) => r.data),
  scan: (payload: Record<string, unknown>) =>
    api.post("/api/v1/fraud/scan", payload).then((r) => r.data),
  ack: (id: string) => api.post(`/api/v1/fraud/ack/${id}`).then((r) => r.data),
};

// --- Assistant ---
export const assistantApi = {
  chat: (payload: { query: string; language?: string; voice_reply?: boolean }) =>
    api.post("/api/v1/assistant/chat", payload).then((r) => r.data),
};

// --- Analytics ---
export const analyticsApi = {
  overview: () => api.get("/api/v1/analytics/overview").then((r) => r.data),
};

// --- Briefings ---
export const briefingsApi = {
  list: () => api.get("/api/v1/briefings").then((r) => r.data),
  triggerMorning: () => api.post("/api/v1/briefings/morning").then((r) => r.data),
  triggerEvening: () => api.post("/api/v1/briefings/evening").then((r) => r.data),
};
